from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==== DATABASE =========================================================
    DB_URL: str | None = None

    # ==== LLM KEYS =========================================================
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    # ==== RUNTIME FLAGS ====================================================
    USE_STUB: bool = True
    LOG_LEVEL: str = "INFO"
    JSON_LOG: bool = False

    # ==== INTERNAL =========================================================
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DB_URL:
            return self.DB_URL
        return "sqlite:////tmp/math_copilot_dev.db"


settings = Settings()
