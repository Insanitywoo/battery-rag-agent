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
    chunk_size: int
    chunk_overlap: int
    csv_preview_char_limit: int
    qdrant_url: str
    qdrant_api_key: str | None
    qdrant_collection_name: str
    llm_provider: str
    llm_api_base_url: str | None
    llm_api_key: str | None
    llm_chat_model: str
    llm_embedding_model: str
    rag_top_k: int
    rag_min_similarity: float
    chat_history_limit: int
    agent_enable_llm_routing: bool
    agent_min_prompt_characters: int
    agent_max_claims: int
    agent_max_comparison_documents: int

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
        chunk_size=_get_int("CHUNK_SIZE", 1000),
        chunk_overlap=_get_int("CHUNK_OVERLAP", 150),
        csv_preview_char_limit=_get_int("CSV_PREVIEW_CHAR_LIMIT", 5000),
        qdrant_url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        qdrant_collection_name=os.getenv("QDRANT_COLLECTION_NAME", "battery_rag_chunks"),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        llm_api_base_url=os.getenv("LLM_API_BASE_URL"),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_chat_model=os.getenv("LLM_CHAT_MODEL", "mock-chat"),
        llm_embedding_model=os.getenv("LLM_EMBEDDING_MODEL", "mock-embedding"),
        rag_top_k=max(1, _get_int("RAG_TOP_K", 4)),
        rag_min_similarity=float(os.getenv("RAG_MIN_SIMILARITY", "0.15")),
        chat_history_limit=max(1, _get_int("CHAT_HISTORY_LIMIT", 6)),
        agent_enable_llm_routing=_get_bool("AGENT_ENABLE_LLM_ROUTING", False),
        agent_min_prompt_characters=max(8, _get_int("AGENT_MIN_PROMPT_CHARACTERS", 18)),
        agent_max_claims=max(1, _get_int("AGENT_MAX_CLAIMS", 6)),
        agent_max_comparison_documents=max(2, _get_int("AGENT_MAX_COMPARISON_DOCUMENTS", 3)),
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
