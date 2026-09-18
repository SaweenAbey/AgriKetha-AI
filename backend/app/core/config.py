from typing import List, Union
from pathlib import Path
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os



class Settings(BaseSettings):
    PROJECT_NAME: str = "AgriKetha-AI Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*"
    ]

    # Database (MongoDB)
    MONGODB_URL: str = "mongodb+srv://saween910_db_user:pLRnbXw5JLISQoTR@cluster0.dqyxqug.mongodb.net/?appName=Cluster0"
    DATABASE_NAME: str = "agriketha_ai_db"

    # Security / JWT
    SECRET_KEY: str = "agriketha_super_secret_jwt_key_for_development_change_in_production_xyz123!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "logs")

    # AI Microservice integrations
    QUERY_AGENT_URL: str = "http://127.0.0.1:8001"
    VISION_AGENT_URL: str = "http://127.0.0.1:8002"
    RESEARCH_AGENT_URL: str = "http://127.0.0.1:8003"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
