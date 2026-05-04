from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import verify_password
from app.db.session import get_session_factory
from app.models.user import User


def register_user(client: TestClient, *, name: str, email: str, password: str):
    return client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )


def login_user(client: TestClient, *, email: str, password: str):
    return client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_registration_hashes_password(client: TestClient) -> None:
    response = register_user(client, name="Alice", email="alice@example.com", password="secret123")
    assert response.status_code == 201

    with get_session_factory()() as session:
        user = session.scalar(select(User).where(User.email == "alice@example.com"))
        assert user is not None
        assert user.password_hash != "secret123"
        assert verify_password("secret123", user.password_hash)


def test_login_sets_cookie_and_me_works(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")

    response = login_user(client, email="alice@example.com", password="secret123")
    assert response.status_code == 200
    assert "set-cookie" in response.headers
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "alice@example.com"


def test_logout_clears_cookie(client: TestClient) -> None:
    register_user(client, name="Alice", email="alice@example.com", password="secret123")
    login_user(client, email="alice@example.com", password="secret123")

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401


def test_project_routes_require_auth(client: TestClient) -> None:
    response = client.get("/api/projects")
    assert response.status_code == 401


def test_owner_scoped_project_access(app) -> None:
    with TestClient(app) as alice_client, TestClient(app) as bob_client:
        register_user(alice_client, name="Alice", email="alice@example.com", password="secret123")
        login_user(alice_client, email="alice@example.com", password="secret123")

        create_response = alice_client.post(
            "/api/projects",
            json={"name": "Battery aging", "description": "Owner project"},
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        list_response = alice_client.get("/api/projects")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        detail_response = alice_client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()
        assert "knowledge_base" in detail_payload
        assert detail_payload["knowledge_base"]["can_chat"] is False

        register_user(bob_client, name="Bob", email="bob@example.com", password="secret123")
        login_user(bob_client, email="bob@example.com", password="secret123")

        bob_list_response = bob_client.get("/api/projects")
        assert bob_list_response.status_code == 200
        assert bob_list_response.json() == []

        cross_user_detail = bob_client.get(f"/api/projects/{project_id}")
        assert cross_user_detail.status_code == 404

        cross_user_delete = bob_client.delete(f"/api/projects/{project_id}")
        assert cross_user_delete.status_code == 404

        owner_delete = alice_client.delete(f"/api/projects/{project_id}")
        assert owner_delete.status_code == 200

        missing_detail = alice_client.get(f"/api/projects/{project_id}")
        assert missing_detail.status_code == 404
