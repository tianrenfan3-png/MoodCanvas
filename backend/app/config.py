from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "production", "test"] = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    firebase_credentials_path: str | None = None
    firebase_credentials_json: str | None = None
    firestore_project_id: str | None = None
    use_firestore_emulator: bool = False
    firestore_emulator_host: str = "localhost:8080"

    clip_model: str = "ViT-B/32"
    clip_temperature: float = 0.07
    analyzer_type: Literal["clip", "mock"] = "clip"

    max_upload_bytes: int = 5 * 1024 * 1024
    predict_rate_limit: str = "30/hour"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        # GitHub Pages project sites (e.g. https://user.github.io/repo/) send this origin.
        return r"https://[\w-]+\.github\.io"


@lru_cache
def get_settings() -> Settings:
    return Settings()
