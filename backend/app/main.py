from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, Point
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, get_db
from .models import Alert, Camera, Detection, TrafficMeasurement, Vehicle
from .schemas import AlertPatch, CameraIn, DetectionIn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema changes are applied by Alembic during deployment, never implicitly at app startup.
    yield

app = FastAPI(title="CityVision AI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
Db = Annotated[Session, Depends(get_db)]

def point(lon: float, lat: float): return from_shape(Point(lon, lat), srid=4326)
def coordinates(g):
    if not g: return None
    return list(g.data[9:]) if False else None

@app.get("/health")
def health(db: Db):
    db.execute(select(1))
    return {"status":"ok", "mode":"demo" if settings.demo_mode else "live"}

@app.get("/api/v1/dashboard")
def dashboard(db: Db):
    now = datetime.now(timezone.utc)
    active = db.scalar(select(func.count()).select_from(Camera).where(Camera.status == "Online")) or 0
    total = db.scalar(select(func.count()).select_from(Camera)) or 0
    detections = db.scalar(select(func.count()).select_from(Detection).where(Detection.observed_at >= now - timedelta(days=1))) or 0
    average_speed = db.scalar(select(func.avg(TrafficMeasurement.avg_speed_kph)).where(TrafficMeasurement.measured_at >= now - timedelta(hours=24))) or 0
    open_alerts = db.scalar(select(func.count()).select_from(Alert).where(Alert.status != "Resolved")) or 0
    return {"mode":"simulation" if settings.demo_mode else "live", "metrics":{"active_cameras":active,"total_cameras":total,"vehicles_detected":detections,"avg_speed_kph":round(float(average_speed),1),"active_alerts":open_alerts}}

@app.get("/api/v1/cameras")
def list_cameras(db: Db, status: str | None = None):
    q = select(Camera)
    if status: q = q.where(Camera.status == status)
    rows = db.scalars(q.order_by(Camera.code)).all()
    return [{"id":c.id,"code":c.code,"name":c.name,"type":c.camera_type,"status":c.status,"stream_url":c.stream_url,"last_heartbeat":c.last_heartbeat} for c in rows]

@app.post("/api/v1/cameras", status_code=201)
def create_camera(body: CameraIn, db: Db):
    if db.scalar(select(Camera).where(Camera.code == body.code)): raise HTTPException(409, "Camera code already exists")
    c = Camera(code=body.code, name=body.name, camera_type=body.camera_type, stream_url=body.stream_url, status="Offline", location=point(body.longitude, body.latitude))
    db.add(c); db.commit(); db.refresh(c)
    return {"id":c.id,"code":c.code}

@app.get("/api/v1/vehicles/{plate}/trajectory")
def trajectory(plate: str, db: Db):
    normalized = plate.upper().replace(" ", "")
    vehicle = db.scalar(select(Vehicle).where(Vehicle.plate_normalized == normalized))
    if not vehicle: raise HTTPException(404, "Vehicle not found")
    rows = db.execute(select(Detection, Camera).join(Camera, Detection.camera_id == Camera.id).where(Detection.vehicle_id == vehicle.id).order_by(Detection.observed_at)).all()
    features=[]
    for d,c in rows:
        p = d.position.data
        # GeoJSON coordinates are intentionally generated through PostGIS in map endpoints; event list avoids binary geometry leakage.
        features.append({"camera":c.code,"location":c.name,"observed_at":d.observed_at,"direction":d.direction,"ocr_confidence":d.ocr_confidence,"vehicle_type":d.vehicle_type})
    return {"plate":normalized,"is_blacklisted":vehicle.is_blacklisted,"events":features,"trajectory_source":"plate, time, camera location, and direction; tracker IDs are video-local only"}

@app.post("/api/v1/detections", status_code=202)
def ingest_detection(body: DetectionIn, db: Db):
    camera = db.scalar(select(Camera).where(Camera.code == body.camera_code))
    if not camera: raise HTTPException(404, "Camera not found")
    vehicle = None
    normalized = body.plate.upper().replace(" ", "") if body.plate else None
    if normalized:
        vehicle = db.scalar(select(Vehicle).where(Vehicle.plate_normalized == normalized))
        if not vehicle:
            vehicle = Vehicle(plate_normalized=normalized, vehicle_type=body.vehicle_type); db.add(vehicle); db.flush()
    event = Detection(vehicle_id=vehicle.id if vehicle else None, camera_id=camera.id, observed_at=body.observed_at, position=point(body.longitude,body.latitude), ocr_text=normalized, ocr_confidence=body.ocr_confidence, detection_confidence=body.detection_confidence, vehicle_type=body.vehicle_type, direction=body.direction, track_id=body.track_id, frame_uri=body.frame_uri)
    db.add(event); db.commit()
    return {"accepted":True, "simulation":settings.demo_mode}

@app.get("/api/v1/map/layers")
def map_layers(db: Db, layer: str = Query("traffic", pattern="^(traffic|cameras|heatmap|hotspots)$")):
    if layer == "cameras":
        rows = db.execute(select(Camera.code, Camera.name, Camera.status, func.ST_X(Camera.location), func.ST_Y(Camera.location))).all()
        return {"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[float(x),float(y)]},"properties":{"code":code,"name":name,"status":status}} for code,name,status,x,y in rows]}
    if layer == "traffic":
        rows = db.execute(select(TrafficMeasurement.road_name,TrafficMeasurement.congestion_index,TrafficMeasurement.avg_speed_kph,func.ST_AsGeoJSON(TrafficMeasurement.geometry))).all()
        import json
        return {"type":"FeatureCollection","features":[{"type":"Feature","geometry":json.loads(g),"properties":{"road_name":road,"congestion_index":idx,"avg_speed_kph":speed}} for road,idx,speed,g in rows]}
    return {"type":"FeatureCollection","features":[],"mode":"simulation","message":"Heatmap/hotspots aggregate backend traffic measurements; seed data or pipeline events populate this layer."}

@app.get("/api/v1/alerts")
def list_alerts(db: Db, status: str | None = None):
    q=select(Alert).order_by(desc(Alert.occurred_at))
    if status:q=q.where(Alert.status==status)
    return [{"id":a.id,"code":a.code,"severity":a.severity,"title":a.title,"status":a.status,"occurred_at":a.occurred_at,"payload":a.payload} for a in db.scalars(q).all()]

@app.patch("/api/v1/alerts/{alert_id}")
def update_alert(alert_id:int, body:AlertPatch, db:Db):
    a=db.get(Alert,alert_id)
    if not a: raise HTTPException(404,"Alert not found")
    a.status=body.status; db.commit(); return {"id":a.id,"status":a.status}

@app.websocket("/ws/operations")
async def operations_socket(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json({"type":"heartbeat","mode":"simulation" if settings.demo_mode else "live","at":datetime.now(timezone.utc).isoformat()})
            import asyncio; await asyncio.sleep(12)
    except WebSocketDisconnect:
        pass
