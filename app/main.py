from fastapi import FastAPI
import uvicorn

from app.api.v1 import hooks, streams
from app.db.base import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Drone Stream Server")

# Include Routers
app.include_router(hooks.router, prefix="/hook", tags=["WebHooks"])
app.include_router(streams.router, prefix="/api", tags=["Business API"])

@app.get("/")
def read_root():
    return {"message": "Drone Stream Server is running"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
