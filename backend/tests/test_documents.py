from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.document import Document


def register_user(client: TestClient, *, name: str, email: str, password: str):
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )


def login_user(client: TestClient, *, email: str, password: str):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )


def create_project(client: TestClient, *, name: str) -> str:
    response = client.post("/api/projects", json={"name": name, "description": "Research workspace"})
    assert response.status_code == 201
    return response.json()["id"]


def upload_document(
    client: TestClient,
    *,
    project_id: str,
    filename: str,
    content: bytes,
    content_type: str,
):
    return client.post(
        f"/api/projects/{project_id}/documents",
        files={"upload": (filename, content, content_type)},
    )


def test_document_routes_require_auth(client: TestClient) -> None:
    response = client.get("/api/projects/project-1/documents")
    assert response.status_code == 401


def test_owner_can_upload_list_detail_and_delete_document(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Battery aging")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="paper.md",
        content=b"# Experiment notes",
        content_type="text/markdown",
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()
    document_id = payload["id"]
    assert payload["original_filename"] == "paper.md"
    assert payload["file_type"] == "md"
    assert payload["status"] == "uploaded"
    assert payload["embedding_status"] == "not_indexed"

    list_response = client.get(f"/api/projects/{project_id}/documents")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/projects/{project_id}/documents/{document_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == document_id

    with get_session_factory()() as session:
        document = session.scalar(select(Document).where(Document.id == document_id))
        assert document is not None
        stored_path = Path(document.storage_path)
        assert stored_path.name == document.filename
        absolute_storage_path = get_settings().storage_root / stored_path
        assert absolute_storage_path.exists()

    delete_response = client.delete(f"/api/projects/{project_id}/documents/{document_id}")
    assert delete_response.status_code == 200

    assert not absolute_storage_path.exists()

    with get_session_factory()() as session:
        deleted_document = session.scalar(select(Document).where(Document.id == document_id))
        assert deleted_document is None

    missing_detail_response = client.get(f"/api/projects/{project_id}/documents/{document_id}")
    assert missing_detail_response.status_code == 404


def test_cross_user_document_access_is_rejected(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client:
        register_user(alice_client, name="Alice", email="alice@example.com", password="secret123")
        login_user(alice_client, email="alice@example.com", password="secret123")
        project_id = create_project(alice_client, name="Charging paper")

        upload_response = upload_document(
            alice_client,
            project_id=project_id,
            filename="results.csv",
            content=b"time,current\n0,1.2",
            content_type="text/csv",
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        cross_user_upload = upload_document(
            bob_client,
            project_id=project_id,
            filename="hack.txt",
            content=b"denied",
            content_type="text/plain",
        )
        assert cross_user_upload.status_code == 404
        assert bob_client.get(f"/api/projects/{project_id}/documents").status_code == 404
        assert bob_client.get(f"/api/projects/{project_id}/documents/{document_id}").status_code == 404
        assert bob_client.delete(f"/api/projects/{project_id}/documents/{document_id}").status_code == 404


def test_invalid_extension_or_mime_is_rejected(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Protocol")

    bad_extension = upload_document(
        client,
        project_id=project_id,
        filename="malware.exe",
        content=b"not allowed",
        content_type="text/plain",
    )
    assert bad_extension.status_code == 400

    bad_mime = upload_document(
        client,
        project_id=project_id,
        filename="paper.pdf",
        content=b"fake pdf",
        content_type="text/plain",
    )
    assert bad_mime.status_code == 400


def test_oversized_upload_is_rejected(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Large file")

    response = upload_document(
        client,
        project_id=project_id,
        filename="notes.txt",
        content=b"a" * 2049,
        content_type="text/plain",
    )
    assert response.status_code == 413
