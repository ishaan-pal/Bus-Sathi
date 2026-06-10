from tests.conftest import ADMIN_MOBILE


def test_login(client):
    resp = client.post("/api/v1/auth/login", json={"mobile": "9123456789"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "access_token" in data["tokens"]


def test_login_invalid_mobile(client):
    resp = client.post("/api/v1/auth/login", json={"mobile": "12345"})
    assert resp.status_code == 422


def test_admin_login(client):
    resp = client.post("/api/v1/auth/login", json={"mobile": ADMIN_MOBILE})
    assert resp.status_code == 200
    assert resp.json()["user"]["is_admin"] is True


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_token(client, admin_token):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["mobile"] == ADMIN_MOBILE


def test_verify_aadhaar(client):
    login = client.post("/api/v1/auth/login", json={"mobile": "9123456780"})
    assert login.status_code == 200
    token = login.json()["tokens"]["access_token"]
    resp = client.post(
        "/api/v1/auth/verify-aadhaar",
        json={"aadhaar_number": "912345678901"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["aadhaar_verified"] is True
