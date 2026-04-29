from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    project_name: str = os.getenv("PROJECT_NAME", "Battery-RAG Agent")
    project_slug: str = "battery-rag-agent-backend"
    app_env: str = os.getenv("APP_ENV", "development")


settings = Settings()
