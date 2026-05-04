from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


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


def process_document(client: TestClient, *, project_id: str, document_id: str):
    return client.post(f"/api/projects/{project_id}/documents/{document_id}/process", json={})


def build_simple_pdf(pages: list[str]) -> bytes:
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }

    page_ids: list[int] = []
    next_object_id = 4
    for page_text in pages:
        page_id = next_object_id
        content_id = next_object_id + 1
        next_object_id += 2
        page_ids.append(page_id)

        escaped_text = (
            page_text.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        stream = f"BT\n/F1 12 Tf\n72 720 Td\n({escaped_text}) Tj\nET".encode("latin-1")
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("latin-1")
        objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream"
        )

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1")

    pdf_parts: list[bytes] = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for object_id in range(1, max(objects) + 1):
        offsets.append(sum(len(part) for part in pdf_parts))
        pdf_parts.append(f"{object_id} 0 obj\n".encode("ascii"))
        pdf_parts.append(objects[object_id])
        pdf_parts.append(b"\nendobj\n")

    xref_offset = sum(len(part) for part in pdf_parts)
    xref_lines = [f"xref\n0 {max(objects) + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref_lines.append(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        f"trailer\n<< /Size {max(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("ascii")
    )
    return b"".join(pdf_parts + xref_lines + [trailer])


def test_document_processing_requires_auth(client: TestClient) -> None:
    response = client.post("/api/projects/project-1/documents/doc-1/process", json={})
    assert response.status_code == 401


def test_owner_can_process_markdown_and_persist_chunks(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Battery aging")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="paper.md",
        content=b"# Title\n\nLithium ion degradation depends on temperature and charge rate.",
        content_type="text/markdown",
    )
    document_id = upload_response.json()["id"]

    process_response = process_document(client, project_id=project_id, document_id=document_id)
    assert process_response.status_code == 200
    payload = process_response.json()
    assert payload["status"] == "processed"
    assert payload["chunk_count"] > 0
    assert payload["processed_at"] is not None

    with get_session_factory()() as session:
        chunks = list(
            session.scalars(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index.asc())
            )
        )
        assert chunks
        assert all(chunk.user_id == payload["user_id"] for chunk in chunks)
        assert all(chunk.project_id == project_id for chunk in chunks)
        assert chunks[0].char_count == len(chunks[0].content)


def test_pdf_processing_preserves_page_numbers(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="PDF project")

    pdf_bytes = build_simple_pdf(["Battery aging page one", "Battery aging page two"])
    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="paper.pdf",
        content=pdf_bytes,
        content_type="application/pdf",
    )
    document_id = upload_response.json()["id"]

    process_response = process_document(client, project_id=project_id, document_id=document_id)
    assert process_response.status_code == 200
    assert process_response.json()["status"] == "processed"

    with get_session_factory()() as session:
        page_numbers = list(
            session.scalars(
                select(DocumentChunk.page_number)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index.asc())
            )
        )
        assert 1 in page_numbers
        assert 2 in page_numbers


def test_cross_user_processing_is_rejected(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client:
        register_user(alice_client, name="Alice", email="alice@example.com", password="secret123")
        login_user(alice_client, email="alice@example.com", password="secret123")
        project_id = create_project(alice_client, name="Charging paper")

        upload_response = upload_document(
            alice_client,
            project_id=project_id,
            filename="notes.txt",
            content=b"allowed content",
            content_type="text/plain",
        )
        document_id = upload_response.json()["id"]

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        response = process_document(bob_client, project_id=project_id, document_id=document_id)
        assert response.status_code == 404


def test_reprocessing_replaces_old_chunks(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Reprocess")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="notes.txt",
        content=b"first version of the content with battery aging details",
        content_type="text/plain",
    )
    document_id = upload_response.json()["id"]

    first_process = process_document(client, project_id=project_id, document_id=document_id)
    assert first_process.status_code == 200
    first_chunk_count = first_process.json()["chunk_count"]

    with get_session_factory()() as session:
        document = session.scalar(select(Document).where(Document.id == document_id))
        assert document is not None
        storage_path = get_settings().storage_root / Path(document.storage_path)
        storage_path.write_text(
            "second version with different text and updated electrochemistry context",
            encoding="utf-8",
        )

    second_process = process_document(client, project_id=project_id, document_id=document_id)
    assert second_process.status_code == 200
    assert second_process.json()["status"] == "processed"

    with get_session_factory()() as session:
        chunks = list(
            session.scalars(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index.asc())
            )
        )
        combined_content = "\n".join(chunk.content for chunk in chunks)
        assert len(chunks) == second_process.json()["chunk_count"]
        assert "second version" in combined_content
        assert "electrochemistry" in combined_content
        assert "first version" not in combined_content
        assert second_process.json()["chunk_count"] != 0
        assert first_chunk_count != 0


def test_processing_failure_marks_document_failed_without_sensitive_path(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Failure")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="notes.txt",
        content=b"readable content",
        content_type="text/plain",
    )
    document_id = upload_response.json()["id"]

    with get_session_factory()() as session:
        document = session.scalar(select(Document).where(Document.id == document_id))
        assert document is not None
        document.storage_path = "../outside.txt"
        session.add(document)
        session.commit()

    process_response = process_document(client, project_id=project_id, document_id=document_id)
    assert process_response.status_code == 200
    payload = process_response.json()
    assert payload["status"] == "failed"
    assert payload["chunk_count"] == 0
    assert payload["error_message"] is not None
    assert "D:\\" not in payload["error_message"]
    assert "storage" not in payload["error_message"].lower()
