"""Explicit prototype pipeline boundary. Accuracy depends on local validation data."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

@dataclass
class InferenceEvent:
    camera_code: str; observed_at: datetime; longitude: float; latitude: float
    plate: str | None = None; ocr_confidence: float | None = None
    detection_confidence: float | None = None; vehicle_type: str | None = None
    direction: str | None = None; track_id: str | None = None

class Detector(Protocol):
    def infer(self, frame) -> list[dict]: ...

def process_frame(frame, camera_code: str, longitude: float, latitude: float, detector: Detector) -> list[InferenceEvent]:
    """Adapter point for Ultralytics YOLO, PaddleOCR and ByteTrack/DeepSORT.
    A track_id is intentionally scoped to one video stream. Cross-camera association is built from
    verified plate observations plus time, direction, road distance and optional appearance features.
    """
    now = datetime.now(timezone.utc)
    return [InferenceEvent(camera_code=camera_code, observed_at=now, longitude=longitude, latitude=latitude, **item) for item in detector.infer(frame)]
