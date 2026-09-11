from datetime import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Timestamped(Base):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class User(Timestamped):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Camera(Timestamped):
    __tablename__ = "cameras"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    camera_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="offline")
    stream_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Vehicle(Timestamped):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True)
    plate_normalized: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    colour: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False)

class Detection(Timestamped):
    __tablename__ = "vehicle_detections"
    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), index=True, nullable=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    track_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detection_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(String(24), index=True, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction: Mapped[str | None] = mapped_column(String(32), nullable=True)
    frame_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[object] = mapped_column(Geometry("POINT", srid=4326), nullable=False)
Index("ix_detection_position", Detection.position, postgresql_using="gist")

class TrafficMeasurement(Timestamped):
    __tablename__ = "traffic_measurements"
    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int | None] = mapped_column(ForeignKey("cameras.id"), index=True, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    vehicle_count: Mapped[int] = mapped_column(Integer)
    avg_speed_kph: Mapped[float] = mapped_column(Float)
    congestion_index: Mapped[float] = mapped_column(Float)
    road_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    geometry: Mapped[object] = mapped_column(Geometry("LINESTRING", srid=4326), nullable=False)
Index("ix_traffic_geometry", TrafficMeasurement.geometry, postgresql_using="gist")

class Alert(Timestamped):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="Open")
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    camera_id: Mapped[int | None] = mapped_column(ForeignKey("cameras.id"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
