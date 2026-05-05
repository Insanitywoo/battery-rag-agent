from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.writing_artifact import WritingArtifact

from test_agent_framework import (
    build_knowledge_base,
    create_project,
    login_user,
    process_document,
    register_user,
    upload_document,
)


def prepare_project_with_knowledge(client: TestClient, *, project_name: str = "Writing Workspace") -> str:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name=project_name)
    upload_response = upload_document(
        client,
        project_id=project_id,
        filename="notes.md",
        content=(
            b"Battery aging accelerates under elevated temperature cycling.\n"
            b"State-of-health estimation benefits from physics-informed features.\n"
            b"Thermal gradients affect degradation consistency."
        ),
        content_type="text/markdown",
    )
    document_id = upload_response.json()["id"]
    assert process_document(client, project_id=project_id, document_id=document_id).status_code == 200
    assert build_knowledge_base(client, project_id=project_id).status_code == 200
    return project_id


def test_owner_can_generate_list_detail_and_export_writing_artifact(client: TestClient) -> None:
    project_id = prepare_project_with_knowledge(client, project_name="Writing Outline")

    response = client.post(
        f"/api/projects/{project_id}/writing/run",
        json={
            "task_type": "outline",
            "topic": "Battery aging paper",
            "research_direction": "Lithium-ion degradation modeling",
            "requirements": "Focus on temperature-driven degradation evidence.",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["artifact_type"] == "outline"
    assert payload["sources"]
    assert "Battery aging paper" in payload["title"]
    assert payload["warnings"]

    with get_session_factory()() as session:
        artifact = session.scalar(select(WritingArtifact).where(WritingArtifact.id == payload["id"]))
        assert artifact is not None
        assert artifact.user_id == payload["user_id"]
        assert artifact.project_id == project_id
        assert artifact.sources_json

    list_response = client.get(f"/api/projects/{project_id}/writing/artifacts")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/projects/{project_id}/writing/artifacts/{payload['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == payload["id"]

    export_response = client.get(f"/api/projects/{project_id}/writing/artifacts/{payload['id']}/export/markdown")
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/markdown")
    assert payload["title"] in export_response.text


def test_citation_check_persists_unsupported_claims(client: TestClient) -> None:
    project_id = prepare_project_with_knowledge(client, project_name="Citation Check")

    response = client.post(
        f"/api/projects/{project_id}/writing/run",
        json={
            "task_type": "citation_check",
            "topic": "Claim support review",
            "requirements": (
                "Battery aging accelerates under elevated temperature cycling.\n"
                "This project proves every battery pack is perfectly safe."
            ),
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["artifact_type"] == "citation_check"
    assert payload["unsupported_claims"]
    assert any("perfectly safe" in claim for claim in payload["unsupported_claims"])
    assert payload["warnings"]


def test_writing_routes_require_auth_and_remain_owner_scoped(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client, TestClient(app) as anon_client:
        project_id = prepare_project_with_knowledge(alice_client, project_name="Owner Writing")
        run_response = alice_client.post(
            f"/api/projects/{project_id}/writing/run",
            json={
                "task_type": "method_framework",
                "topic": "State-of-health estimation method",
                "requirements": "Focus on evidence from this project only.",
            },
        )
        artifact_id = run_response.json()["id"]

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        anon_response = anon_client.get(f"/api/projects/{project_id}/writing/artifacts")
        assert anon_response.status_code == 401

        bob_list = bob_client.get(f"/api/projects/{project_id}/writing/artifacts")
        assert bob_list.status_code == 404

        bob_detail = bob_client.get(f"/api/projects/{project_id}/writing/artifacts/{artifact_id}")
        assert bob_detail.status_code == 404

        bob_delete = bob_client.delete(f"/api/projects/{project_id}/writing/artifacts/{artifact_id}")
        assert bob_delete.status_code == 404

        delete_response = alice_client.delete(f"/api/projects/{project_id}/writing/artifacts/{artifact_id}")
        assert delete_response.status_code == 200

        with get_session_factory()() as session:
            artifact = session.scalar(select(WritingArtifact).where(WritingArtifact.id == artifact_id))
            assert artifact is None
