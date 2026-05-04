from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.agent_task import AgentTask


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
    response = client.post("/api/projects", json={"name": name, "description": "Agent workspace"})
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


def build_knowledge_base(client: TestClient, *, project_id: str):
    return client.post(f"/api/projects/{project_id}/knowledge-base/build", json={})


def test_owner_can_run_agent_research_qa_and_task_is_persisted(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Agent QA")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="battery-notes.md",
        content=b"Battery aging accelerates under elevated temperature cycling.",
        content_type="text/markdown",
    )
    document_id = upload_response.json()["id"]
    assert process_document(client, project_id=project_id, document_id=document_id).status_code == 200
    assert build_knowledge_base(client, project_id=project_id).status_code == 200

    response = client.post(
        f"/api/projects/{project_id}/agent/run",
        json={"user_input": "What does this project say about battery aging?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["task_type"] == "research_qa"
    assert payload["result_json"]["routed_task_type"] == "research_qa"
    assert "grounded answer" in payload["result_json"]["answer"]
    assert payload["result_json"]["sources"]

    with get_session_factory()() as session:
        task = session.scalar(select(AgentTask).where(AgentTask.id == payload["id"]))
        assert task is not None
        assert task.user_id == payload["user_id"]
        assert task.project_id == project_id
        assert task.status == "completed"
        assert task.result_json is not None


def test_ambiguous_prompt_returns_clarification_task(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Clarification")

    response = client.post(
        f"/api/projects/{project_id}/agent/run",
        json={"user_input": "help"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "needs_clarification"
    assert payload["result_json"]["clarification"]
    assert payload["result_json"]["sources"] == []


def test_evidence_check_returns_unsupported_claims(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="Evidence Check")

    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="paper.txt",
        content=b"Battery cells degrade faster at elevated temperature.",
        content_type="text/plain",
    )
    document_id = upload_response.json()["id"]
    assert process_document(client, project_id=project_id, document_id=document_id).status_code == 200
    assert build_knowledge_base(client, project_id=project_id).status_code == 200

    response = client.post(
        f"/api/projects/{project_id}/agent/run",
        json={
            "user_input": (
                "Battery cells degrade faster at elevated temperature.\n"
                "This project proves every lithium battery is perfectly safe."
            ),
            "task_type": "evidence_check",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["task_type"] == "evidence_check"
    assert payload["result_json"]["supported_claims"]
    assert payload["result_json"]["unsupported_claims"]
    assert payload["result_json"]["sources"]


def test_agent_execution_is_owner_scoped(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client:
        register_user(alice_client, name="Alice", email="alice@example.com", password="secret123")
        login_user(alice_client, email="alice@example.com", password="secret123")
        project_id = create_project(alice_client, name="Owner Agent")

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        response = bob_client.post(
            f"/api/projects/{project_id}/agent/run",
            json={"user_input": "Summarize this project."},
        )
        assert response.status_code == 404
