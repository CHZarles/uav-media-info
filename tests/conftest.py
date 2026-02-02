import os

import pytest
from fastapi.testclient import TestClient


# Ensure test runs don't create log files and always build play URLs deterministically.
os.environ.setdefault("LOG_FILE", "")
os.environ.setdefault("ZLM_HOST", "http://localhost:9000")
# Default to the repo's dev database settings; CI overrides via workflow env.
os.environ.setdefault("DATABASE_URL", "postgresql://uav_user:change_me@localhost:5432/uav")


from app.core import state  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.models import VideoRecord  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_state_and_db() -> None:
    state.DRONE_SESSIONS.clear()
    state.DRONE_ID_MAP.clear()

    db = SessionLocal()
    try:
        db.query(VideoRecord).delete()
        db.commit()
    finally:
        db.close()
