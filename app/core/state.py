from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime

class DroneSession(BaseModel):
    stream_id: str
    drone_id: str
    status: str = "Offline"  # Online, Offline
    app: str = "live"
    vhost: str = "__defaultVhost__"
    params: str = ""
    start_time: Optional[datetime] = None
    client_ip: Optional[str] = None
    
    # Metadata
    video_code: Optional[str] = None
    video_height: int = 0
    video_width: int = 0
    fps: float = 0.0

# Global In-Memory State
# Key: stream_id, Value: DroneSession
DRONE_SESSIONS: Dict[str, DroneSession] = {}

# Map drone_id to stream_id for reverse lookup if needed
# Key: drone_id, Value: stream_id
DRONE_ID_MAP: Dict[str, str] = {}
