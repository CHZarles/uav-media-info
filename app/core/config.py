from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"

    ZLM_HOST: str = "http://localhost:8000"
    ZLM_SECRET: str = "035c73f7-bb6b-4889-a715-d9eb2d1925cc"

    LOG_LEVEL: str = "INFO"           # Controls application log verbosity
    LOG_FILE: Optional[str] = "logs/app.log"  # If set, logs also persist to this file
    LOG_FILE_MAX_BYTES: int = 5 * 1024 * 1024  # Rotate when exceeding this size (bytes)

    class Config:
        env_file = ".env"


settings = Settings()
