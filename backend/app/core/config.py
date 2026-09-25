from typing import List, Union
from pathlib import Path
from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import hashlib
import hmac
import os
import secrets

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"



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
    ]

    # Database (MongoDB) - credentials must come from .env, never from source
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "agriketha_ai_db"

    # Security / JWT - a random fallback means a leaked repository default
    # can never be used to forge tokens; set SECRET_KEY in .env to persist sessions.
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "logs")

    # AI Microservice integration
    QUERY_AGENT_URL: str = "http://127.0.0.1:8001"
    VISION_AGENT_URL: str = "http://127.0.0.1:8002"
    RESEARCH_AGENT_URL: str = "http://127.0.0.1:8004"

    # Shared secret sent as X-Internal-Agent-Key to the agent microservices.
    # Empty means "derive from SECRET_KEY" (see internal_agent_key).
    INTERNAL_AGENT_KEY: str = ""

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Payment Gateway (PayHere Sri Lanka Sandbox / Live)
    PAYHERE_MERCHANT_ID: str = "1211111"
    PAYHERE_MERCHANT_SECRET: str = "4TkAgriKethaSecret2026Sample"
    PAYHERE_MODE: str = "sandbox"  # sandbox or live
    PAYHERE_URL: str = "https://sandbox.payhere.lk/pay/checkout"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def internal_agent_key(self) -> str:
        """Stable inter-service key, derived from SECRET_KEY when not set explicitly."""
        if self.INTERNAL_AGENT_KEY:
            return self.INTERNAL_AGENT_KEY
        return hmac.new(self.SECRET_KEY.encode(), b"agriketha-internal-agent", hashlib.sha256).hexdigest()


settings = Settings()
