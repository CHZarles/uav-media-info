import time
import uuid
import random
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import requests

# ================= 配置区域 =================
# 你的后端服务地址 (接收 WebHook 的地址)
BACKEND_HOOK_URL = "http://localhost:8000"  # 假设你的业务后端运行在 8000
# ZLM 的一些固定配置模拟
ZLM_SECRET = "035c73f7-bb6b-4889-a715-d9eb2d1925cc"
MEDIA_SERVER_ID = "mock_zlm_server_01"
HTTP_PORT = 46545 # 本 Mock 服务运行端口

app = FastAPI(title="Mock ZLMediaKit Service")

# ================= 内存状态 =================
# 用于存储正在推流的模拟设备，key=stream_id
# 结构: {"stream_id": {"start_time": timestamp, "app": "live"}}
active_streams: Dict[str, dict] = {}

# ================= 请求模型 =================
class StreamControl(BaseModel):
    stream_id: str
    app: str = "live"

# ================= 辅助函数：发送 WebHook =================
def send_webhook(path: str, payload: dict):
    url = f"{BACKEND_HOOK_URL}{path}"
    try:
        print(f"[Mock ZLM] -> 发送 WebHook 到: {path} | Data: {payload}")
        resp = requests.post(url, json=payload, timeout=2)
        print(f"[Mock ZLM] <- 收到响应: {resp.status_code} - {resp.text}")
        return resp.status_code
    except Exception as e:
        print(f"[Mock ZLM] !! 发送失败: {str(e)}")

# ================= 控制接口 (供开发者调用) =================

@app.post("/control/start_stream")
async def mock_start_stream(data: StreamControl):
    """
    【控制指令】模拟无人机开始推流
    触发: hook/on_publish
    """
    if data.stream_id in active_streams:
        return {"msg": "流已经在推流中了", "stream_id": data.stream_id}

    # 1. 更新内部状态
    active_streams[data.stream_id] = {
        "start_time": time.time(),
        "app": data.app,
        "vhost": "__defaultVhost__"
    }

    # 2. 构造 ZLM on_publish 包体
    payload = {
        "mediaServerId": MEDIA_SERVER_ID,
        "app": data.app,
        "stream": data.stream_id,
        "ip": "192.168.1.100",
        "params": "",
        "port": 1935,
        "schema": "rtmp",
        "vhost": "__defaultVhost__",
        "originType": 1, # rtmp 推流
        "originTypeStr": "rtmp_push"
    }

    # 3. 发送 WebHook
    send_webhook("/hook/on_publish", payload)
    
    return {"msg": "模拟推流成功", "status": "Online", "stream_id": data.stream_id}


@app.post("/control/stop_stream")
async def mock_stop_stream(data: StreamControl, background_tasks: BackgroundTasks):
    """
    【控制指令】模拟无人机断开推流
    触发: 
    1. hook/on_stream_changed (regist=false)
    2. hook/on_record_mp4 (模拟生成了录像文件)
    """
    if data.stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="该流未在线")

    stream_info = active_streams.pop(data.stream_id)
    duration = int(time.time() - stream_info['start_time'])
    if duration <= 0: duration = 1

    # --- 动作 1: 发送流注销事件 ---
    def send_hooks():
        # 1. on_stream_changed (下线)
        offline_payload = {
            "mediaServerId": MEDIA_SERVER_ID,
            "app": data.app,
            "stream": data.stream_id,
            "regist": False,  # 关键：False 代表下线
            "schema": "rtmp",
            "vhost": "__defaultVhost__"
        }
        send_webhook("/hook/on_stream_changed", offline_payload)
        
        # 模拟文件写入耗时
        time.sleep(0.5)

        # 2. on_record_mp4 (录制完成)
        # 模拟生成一个文件路径
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_name = f"{data.stream_id}_{int(time.time())}.mp4"
        file_path = f"/data/media/{data.app}/{data.stream_id}/{date_str}/{file_name}"
        
        record_payload = {
            "mediaServerId": MEDIA_SERVER_ID,
            "app": data.app,
            "stream": data.stream_id,
            "file_path": file_path,
            "file_size": 1024 * 1024 * random.randint(5, 50), # 随机大小 5MB-50MB
            "folder": f"/data/media/{data.app}/{data.stream_id}/",
            "start_time": int(stream_info['start_time']),
            "time_len": duration, # 实际持续时长
            "url": f"http://localhost:{HTTP_PORT}/record/{data.app}/{data.stream_id}/{file_name}",
            "vhost": "__defaultVhost__"
        }
        send_webhook("/hook/on_record_mp4", record_payload)

    # 异步执行发送，快速响应控制接口
    background_tasks.add_task(send_hooks)

    return {"msg": "模拟断流指令已接收", "simulated_duration": duration}


# ================= ZLM 业务 API 模拟 (被动调用) =================

@app.get("/index/api/getMediaList")
async def mock_get_media_list(secret: str = ""):
    """
    模拟 ZLM 获取流列表接口
    供后端兜底查询使用
    """
    # 模拟简单的 secret 校验（可选）
    # if secret != ZLM_SECRET: return {"code": -1, "msg": "auth fail"}

    data = []
    for stream_id, info in active_streams.items():
        data.append({
            "app": info["app"],
            "stream": stream_id,
            "schema": "rtmp",
            "vhost": "__defaultVhost__",
            "originType": 1,
            "createStamp": int(info["start_time"]),
            "bytesSpeed": 1024 * 50, # 模拟码率
            "aliveSecond": int(time.time() - info["start_time"])
        })
    
    return {
        "code": 0,
        "msg": "success",
        "data": data
    }

# ================= 启动说明 =================
if __name__ == "__main__":
    import uvicorn
    print(f"Mock ZLM 正在启动，监听端口: {HTTP_PORT}")
    print(f"请确保你的后端服务正在运行于: {BACKEND_HOOK_URL}")
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT)