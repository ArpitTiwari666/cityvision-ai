"""initial CityVision PostGIS schema"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = "20260909_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table("users", sa.Column("id",sa.Integer,primary_key=True),sa.Column("email",sa.String(255),nullable=False),sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("role",sa.String(32),nullable=False),sa.Column("is_active",sa.Boolean,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()")))
    op.create_index("ix_users_email","users",["email"],unique=True)
    op.create_table("cameras", sa.Column("id",sa.Integer,primary_key=True),sa.Column("code",sa.String(32),nullable=False),sa.Column("name",sa.String(160),nullable=False),sa.Column("camera_type",sa.String(64),nullable=False),sa.Column("status",sa.String(24),nullable=False),sa.Column("stream_url",sa.Text),sa.Column("location",Geometry("POINT",srid=4326),nullable=False),sa.Column("last_heartbeat",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()")))
    op.create_index("ix_cameras_code","cameras",["code"],unique=True); op.create_index("ix_cameras_location","cameras",["location"],postgresql_using="gist")
    op.create_table("vehicles",sa.Column("id",sa.Integer,primary_key=True),sa.Column("plate_normalized",sa.String(24),nullable=False),sa.Column("vehicle_type",sa.String(64)),sa.Column("colour",sa.String(64)),sa.Column("is_blacklisted",sa.Boolean,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()")))
    op.create_index("ix_vehicles_plate","vehicles",["plate_normalized"],unique=True)
    op.create_table("vehicle_detections",sa.Column("id",sa.Integer,primary_key=True),sa.Column("vehicle_id",sa.Integer,sa.ForeignKey("vehicles.id")),sa.Column("camera_id",sa.Integer,sa.ForeignKey("cameras.id"),nullable=False),sa.Column("observed_at",sa.DateTime(timezone=True),nullable=False),sa.Column("track_id",sa.String(64)),sa.Column("vehicle_type",sa.String(64)),sa.Column("detection_confidence",sa.Float),sa.Column("ocr_text",sa.String(24)),sa.Column("ocr_confidence",sa.Float),sa.Column("direction",sa.String(32)),sa.Column("frame_uri",sa.Text),sa.Column("position",Geometry("POINT",srid=4326),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()")))
    op.create_index("ix_detection_position","vehicle_detections",["position"],postgresql_using="gist"); op.create_index("ix_detection_observed","vehicle_detections",["observed_at"])
    op.create_table("traffic_measurements",sa.Column("id",sa.Integer,primary_key=True),sa.Column("camera_id",sa.Integer,sa.ForeignKey("cameras.id")),sa.Column("measured_at",sa.DateTime(timezone=True),nullable=False),sa.Column("vehicle_count",sa.Integer,nullable=False),sa.Column("avg_speed_kph",sa.Float,nullable=False),sa.Column("congestion_index",sa.Float,nullable=False),sa.Column("road_name",sa.String(160)),sa.Column("geometry",Geometry("LINESTRING",srid=4326),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()")))
    op.create_index("ix_traffic_geometry","traffic_measurements",["geometry"],postgresql_using="gist")
    op.create_table("alerts",sa.Column("id",sa.Integer,primary_key=True),sa.Column("code",sa.String(32),nullable=False),sa.Column("severity",sa.String(16),nullable=False),sa.Column("title",sa.String(255),nullable=False),sa.Column("status",sa.String(32),nullable=False),sa.Column("vehicle_id",sa.Integer,sa.ForeignKey("vehicles.id")),sa.Column("camera_id",sa.Integer,sa.ForeignKey("cameras.id")),sa.Column("occurred_at",sa.DateTime(timezone=True),nullable=False),sa.Column("payload",sa.JSON,nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("now()")))
    op.create_index("ix_alerts_code","alerts",["code"],unique=True); op.create_index("ix_alerts_occurred","alerts",["occurred_at"])

def downgrade():
    for table in ["alerts","traffic_measurements","vehicle_detections","vehicles","cameras","users"]: op.drop_table(table)
