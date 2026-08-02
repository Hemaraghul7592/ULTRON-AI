from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "ULTRON"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    DATABASE_URL: str = "sqlite+aiosqlite:///./ultron.db"
    DB_ECHO: bool = False

    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    ADMIN_USER_IDS: list[str] = []

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENAI_API_KEY: SecretStr = SecretStr("")
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROK_API_KEY: SecretStr = SecretStr("")
    GROK_MODEL: str = "grok-2-latest"
    DEFAULT_AI_PROVIDER: str = "groq"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 4096

    OPEN_WEATHER_API_KEY: str = ""
    OCR_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REFRESH_TOKEN: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    GITHUB_TOKEN: str = ""
    NOTION_API_KEY: str = ""

    TTS_ENABLED: bool = True
    STT_ENABLED: bool = True
    WAKE_WORD_ENABLED: bool = False
    TTS_MODEL: str = "tts-1"
    STT_MODEL: str = "whisper-1"

    REDIS_URL: str = ""
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    MAX_CONCURRENT_JOBS: int = 10
    EMBEDDING_DIM: int = 384

    MEMORY_SHORT_TERM_MAX: int = 50
    MEMORY_LONG_TERM_THRESHOLD: float = 0.7
    MEMORY_SUMMARIZATION_THRESHOLD: int = 10

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json

            return json.loads(v)
        return v

    @model_validator(mode="after")
    def validate_secret_key(self) -> Settings:
        insecure_defaults = {
            "change-me-in-production",
            "change-me-in-production-use-openssl-rand-hex-32",
        }
        if self.SECRET_KEY in insecure_defaults:
            raise ValueError(
                "SECRET_KEY must be changed from the default value. "
                "Generate a strong key with: openssl rand -hex 32",
            )
        return self

    @model_validator(mode="after")
    def validate_encryption_key(self) -> Settings:
        if not self.ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY is required. Generate one with: "
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',
            )
        return self

    @property
    def is_postgres(self) -> bool:
        return "postgresql" in self.DATABASE_URL

    def get_configured_api_keys(self) -> dict[str, bool]:
        return {
            "GROQ_API_KEY": bool(self.GROQ_API_KEY),
            "GEMINI_API_KEY": bool(self.GEMINI_API_KEY),
            "OPENAI_API_KEY": bool(self.OPENAI_API_KEY.get_secret_value()),
            "GROK_API_KEY": bool(self.GROK_API_KEY.get_secret_value()),
            "OPEN_WEATHER_API_KEY": bool(self.OPEN_WEATHER_API_KEY),
            "OCR_API_KEY": bool(self.OCR_API_KEY),
            "TAVILY_API_KEY": bool(self.TAVILY_API_KEY),
            "GOOGLE_CLIENT_ID": bool(self.GOOGLE_CLIENT_ID),
            "GOOGLE_CLIENT_SECRET": bool(self.GOOGLE_CLIENT_SECRET),
            "GOOGLE_REFRESH_TOKEN": bool(self.GOOGLE_REFRESH_TOKEN),
            "GOOGLE_MAPS_API_KEY": bool(self.GOOGLE_MAPS_API_KEY),
            "GITHUB_TOKEN": bool(self.GITHUB_TOKEN),
            "NOTION_API_KEY": bool(self.NOTION_API_KEY),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
