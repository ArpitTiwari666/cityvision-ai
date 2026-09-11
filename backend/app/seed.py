"""Seed clearly-labelled Indore simulation data for a no-CCTV demo."""
from datetime import datetime, timezone
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, Point
from .db import Base, SessionLocal, engine
from .models import Alert, Camera, TrafficMeasurement, Vehicle

CAMERAS = [("CAM-014","Vijay Nagar Junction","ANPR PTZ",75.894,22.753),("CAM-027","Palasia Square","Fixed ANPR",75.890,22.727),("CAM-063","MR-10 Corridor","Traffic Cam",75.862,22.742),("CAM-093","Rau Bypass","Fixed ANPR",75.809,22.676)]

def seed():
    Base.metadata.create_all(engine); db=SessionLocal()
    try:
        if db.query(Camera).count(): return
        cameras=[]
        for code,name,kind,lon,lat in CAMERAS:
            camera=Camera(code=code,name=name,camera_type=kind,status="Online",location=from_shape(Point(lon,lat),srid=4326));db.add(camera);cameras.append(camera)
        db.flush(); now=datetime.now(timezone.utc)
        db.add(TrafficMeasurement(camera_id=cameras[0].id,measured_at=now,vehicle_count=84,avg_speed_kph=27,congestion_index=84,road_name="MR-10 Corridor",geometry=from_shape(LineString([(75.85,22.74),(75.88,22.75)]),srid=4326)))
        vehicle=Vehicle(plate_normalized="MP09AB1234",vehicle_type="Sedan",is_blacklisted=True);db.add(vehicle);db.flush()
        db.add(Alert(code="AL-3091",severity="Critical",title="Blacklisted vehicle detected",status="Open",vehicle_id=vehicle.id,camera_id=cameras[0].id,occurred_at=now,payload={"mode":"simulation","reason":"seeded demonstration event"}))
        db.commit()
    finally: db.close()

if __name__ == "__main__": seed()
