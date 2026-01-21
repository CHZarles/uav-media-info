import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core import state
from app.core.config import settings
from app.db.models import VideoRecord
from app.schemas.hook_schema import OnPublishItem, OnStreamChangedItem, OnRecordMp4Item


logger = logging.getLogger(__name__)

class DroneService:
    def register_drone(self, drone_id: str, stream_id: str):
        """
        Register a drone mapping in memory
        """
        # Create session if not exists or update
        session = state.DroneSession(
            stream_id=stream_id,
            drone_id=drone_id,
            status="Offline"
        )
        state.DRONE_SESSIONS[stream_id] = session
        state.DRONE_ID_MAP[drone_id] = stream_id
        logger.info("Registered drone", extra={"drone_id": drone_id, "stream_id": stream_id})

    def handle_publish(self, data: OnPublishItem) -> bool:
        """
        Handle stream online event
        """
        stream_id = data.stream
        # Check if we know this stream
        if stream_id in state.DRONE_SESSIONS:
            session = state.DRONE_SESSIONS[stream_id]
            session.status = "Online"
            session.app = data.app
            session.vhost = data.vhost
            session.params = data.params
            session.client_ip = data.ip
            logger.info(
                "Stream online",
                extra={"stream_id": stream_id, "app": data.app, "vhost": data.vhost},
            )
            return True
        else:
            # Optionally auto-register/allow unknown streams or reject
            logger.warning("Unknown stream publishing", extra={"stream_id": stream_id})
            # We can allow it but treat as anonymous or reject. 
            # Returning True allows the stream.
            return True

    def handle_stream_changed(self, data: OnStreamChangedItem):
        """
        Handle stream connect/disconnect
        """
        stream_id = data.stream
        if not data.regist:
            # Stream disconnected
            if stream_id in state.DRONE_SESSIONS:
                state.DRONE_SESSIONS[stream_id].status = "Offline"
                logger.info("Stream offline", extra={"stream_id": stream_id})

    def handle_record_mp4(self, db: Session, data: OnRecordMp4Item):
        """
        Save recording record to DB
        """
        stream_id = data.stream
        drone_id = "unknown"
        
        # Try to find drone_id from memory (if session still exists)
        if stream_id in state.DRONE_SESSIONS:
            drone_id = state.DRONE_SESSIONS[stream_id].drone_id
        
        # Create record
        record = VideoRecord(
            stream_id=stream_id,
            drone_id=drone_id,
            file_path=data.file_path
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            "Recording saved",
            extra={"stream_id": stream_id, "file_path": data.file_path, "record_id": record.record_id},
        )

    def get_online_streams(self) -> List[state.DroneSession]:
        return [
            s for s in state.DRONE_SESSIONS.values() 
            if s.status == "Online"
        ]
    
    def get_play_url(self, stream_id: str, flv: bool = True) -> Optional[str]:
        # Simple URL construction based on ZLM rules
        # http://<host>:<port>/<app>/<stream>.flv
        # This is a bit simplistic, might need real ZLM logic
        if stream_id not in state.DRONE_SESSIONS:
            return None
        
        session = state.DRONE_SESSIONS[stream_id]
        if session.status != "Online":
             return None
             
        # Construct URL
        # Assumption: ZLM HTTP port is 80 or part of ZLM_HOST
        base = settings.ZLM_HOST
        ext = ".flv" if flv else ".m3u8"
        return f"{base}/{session.app}/{stream_id}{ext}"

drone_service = DroneService()
