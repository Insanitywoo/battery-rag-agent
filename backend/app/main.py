from fastapi import FastAPI

from app.api.routes import system
from app.core.config import settings


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(system.router, prefix="/api")
    return app


app = create_application()
