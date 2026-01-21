from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DroneRegisterRequest(BaseModel):
    drone_id: str
    stream_id: str

class DroneRegisterResponse(BaseModel):
    success: bool
    message: str

class StreamInfo(BaseModel):
    stream_id: str
    drone_id: str
    status: str
    app: str
    play_url: Optional[str] = None
    # Details
    resolution: Optional[str] = None
    fps: Optional[float] = None

class VideoRecordResponse(BaseModel):
    record_id: int
    drone_id: str
    stream_id: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True
