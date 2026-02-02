from fastapi.testclient import TestClient

from app.db.base import SessionLocal
from app.db.models import VideoRecord
from app.main import app


client = TestClient(app)


def _clear_records() -> None:
    db = SessionLocal()
    try:
        db.query(VideoRecord).delete()
        db.commit()
    finally:
        db.close()


def _record_payload(stream_id: str) -> dict:
    return {
        "mediaServerId": "test_zlm",
        "app": "live",
        "stream": stream_id,
        "file_path": f"/data/media/live/{stream_id}/2026-02-02/{stream_id}.mp4",
        "file_size": 1234,
        "folder": f"/data/media/live/{stream_id}/",
        "start_time": 0,
        "time_len": 1.0,
        "url": f"http://localhost:9000/record/live/{stream_id}/{stream_id}.mp4",
        "vhost": "__defaultVhost__",
    }


def test_record_hook_ignored_for_unregistered_stream() -> None:
    _clear_records()

    r = client.post("/hook/on_record_mp4", json=_record_payload("unregistered_stream"))
    assert r.status_code == 200

    recordings = client.get("/api/recordings").json()
    assert recordings == []


def test_record_hook_saved_for_registered_stream() -> None:
    _clear_records()

    stream_id = "stream_001"
    drone_id = "drone_001"
    r = client.post("/api/stream/register", json={"drone_id": drone_id, "stream_id": stream_id})
    assert r.status_code == 200

    r = client.post("/hook/on_record_mp4", json=_record_payload(stream_id))
    assert r.status_code == 200

    recordings = client.get("/api/recordings").json()
    assert len(recordings) == 1
    assert recordings[0]["stream_id"] == stream_id
    assert recordings[0]["drone_id"] == drone_id
