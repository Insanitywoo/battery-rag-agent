from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.rag import INSUFFICIENT_INFORMATION_TEXT
from app.services.vector_store import _MEMORY_STORE


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


def create_session(client: TestClient, *, project_id: str, title: str = "Research chat") -> str:
    response = client.post(
        f"/api/projects/{project_id}/chat/sessions",
        json={"title": title},
    )
    assert response.status_code == 201
    return response.json()["id"]


def build_knowledge_base(client: TestClient, *, project_id: str):
    return client.post(f"/api/projects/{project_id}/knowledge-base/build", json={})


def stream_question(client: TestClient, *, project_id: str, session_id: str, question: str) -> str:
    with client.stream(
        "POST",
        f"/api/projects/{project_id}/chat/sessions/{session_id}/messages/stream",
        json={"question": question},
    ) as response:
        assert response.status_code == 200
        return "".join(chunk for chunk in response.iter_text() if chunk)


def test_owner_can_build_project_knowledge_base_and_detail_reflects_status(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Vector build")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="paper.md",
        content=b"# Title\nBattery aging depends on state of charge and temperature.",
        content_type="text/markdown",
    )
    document_id = upload_response.json()["id"]
    process_response = process_document(client, project_id=project_id, document_id=document_id)
    assert process_response.status_code == 200

    build_response = build_knowledge_base(client, project_id=project_id)
    assert build_response.status_code == 200
    payload = build_response.json()
    assert payload["knowledge_base"]["embedded_documents"] == 1
    assert payload["knowledge_base"]["can_chat"] is True
    assert payload["knowledge_base"]["indexed_chunks"] > 0

    detail_response = client.get(f"/api/projects/{project_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["knowledge_base"]["can_chat"] is True

    with get_session_factory()() as session:
        document = session.scalar(select(Document).where(Document.id == document_id))
        assert document is not None
        assert document.embedding_status == "indexed"
        assert document.embedded_at is not None


def test_rebuild_replaces_project_vectors_in_memory_store(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Rebuild vectors")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="notes.txt",
        content=b"first vectorized battery aging content",
        content_type="text/plain",
    )
    document_id = upload_response.json()["id"]
    process_document(client, project_id=project_id, document_id=document_id)
    first_build = build_knowledge_base(client, project_id=project_id)
    assert first_build.status_code == 200

    with get_session_factory()() as session:
        first_chunk_ids = list(
            session.scalars(
                select(DocumentChunk.id)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index.asc())
            )
        )
        document = session.scalar(select(Document).where(Document.id == document_id))
        assert document is not None
        storage_path = get_settings().storage_root / Path(document.storage_path)
        storage_path.write_text("second vectorized electrochemistry content", encoding="utf-8")

    process_document(client, project_id=project_id, document_id=document_id)
    second_build = build_knowledge_base(client, project_id=project_id)
    assert second_build.status_code == 200

    with get_session_factory()() as session:
        second_chunk_ids = list(
            session.scalars(
                select(DocumentChunk.id)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index.asc())
            )
        )

    collection = _MEMORY_STORE[get_settings().qdrant_collection_name]
    assert set(collection.keys()) == set(second_chunk_ids)
    assert set(first_chunk_ids) != set(second_chunk_ids)


def test_streaming_chat_persists_final_assistant_message_and_sources(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Chat project")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="paper.md",
        content=b"# Cells\nBattery aging increases when cells are cycled at elevated temperature.",
        content_type="text/markdown",
    )
    document_id = upload_response.json()["id"]
    process_document(client, project_id=project_id, document_id=document_id)
    build_knowledge_base(client, project_id=project_id)
    session_id = create_session(client, project_id=project_id)

    answer = stream_question(
        client,
        project_id=project_id,
        session_id=session_id,
        question="What does the project knowledge base say about battery aging?",
    )
    assert "grounded answer" in answer

    session_response = client.get(f"/api/projects/{project_id}/chat/sessions/{session_id}")
    assert session_response.status_code == 200
    session_payload = session_response.json()
    assert len(session_payload["messages"]) == 2
    assistant_message = session_payload["messages"][1]
    assert assistant_message["role"] == "assistant"
    assert assistant_message["content"] == answer
    assert assistant_message["sources_json"]
    source = assistant_message["sources_json"][0]
    assert source["document_id"] == document_id
    assert source["document_name"] == "paper.md"
    assert "chunk_id" in source
    assert "excerpt" in source


def test_insufficient_retrieval_returns_exact_fallback_and_empty_sources(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Fallback project")
    session_id = create_session(client, project_id=project_id)

    answer = stream_question(
        client,
        project_id=project_id,
        session_id=session_id,
        question="What is the diffusion coefficient?",
    )
    assert answer == INSUFFICIENT_INFORMATION_TEXT

    session_response = client.get(f"/api/projects/{project_id}/chat/sessions/{session_id}")
    assistant_message = session_response.json()["messages"][1]
    assert assistant_message["content"] == INSUFFICIENT_INFORMATION_TEXT
    assert assistant_message["sources_json"] == []


def test_chat_sessions_remain_owner_scoped(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client:
        register_user(alice_client, name="Alice", email="alice@example.com", password="secret123")
        login_user(alice_client, email="alice@example.com", password="secret123")
        project_id = create_project(alice_client, name="Owner chat")
        session_id = create_session(alice_client, project_id=project_id)

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        assert bob_client.get(f"/api/projects/{project_id}/chat/sessions").status_code == 404
        assert bob_client.get(f"/api/projects/{project_id}/chat/sessions/{session_id}").status_code == 404
        assert bob_client.delete(f"/api/projects/{project_id}/chat/sessions/{session_id}").status_code == 404

        owner_delete = alice_client.delete(f"/api/projects/{project_id}/chat/sessions/{session_id}")
        assert owner_delete.status_code == 200

        with get_session_factory()() as session:
            deleted_session = session.scalar(select(ChatSession).where(ChatSession.id == session_id))
            remaining_messages = list(session.scalars(select(ChatMessage).where(ChatMessage.session_id == session_id)))
            assert deleted_session is None
            assert remaining_messages == []
