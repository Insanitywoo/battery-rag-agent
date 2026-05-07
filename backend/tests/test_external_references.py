from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_session_factory
from app.models.external_reference import ExternalReference
from app.services.external_references import ExternalReferenceCandidate, dedupe_candidates

from test_agent_framework import create_project, login_user, register_user
from test_writing_api import prepare_project_with_knowledge


def build_candidate(*, title: str = "Battery thermal management review", doi: str | None = "10.1000/example-doi"):
    return {
        "source": "crossref",
        "title": title,
        "authors": ["Alice Smith", "Bob Zhang"],
        "year": 2024,
        "venue": "Journal of Battery Systems",
        "doi": doi,
        "url": "https://doi.org/10.1000/example-doi",
        "abstract": "A bounded metadata record for testing project-scoped external references.",
        "warnings": [],
    }


def test_dedupe_candidates_prefers_doi_then_title() -> None:
    candidates = [
        ExternalReferenceCandidate(source="crossref", title="Battery review", doi="10.1000/abc", authors=["A"]),
        ExternalReferenceCandidate(source="arxiv", title="Battery review", doi="10.1000/abc", authors=["A", "B"], abstract="More complete"),
        ExternalReferenceCandidate(source="crossref", title="Thermal management for batteries", doi=None),
        ExternalReferenceCandidate(source="arxiv", title="Thermal management for batteries", doi=None, authors=["X"]),
    ]

    deduped = dedupe_candidates(candidates)
    assert len(deduped) == 2
    assert any(candidate.abstract == "More complete" for candidate in deduped)
    assert any(candidate.title == "Thermal management for batteries" and candidate.authors == ["X"] for candidate in deduped)


def test_owner_can_search_save_list_export_and_delete_external_references(client: TestClient, monkeypatch) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")
    project_id = create_project(client, name="External References")

    class FakeRegistry:
        def search(self, *, provider, search_input):
            assert provider == "all"
            assert search_input.query == "battery thermal management"
            return (
                [
                    ExternalReferenceCandidate(**build_candidate()),
                    ExternalReferenceCandidate(**build_candidate()),
                ],
                ["Crossref search failed."],
            )

    monkeypatch.setattr("app.api.routes.external_references.get_external_tool_registry", lambda: FakeRegistry())

    search_response = client.post(
        f"/api/projects/{project_id}/external-references/search",
        json={"query": "battery thermal management", "provider": "all", "limit": 6},
    )
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert len(search_payload["results"]) == 2
    assert search_payload["warnings"] == ["Crossref search failed."]

    save_response = client.post(
        f"/api/projects/{project_id}/external-references",
        json=build_candidate(),
    )
    assert save_response.status_code == 201
    saved_id = save_response.json()["id"]

    duplicate_response = client.post(
        f"/api/projects/{project_id}/external-references",
        json=build_candidate(),
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["id"] == saved_id

    list_response = client.get(f"/api/projects/{project_id}/external-references")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload) == 1
    assert list_payload[0]["bibtex"]

    export_response = client.get(f"/api/projects/{project_id}/external-references/export/bibtex")
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("application/x-bibtex")
    assert "Manual verification required" in export_response.text
    assert "Battery thermal management review" in export_response.text

    with get_session_factory()() as session:
        reference = session.scalar(select(ExternalReference).where(ExternalReference.id == saved_id))
        assert reference is not None
        assert reference.user_id == list_payload[0]["user_id"]
        assert reference.project_id == project_id

    delete_response = client.delete(f"/api/projects/{project_id}/external-references/{saved_id}")
    assert delete_response.status_code == 200

    with get_session_factory()() as session:
        reference = session.scalar(select(ExternalReference).where(ExternalReference.id == saved_id))
        assert reference is None


def test_external_reference_routes_require_auth_and_are_owner_scoped(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client, TestClient(app) as anon_client:
        register_user(alice_client, name="Alice", email="alice@example.com", password="secret123")
        login_user(alice_client, email="alice@example.com", password="secret123")
        project_id = create_project(alice_client, name="Owner Scoped References")
        save_response = alice_client.post(
            f"/api/projects/{project_id}/external-references",
            json=build_candidate(),
        )
        reference_id = save_response.json()["id"]

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        anon_search = anon_client.post(
            f"/api/projects/{project_id}/external-references/search",
            json={"query": "battery", "provider": "all", "limit": 6},
        )
        assert anon_search.status_code == 401

        bob_list = bob_client.get(f"/api/projects/{project_id}/external-references")
        assert bob_list.status_code == 404

        bob_delete = bob_client.delete(f"/api/projects/{project_id}/external-references/{reference_id}")
        assert bob_delete.status_code == 404

        bob_export = bob_client.get(f"/api/projects/{project_id}/external-references/export/bibtex")
        assert bob_export.status_code == 404


def test_agent_and_writing_can_reuse_saved_external_references(client: TestClient) -> None:
    project_id = prepare_project_with_knowledge(client, project_name="External Reference Reuse")
    save_response = client.post(
        f"/api/projects/{project_id}/external-references",
        json=build_candidate(title="External battery survey", doi=None),
    )
    assert save_response.status_code == 201

    agent_response = client.post(
        f"/api/projects/{project_id}/agent/run",
        json={
            "task_type": "literature_review",
            "user_input": "Create a literature review for battery thermal management.",
        },
    )
    assert agent_response.status_code == 200
    agent_payload = agent_response.json()
    assert agent_payload["result_json"]["external_references"]
    assert any(
        "metadata only" in warning.lower()
        for warning in agent_payload["result_json"]["warnings"]
    )

    writing_response = client.post(
        f"/api/projects/{project_id}/writing/run",
        json={
            "task_type": "related_work",
            "topic": "Battery thermal management",
            "requirements": "Use current project evidence and saved external references carefully.",
        },
    )
    assert writing_response.status_code == 201
    writing_payload = writing_response.json()
    assert "External References (Metadata Only)" in writing_payload["content_markdown"]
    assert "External battery survey" in writing_payload["content_markdown"]
