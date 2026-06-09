from tests.conftest import ADMIN_MOBILE, DEV_OTP


def test_send_otp(client):
    resp = client.post("/api/v1/auth/send-otp", json={"mobile": "9123456789"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    if data.get("dev_mode"):
        assert data.get("dev_otp") == DEV_OTP


def test_verify_otp_invalid(client):
    client.post("/api/v1/auth/send-otp", json={"mobile": "9123456788"})
    resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"mobile": "9123456788", "otp": "000000"},
    )
    assert resp.status_code == 400


def test_admin_login(client):
    client.post("/api/v1/auth/send-otp", json={"mobile": ADMIN_MOBILE})
    resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"mobile": ADMIN_MOBILE, "otp": DEV_OTP},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["is_admin"] is True


def test_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client, admin_token):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["mobile"] == ADMIN_MOBILE
