from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    ZLM_HOST: str = "http://localhost:8000"
    ZLM_SECRET: str = "035c73f7-bb6b-4889-a715-d9eb2d1925cc"
    
    class Config:
        env_file = ".env"

settings = Settings()
