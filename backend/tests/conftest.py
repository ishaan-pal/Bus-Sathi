import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from app.main import app

ADMIN_MOBILE = settings.SEED_ADMIN_MOBILE or "9999999999"
DEV_OTP = settings.OTP_DEV_FIXED or "123456"


@pytest.fixture(autouse=True)
def _reset_redis_client():
    """Avoid stale async Redis clients across tests."""
    import app.core.dependencies as deps
    deps._redis_client = None
    yield
    deps._redis_client = None


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client: TestClient) -> str:
    client.post("/api/v1/auth/send-otp", json={"mobile": ADMIN_MOBILE})
    resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"mobile": ADMIN_MOBILE, "otp": DEV_OTP},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


@pytest.fixture
def user_token(client: TestClient) -> str:
    mobile = "9876543210"
    client.post("/api/v1/auth/send-otp", json={"mobile": mobile})
    resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"mobile": mobile, "otp": DEV_OTP},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    token = data["tokens"]["access_token"]
    if not data["user"]["profile_complete"]:
        profile = client.post(
            "/api/v1/auth/complete-profile",
            json={"name": "Test User", "date_of_birth": "1995-06-15"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile.status_code == 200, profile.text
    return token
