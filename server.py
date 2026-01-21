import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 设置日志格式，方便在控制台看到 Hook 事件
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [BACKEND] - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple Backend for ZLM")

# ================= 内存数据库 =================
# 结构: stream_id -> { drone_id, status, records: [], ... }
app.state.sessions: Dict[str, Dict[str, Any]] = {}

# ================= 请求模型 =================

class RegisterPayload(BaseModel):
    drone_id: str
    stream_id: str
    name: str | None = None
    model: str | None = None
    class Config:
        extra = "allow"

class HookPublish(BaseModel):
    app: str
    stream: str
    ip: str | None = None
    params: str | None = None
    schema_: str = Field(None, alias="schema") # schema 是 python 关键字，用 alias 处理
    class Config:
        extra = "allow"

class HookStreamChanged(BaseModel):
    app: str
    stream: str
    regist: bool # True=注册(很少用到), False=注销(断流)
    class Config:
        extra = "allow"

class HookRecord(BaseModel):
    stream: str
    file_path: str
    time_len: float
    url: str | None = None
    class Config:
        extra = "allow"

# ================= 业务接口 =================

@app.post("/api/stream/register")
async def register(payload: RegisterPayload):
    """设备注册接口"""
    data = payload.dict()
    
    # 初始化状态
    data["status"] = "Offline"
    data["records"] = []
    
    # 存入内存
    app.state.sessions[data["stream_id"]] = data
    logger.info(f"✅ 设备已注册: {data['drone_id']} (Stream: {data['stream_id']})")
    
    return {"code": 0, "msg": "registered", "data": data}


@app.get("/api/streams/online")
async def streams_online():
    """获取所有设备列表(含状态)"""
    return {"code": 0, "data": list(app.state.sessions.values())}


@app.get("/api/recordings")
async def get_recordings():
    """获取所有录像记录 (扁平化展示)"""
    all_records = []
    for sid, session in app.state.sessions.items():
        for rec in session.get("records", []):
            rec["drone_name"] = session.get("name")
            all_records.append(rec)
    return {"code": 0, "data": all_records}

# ================= ZLMediaKit WebHooks =================

@app.post("/hook/on_publish")
async def on_publish(payload: HookPublish):
    """
    流上线回调
    ZLM 询问是否允许推流，返回 code:0 表示允许
    """
    stream_id = payload.stream
    logger.info(f"📡 [Hook] 收到推流请求: stream_id={stream_id}")

    # 1. 校验设备是否注册 (V0版本如果不注册也可以允许，但这里做个简单的校验)
    if stream_id not in app.state.sessions:
        logger.warning(f"❌ 未知设备尝试推流: {stream_id}")
        # 如果你想拒绝未知设备，返回 code: -1
        # return {"code": -1, "msg": "Device not registered"}
        
        # 为了演示方便，这里自动创建一个临时Session
        app.state.sessions[stream_id] = {"drone_id": "unknown", "stream_id": stream_id, "status": "Offline", "records": []}

    # 2. 更新状态为 Online
    app.state.sessions[stream_id]["status"] = "Online"
    logger.info(f"🟢 设备状态更新为: Online")

    return {"code": 0, "msg": "success"}


@app.post("/hook/on_stream_changed")
async def on_stream_changed(payload: HookStreamChanged):
    """
    流注册/注销回调
    主要用于捕获断流事件 (regist=False)
    """
    stream_id = payload.stream
    
    if not payload.regist:
        # 断流事件
        logger.info(f"🔌 [Hook] 流断开: stream_id={stream_id}")
        if stream_id in app.state.sessions:
            app.state.sessions[stream_id]["status"] = "Offline"
            logger.info(f"🔴 设备状态更新为: Offline")
    
    return {"code": 0, "msg": "success"}


@app.post("/hook/on_record_mp4")
async def on_record_mp4(payload: HookRecord):
    """
    录制完成回调
    收到此 Hook 说明 MP4 文件已生成
    """
    stream_id = payload.stream
    logger.info(f"💾 [Hook] 录像完成: stream_id={stream_id} | 时长: {payload.time_len}s")
    logger.info(f"   -> 路径: {payload.file_path}")

    # 保存录像记录到内存
    if stream_id in app.state.sessions:
        record_entry = {
            "path": payload.file_path,
            "duration": payload.time_len,
            "url": payload.url
        }
        app.state.sessions[stream_id]["records"].append(record_entry)

    return {"code": 0, "msg": "success"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# 启动说明
if __name__ == "__main__":
    import uvicorn
    print("Backend Server running on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)