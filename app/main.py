import logging
import logging.handlers
import os
from datetime import datetime
from fastapi import FastAPI
import uvicorn

from app.api.v1 import hooks, streams
from app.core.config import settings
from app.db.base import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Drone Stream Server")

# Configure root logger with level from settings
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
handlers = [logging.StreamHandler()]

if settings.LOG_FILE:
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Pre-rotate if the existing file is too large
    try:
        if os.path.exists(settings.LOG_FILE):
            size = os.path.getsize(settings.LOG_FILE)
            if size >= settings.LOG_FILE_MAX_BYTES:
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                rotated = f"{settings.LOG_FILE}.{ts}"
                os.rename(settings.LOG_FILE, rotated)
    except OSError:
        pass

    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=5,
        encoding="utf-8",
    )
    handlers.append(file_handler)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
for h in handlers:
    h.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.handlers = []
root_logger.setLevel(log_level)
for h in handlers:
    root_logger.addHandler(h)

# Include Routers
app.include_router(hooks.router, prefix="/hook", tags=["WebHooks"])
app.include_router(streams.router, prefix="/api", tags=["Business API"])

@app.get("/")
def read_root():
    return {"message": "Drone Stream Server is running"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
