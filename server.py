from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class RegisterPayload(BaseModel):
    drone_id: str
    stream_id: str
    name: str | None = None
    model: str | None = None

    class Config:
        extra = "allow"


# simple in-memory store: stream_id -> info
app.state.sessions: Dict[str, Dict[str, Any]] = {}


@app.post("/api/stream/register")
async def register(payload: RegisterPayload):
    data = payload.dict()
    # store mapping
    app.state.sessions[data["stream_id"]] = data
    return {"code": 0, "msg": "registered", "data": data}


@app.get("/api/streams/online")
async def streams_online():
    # return list of registered streams
    return {"code": 0, "data": list(app.state.sessions.values())}


@app.get("/health")
async def health():
    return {"status": "ok"}
