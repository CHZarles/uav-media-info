def _publish_payload(stream_id: str) -> dict:
    return {
        "mediaServerId": "test_zlm",
        "app": "live",
        "stream": stream_id,
        "params": "",
        "ip": "192.168.1.100",
        "port": 1935,
        "vhost": "__defaultVhost__",
        # Extra fields from ZLM are tolerated by our schema.
        "schema": "rtmp",
        "originType": 1,
        "originTypeStr": "rtmp_push",
    }


def _stream_changed_payload(stream_id: str, regist: bool) -> dict:
    return {
        "mediaServerId": "test_zlm",
        "app": "live",
        "stream": stream_id,
        "regist": regist,
        "schema": "rtmp",
        "vhost": "__defaultVhost__",
    }


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


def test_register_then_online_list_empty_until_published(client) -> None:
    stream_id = "stream_001"
    drone_id = "drone_001"

    r = client.post("/api/stream/register", json={"drone_id": drone_id, "stream_id": stream_id})
    assert r.status_code == 200

    streams = client.get("/api/streams/online").json()
    assert streams == []


def test_publish_makes_stream_online_and_playable(client) -> None:
    stream_id = "stream_001"
    drone_id = "drone_001"

    r = client.post("/api/stream/register", json={"drone_id": drone_id, "stream_id": stream_id})
    assert r.status_code == 200

    r = client.post("/hook/on_publish", json=_publish_payload(stream_id))
    assert r.status_code == 200
    assert r.json()["code"] == 0

    streams = client.get("/api/streams/online").json()
    assert len(streams) == 1
    assert streams[0]["stream_id"] == stream_id
    assert streams[0]["drone_id"] == drone_id
    assert streams[0]["status"] == "Online"
    assert streams[0]["app"] == "live"
    assert streams[0]["play_url"] == f"http://localhost:9000/live/{stream_id}.flv"


def test_stream_changed_offline_removes_from_online_list(client) -> None:
    stream_id = "stream_001"
    drone_id = "drone_001"

    client.post("/api/stream/register", json={"drone_id": drone_id, "stream_id": stream_id})
    client.post("/hook/on_publish", json=_publish_payload(stream_id))

    r = client.post("/hook/on_stream_changed", json=_stream_changed_payload(stream_id, regist=False))
    assert r.status_code == 200
    assert r.json()["code"] == 0

    streams = client.get("/api/streams/online").json()
    assert streams == []


def test_publish_unknown_stream_allowed_but_not_listed(client) -> None:
    r = client.post("/hook/on_publish", json=_publish_payload("unknown_stream"))
    assert r.status_code == 200
    assert r.json()["code"] == 0

    streams = client.get("/api/streams/online").json()
    assert streams == []


def test_play_url_endpoint_disabled(client) -> None:
    r = client.get("/api/stream/play-url", params={"id": "stream_001"})
    assert r.status_code == 404
    assert r.json()["detail"] == "Not Found"


def test_record_saved_even_if_stream_is_offline_after_disconnect(client) -> None:
    stream_id = "stream_001"
    drone_id = "drone_001"

    client.post("/api/stream/register", json={"drone_id": drone_id, "stream_id": stream_id})
    client.post("/hook/on_publish", json=_publish_payload(stream_id))
    client.post("/hook/on_stream_changed", json=_stream_changed_payload(stream_id, regist=False))

    r = client.post("/hook/on_record_mp4", json=_record_payload(stream_id))
    assert r.status_code == 200

    recordings = client.get("/api/recordings").json()
    assert len(recordings) == 1
    assert recordings[0]["drone_id"] == drone_id
    assert recordings[0]["stream_id"] == stream_id


def test_recordings_filter_by_drone_id(client) -> None:
    drone_a = {"drone_id": "drone_a", "stream_id": "stream_a"}
    drone_b = {"drone_id": "drone_b", "stream_id": "stream_b"}

    client.post("/api/stream/register", json=drone_a)
    client.post("/api/stream/register", json=drone_b)

    client.post("/hook/on_record_mp4", json=_record_payload(drone_a["stream_id"]))
    client.post("/hook/on_record_mp4", json=_record_payload(drone_b["stream_id"]))

    rec_a = client.get("/api/recordings", params={"drone_id": drone_a["drone_id"]}).json()
    assert len(rec_a) == 1
    assert rec_a[0]["drone_id"] == drone_a["drone_id"]

    rec_b = client.get("/api/recordings", params={"drone_id": drone_b["drone_id"]}).json()
    assert len(rec_b) == 1
    assert rec_b[0]["drone_id"] == drone_b["drone_id"]
