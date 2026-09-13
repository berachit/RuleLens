"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from typing import List, Union
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
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=[
            "https://rule-lens.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins for production and local development",
    )

    # Database — loaded strictly from environment variable DATABASE_URL
    DATABASE_URL: str = Field(default="", description="PostgreSQL connection string loaded from environment")
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Embeddings & Vector
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384

    # LLM Providers — loaded strictly from environment variables
    GROQ_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    LLM_PROVIDER: str = "gemini"

    # Admin Panel — loaded strictly from environment variable ADMIN_API_KEY
    ADMIN_API_KEY: str = Field(default="", description="Admin API key loaded from environment")
    MAX_UPLOAD_SIZE_MB: int = 20

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if not v:
            return ""
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        base_origins = [
            "https://rule-lens.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        if not v:
            return base_origins

        parsed: List[str] = []
        if isinstance(v, str):
            v_s = v.strip()
            if (v_s.startswith("[") and v_s.endswith("]")) or (v_s.startswith("{") and v_s.endswith("}")):
                import json
                try:
                    loaded = json.loads(v_s)
                    if isinstance(loaded, list):
                        parsed = [str(x) for x in loaded]
                except Exception:
                    v_s = v_s.strip("[]").strip()
            if not parsed and v_s and v_s not in ("[]", '""', "''"):
                parsed = [x for x in v_s.split(",")]
        elif isinstance(v, list):
            parsed = [str(x) for x in v]

        cleaned: List[str] = []
        for item in parsed:
            s = item.strip().strip("\"'").rstrip("/")
            if s and s != "*":
                cleaned.append(s)

        seen = set()
        result: List[str] = []
        for origin in base_origins + cleaned:
            if origin and origin not in seen:
                seen.add(origin)
                result.append(origin)
        return result


settings = Settings()
