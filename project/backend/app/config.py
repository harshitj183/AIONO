"""
Application settings loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./aiono.db"

    # Auth
    SECRET_KEY: str = "change-this-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # App
    APP_NAME: str = "AIONO - AI Business Operations Investigator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
