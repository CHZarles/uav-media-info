from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.hook_schema import HookResponse, OnPublishItem, OnStreamChangedItem, OnRecordMp4Item
from app.services.drone_service import drone_service
from app.db.base import get_db

router = APIRouter()

@router.post("/on_publish", response_model=HookResponse)
async def on_publish(item: OnPublishItem):
    """
    ZLM callback when a stream goes online.
    Return {code: 0, msg: "success"} to allow publishing.
    """
    allowed = drone_service.handle_publish(item)
    if allowed:
        return HookResponse(code=0, msg="success")
    else:
        return HookResponse(code=-1, msg="auth failed")

@router.post("/on_stream_changed", response_model=HookResponse)
async def on_stream_changed(item: OnStreamChangedItem):
    """
    ZLM callback when stream connects/disconnects.
    """
    drone_service.handle_stream_changed(item)
    return HookResponse(code=0, msg="success")

@router.post("/on_record_mp4", response_model=HookResponse)
async def on_record_mp4(item: OnRecordMp4Item, db: Session = Depends(get_db)):
    """
    ZLM callback when MP4 recording is finished.
    """
    drone_service.handle_record_mp4(db, item)
    return HookResponse(code=0, msg="success")
