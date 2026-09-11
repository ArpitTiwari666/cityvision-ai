from datetime import datetime
from pydantic import BaseModel, Field

class CameraIn(BaseModel):
    code: str = Field(pattern=r"^CAM-\\d{3,}$")
    name: str
    camera_type: str
    longitude: float
    latitude: float
    stream_url: str | None = None

class CameraOut(CameraIn):
    id: int
    status: str
    class Config: from_attributes = True

class DetectionIn(BaseModel):
    camera_code: str
    observed_at: datetime
    longitude: float
    latitude: float
    plate: str | None = None
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)
    detection_confidence: float | None = Field(default=None, ge=0, le=1)
    vehicle_type: str | None = None
    direction: str | None = None
    track_id: str | None = None
    frame_uri: str | None = None

class AlertPatch(BaseModel):
    status: str = Field(pattern="^(Open|Investigating|Resolved)$")
