import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.db.models import VideoRecord
from app.schemas.stream_schema import (
    DroneRegisterRequest, DroneRegisterResponse, StreamInfo, VideoRecordResponse
)
from app.services.drone_service import drone_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/stream/register", response_model=DroneRegisterResponse)
async def register_drone(item: DroneRegisterRequest):
    drone_service.register_drone(item.drone_id, item.stream_id)
    logger.info("Drone registered", extra={"drone_id": item.drone_id, "stream_id": item.stream_id})
    return DroneRegisterResponse(success=True, message="Registered successfully")

# NOTE: The `/api/stream/play-url` endpoint is intentionally disabled for now.
# Clients can use the `play_url` field returned by `GET /api/streams/online`.
#
# @router.get("/stream/play-url")
# async def get_play_url(id: str, type: str = "live"):
#     # TODO: 根据不同的协议类型返回不同的URL
#     # id is stream_id
#     url = drone_service.get_play_url(id)
#     if not url:
#         raise HTTPException(status_code=404, detail="Stream offline or not found")
#     logger.debug("Play URL requested", extra={"stream_id": id, "type": type})
#     return {"url": url}

@router.get("/streams/online", response_model=List[StreamInfo])
async def get_online_streams():
    streams = drone_service.get_online_streams()
    logger.debug("Online streams fetched", extra={"count": len(streams)})
    # Convert internal DroneSession to Schema StreamInfo
    return [
        StreamInfo(
            stream_id=s.stream_id,
            drone_id=s.drone_id,
            status=s.status,
            app=s.app,
            play_url=drone_service.get_play_url(s.stream_id)
        )
        for s in streams
    ]

@router.get("/recordings", response_model=List[VideoRecordResponse])
async def get_recordings(
    drone_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(VideoRecord)
    if drone_id:
        query = query.filter(VideoRecord.drone_id == drone_id)
    
    # Order by time desc
    records = query.order_by(VideoRecord.record_id.desc()).all()
    logger.debug("Recordings fetched", extra={"count": len(records), "drone_id": drone_id})
    return records
