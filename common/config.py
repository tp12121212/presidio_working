from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="PRESIDIO_SIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "presidio-sit-service"
    database_url: str = "sqlite:///./presidio_sit.db"
    redis_url: str = "redis://redis:6379/0"
    storage_path: Path = Path("/data/uploads")
    scan_root: Path = Path("/data/uploads")
    max_archive_depth: int = 3
    max_archive_files: int = 1000
    max_file_size_mb: int = 250
    ocr_max_pages: int = 20
    ocr_concurrency: int = 2
    log_level: str = "INFO"
    sqlalchemy_echo: bool = False


settings = Settings()
