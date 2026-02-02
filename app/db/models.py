from sqlalchemy import Column, Integer, String, DateTime, func
from .base import Base

class VideoRecord(Base):
    __tablename__ = "video_recordings"

    record_id = Column(Integer, primary_key=True, index=True)
    
    stream_id = Column(String, nullable=False, index=True)
    # Allows tracking which drone this recording belongs to, 
    # derived from stream_id -> drone_id map at the time of recording
    drone_id = Column(String, nullable=False, index=True) 
    
    file_path = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
