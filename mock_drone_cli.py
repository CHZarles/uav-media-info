"""
CLI tool to:
1. Register a mock drone to the Backend Gateway (/api/stream/register).
2. Control the Mock ZLMediaKit to start/stop streaming (/control/start_stream).
"""
import argparse
import json
import sys
import time
from typing import Any, Dict

import requests

def _post_request(url: str, payload: Dict[str, Any], description: str) -> bool:
    """Helper to send POST request and print status."""
    print(f"\n--- {description} ---")
    print(f"Target: {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
    except requests.RequestException as exc:
        print(f"❌ Request failed: {exc}")
        return False

    if response.status_code == 200:
        print(f"✅ Success ({response.status_code})")
        try:
            print("Response:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        except ValueError:
            print("Response:", response.text)
        return True
    else:
        print(f"⚠️ Failed ({response.status_code})")
        print("Response:", response.text)
        return False


def register_drone(base_url: str, args: argparse.Namespace) -> bool:
    """Send registration payload to the Business Backend."""
    url = base_url.rstrip("/") + "/api/stream/register"
    
    # 构建注册数据
    extra: Dict[str, Any] = {}
    if args.extra_json:
        try:
            extra = json.loads(args.extra_json)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON for --extra-json: {exc}")
            sys.exit(1)

    payload = {
        "drone_id": args.drone_id,
        "stream_id": args.stream_id,
        "name": args.name,
        "model": args.model,
    }
    if extra:
        payload.update(extra)

    return _post_request(url, payload, "1. Registering Device to Backend")


def control_zlm_stream(zlm_url: str, stream_id: str, action: str) -> bool:
    """Send control command to Mock ZLM Service."""
    if action == "start":
        endpoint = "/control/start_stream"
        desc = "2. Triggering Mock ZLM (Start Stream)"
    elif action == "stop":
        endpoint = "/control/stop_stream"
        desc = "Triggering Mock ZLM (Stop Stream)"
    else:
        return False

    url = zlm_url.rstrip("/") + endpoint
    payload = {
        "stream_id": stream_id,
        "app": "live"
    }
    
    return _post_request(url, payload, desc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate drone registration and ZLM streaming.")
    
    # 基础配置
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Business Backend URL")
    parser.add_argument("--zlm-url", default="http://localhost:9000", help="Mock ZLM Service URL")
    
    # 动作选择
    parser.add_argument("--action", choices=["register", "start", "stop", "full"], default="register",
                        help="Action to perform: 'register' (only DB), 'start' (only ZLM), 'stop' (only ZLM), 'full' (Register + Start ZLM)")
    
    # 设备参数
    parser.add_argument("--drone-id", default="drone123", help="Drone identifier")
    parser.add_argument("--stream-id", default="stream123", help="Stream identifier")
    parser.add_argument("--name", default="Test Drone", help="Drone display name")
    parser.add_argument("--model", default="demo-model", help="Drone model")
    parser.add_argument("--extra-json", default=None, help="Optional JSON string for extra fields")
    
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1. 仅注册
    if args.action == "register":
        register_drone(args.backend_url, args)

    # 2. 仅通知 ZLM 开始推流 (假设已注册)
    elif args.action == "start":
        control_zlm_stream(args.zlm_url, args.stream_id, "start")

    # 3. 仅通知 ZLM 断开流
    elif args.action == "stop":
        control_zlm_stream(args.zlm_url, args.stream_id, "stop")

    # 4. 全套流程：先注册，再推流
    elif args.action == "full":
        success = register_drone(args.backend_url, args)
        if success:
            # 稍微停顿一下，模拟真实网络延迟
            time.sleep(0.2)
            control_zlm_stream(args.zlm_url, args.stream_id, "start")
        else:
            print("Skipping ZLM trigger due to registration failure.")

if __name__ == "__main__":
    main()
