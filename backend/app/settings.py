"""All runtime settings, overridable with CODECLONE_* environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CODECLONE_", env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = "sqlite:///%s" % (BACKEND_DIR / "codeclone.db")
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_file_bytes: int = 200_000          # one .py file
    max_zip_bytes: int = 10_000_000        # one uploaded .zip
    max_files_per_upload: int = 500
    log_level: str = "INFO"


settings = Settings()
