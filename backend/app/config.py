"""Application configuration loaded from environment variables."""

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Base directory for backend
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core App
    APP_NAME: str = "RuleLens"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    # Keep this as a string so pydantic-settings does not try
    # to JSON-decode the environment variable before validation.
    CORS_ORIGINS: str = Field(
        default="https://rule-lens.vercel.app,http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origins",
    )

    # Database
    DATABASE_URL: str = Field(
        default="",
        description="PostgreSQL connection string loaded from environment",
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Embeddings & Vector
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384

    # LLM Providers
    GROQ_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    LLM_PROVIDER: str = "gemini"

    # Admin Panel
    ADMIN_API_KEY: str = Field(
        default="",
        description="Admin API key loaded from environment",
    )
    MAX_UPLOAD_SIZE_MB: int = 20

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if not v:
            return ""

        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]

        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]

        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a cleaned list."""

        base_origins = [
            "https://rule-lens.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

        if not self.CORS_ORIGINS:
            return base_origins

        origins = [
            origin.strip().strip("\"'").rstrip("/")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

        result = []
        seen = set()

        for origin in base_origins + origins:
            if origin and origin != "*" and origin not in seen:
                seen.add(origin)
                result.append(origin)

        return result


settings = Settings()