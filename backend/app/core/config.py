from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _get_cors_origins() -> tuple[str, ...]:
    raw = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000")
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


def _get_csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.getenv(name, default)
    return tuple(item.strip().lower() for item in raw.split(",") if item.strip())


def _default_database_url() -> str:
    if explicit := os.getenv("DATABASE_URL"):
        return explicit

    user = os.getenv("POSTGRES_USER", "battery_rag")
    password = os.getenv("POSTGRES_PASSWORD", "battery_rag_password")
    database = os.getenv("POSTGRES_DB", "battery_rag")
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


@dataclass(frozen=True)
class Settings:
    project_name: str
    project_slug: str
    app_env: str
    backend_host: str
    backend_port: int
    backend_cors_origins: tuple[str, ...]
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    access_token_ttl_minutes: int
    cookie_name: str
    cookie_secure: bool
    cookie_samesite: str
    storage_root: Path
    max_upload_size_bytes: int
    allowed_upload_extensions: tuple[str, ...]
    allowed_upload_mime_types: tuple[str, ...]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET environment variable is required.")

    return Settings(
        project_name=os.getenv("PROJECT_NAME", "Battery-RAG Agent"),
        project_slug="battery-rag-agent-backend",
        app_env=os.getenv("APP_ENV", "development"),
        backend_host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        backend_port=_get_int("BACKEND_PORT", 8000),
        backend_cors_origins=_get_cors_origins(),
        database_url=_default_database_url(),
        jwt_secret=jwt_secret,
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_ttl_minutes=_get_int("ACCESS_TOKEN_TTL_MINUTES", 60),
        cookie_name=os.getenv("COOKIE_NAME", "access_token"),
        cookie_secure=_get_bool("COOKIE_SECURE", False),
        cookie_samesite=os.getenv("COOKIE_SAMESITE", "lax"),
        storage_root=(ROOT_DIR / os.getenv("STORAGE_ROOT", "storage")).resolve(),
        max_upload_size_bytes=_get_int("MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024),
        allowed_upload_extensions=_get_csv("ALLOWED_UPLOAD_EXTENSIONS", ".pdf,.txt,.md,.csv"),
        allowed_upload_mime_types=_get_csv(
            "ALLOWED_UPLOAD_MIME_TYPES",
            "application/pdf,text/plain,text/markdown,text/csv,application/csv",
        ),
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
