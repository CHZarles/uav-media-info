"""CLI tool to POST a mock drone registration to /api/stream/register."""
import argparse
import json
import sys
from typing import Any, Dict

import requests


def send_registration(base_url: str, payload: Dict[str, Any]) -> None:
    """Send registration payload and print the response."""
    url = base_url.rstrip("/") + "/api/stream/register"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
    except requests.RequestException as exc:  # network or connection issue
        print(f"Request failed: {exc}")
        sys.exit(1)

    print(f"Status: {response.status_code}")
    try:
        parsed = response.json()
        print("Response JSON:\n" + json.dumps(parsed, indent=2, ensure_ascii=False))
    except ValueError:
        print("Response body:\n" + response.text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate drone registration call.")
    # 加 default values for easier testing
    parser.add_argument("--base-url", default="http://localhost:8000", help="Gateway base URL")
    parser.add_argument("--drone-id", default="drone123", help="Drone identifier")
    parser.add_argument("--stream-id", default="stream123", help="Stream identifier")
    parser.add_argument("--name", default="Test Drone", help="Drone display name")
    parser.add_argument("--model", default="demo-model", help="Drone model")
    parser.add_argument(
        "--extra-json",
        default=None,
        help="Optional JSON string for extra fields",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    extra: Dict[str, Any] = {}
    if args.extra_json:
        try:
            extra = json.loads(args.extra_json)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON for --extra-json: {exc}")
            sys.exit(1)

    payload: Dict[str, Any] = {
        "drone_id": args.drone_id,
        "stream_id": args.stream_id,
        "name": args.name,
        "model": args.model,
    }
    if extra:
        payload.update(extra)

    send_registration(args.base_url, payload)


if __name__ == "__main__":
    main()
