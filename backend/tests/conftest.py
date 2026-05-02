from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def app(tmp_path: Path):
    db_path = tmp_path / "test.db"
    storage_root = tmp_path / "storage"

    os.environ["APP_ENV"] = "development"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["COOKIE_SECURE"] = "false"
    os.environ["COOKIE_SAMESITE"] = "lax"
    os.environ["BACKEND_CORS_ORIGINS"] = "http://localhost:3000"
    os.environ["STORAGE_ROOT"] = str(storage_root)
    os.environ["MAX_UPLOAD_SIZE_BYTES"] = "2048"

    from app.core.config import clear_settings_cache
    from app.db.session import clear_db_cache, init_db
    from app.main import create_application

    clear_settings_cache()
    clear_db_cache()
    application = create_application()
    init_db()
    yield application
    clear_db_cache()
    clear_settings_cache()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client
