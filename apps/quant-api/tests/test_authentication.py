from fastapi.testclient import TestClient


def register(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": "http://localhost:3000"},
        json={"name": "Quant User", "email": "user@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["user"]["id"] == 1


def login(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:3000"},
        json={"email": "user@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_authentication_lifecycle_with_numeric_user_id(client: TestClient) -> None:
    register(client)
    payload = login(client)
    assert isinstance(payload["user"]["id"], int)
    assert payload["access_token"]

    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "user@example.com"


def test_refresh_rotation_detects_reuse_and_revokes_session(client: TestClient) -> None:
    register(client)
    login(client)
    original_token = client.cookies.get("quantlens_refresh")
    assert original_token

    refreshed = client.post("/api/v1/auth/refresh", headers={"Origin": "http://localhost:3000"})
    assert refreshed.status_code == 200

    attacker = TestClient(client.app)
    attacker.cookies.set("quantlens_refresh", original_token, path="/api/v1/auth")
    reuse = attacker.post("/api/v1/auth/refresh", headers={"Origin": "http://localhost:3000"})
    assert reuse.status_code == 401
    assert reuse.json()["code"] == "REFRESH_TOKEN_REUSED"

    revoked = client.post("/api/v1/auth/refresh", headers={"Origin": "http://localhost:3000"})
    assert revoked.status_code == 401
    assert revoked.json()["code"] == "SESSION_REVOKED"


def test_authentication_mutations_reject_untrusted_origins(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": "https://untrusted.example"},
        json={"name": "Quant User", "email": "user@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
