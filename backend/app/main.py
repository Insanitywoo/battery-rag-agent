from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agent, auth, chat, documents, external_references, knowledge_base, projects, system, writing
from app.core.config import get_settings
from app.db.session import init_db
from app.services.storage import ensure_storage_root


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ensure_storage_root()
    yield


def create_application() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.backend_cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(knowledge_base.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(agent.router, prefix="/api")
    app.include_router(writing.router, prefix="/api")
    app.include_router(external_references.router, prefix="/api")
    app.include_router(system.router, prefix="/api")
    return app


app = create_application()
