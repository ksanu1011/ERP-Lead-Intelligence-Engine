from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    TAVILY_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("GROQ_API_KEY", "TAVILY_API_KEY", mode="before")
    @classmethod
    def strip_api_key(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


settings = Settings()
