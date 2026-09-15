import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Creation of Intelligent Bug Diagnosis Platform with Fix Recommendation Assistance"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # SQLite default, easily overridden via DATABASE_URL env var (e.g. postgresql://user:pass@localhost/dbname)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database/app.db")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
