from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AnyHttpUrl, BaseSettings, Field, validator


class Settings(BaseSettings):
    app_name: str = "AI Fairytale Audio Generator"
    environment: str = Field(default="development")
    database_url: str = Field(default="sqlite:///../../data/db.sqlite3")
    log_directory: Path = Field(default=Path("/logs"))
    log_level: str = Field(default="INFO")
    log_retention_days: int = Field(default=7)
    allowed_origins: List[AnyHttpUrl] = Field(default_factory=list)
    rate_limit_requests: int = Field(default=60)
    rate_limit_window_seconds: int = Field(default=60)

    data_directory: Path = Field(default=Path("data"))
    assets_subdir: str = Field(default="assets")
    exports_subdir: str = Field(default="exports")

    piper_binary: Path | None = Field(default=None)
    piper_model_path: Path | None = Field(default=None)
    piper_model_checksum: str | None = Field(default=None)
    piper_config_path: Path | None = Field(default=None)
    piper_config_checksum: str | None = Field(default=None)
    piper_max_retries: int = Field(default=3)
    piper_retry_backoff_seconds: float = Field(default=1.5)
    piper_enable_fallback: bool = Field(default=False)

    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("data_directory", pre=True)
    def _coerce_data_directory(cls, value: str | Path) -> Path:
        path_value = Path(value)
        path_value.mkdir(parents=True, exist_ok=True)
        return path_value

    @validator("log_directory", pre=True)
    def _coerce_log_directory(cls, value: str | Path) -> Path:
        return Path(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    data_dir = settings.data_directory
    (data_dir / settings.assets_subdir).mkdir(parents=True, exist_ok=True)
    (data_dir / settings.exports_subdir).mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
