import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from app.main import app

ADMIN_MOBILE = settings.SEED_ADMIN_MOBILE or "9999999999"


@pytest.fixture(autouse=True)
def _reset_redis_client():
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
    resp = client.post("/api/v1/auth/login", json={"mobile": ADMIN_MOBILE})
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


@pytest.fixture
def user_token(client: TestClient) -> str:
    mobile = "9876543210"
    resp = client.post("/api/v1/auth/login", json={"mobile": mobile})
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


@pytest.fixture
def verified_user_token(client: TestClient, user_token: str) -> str:
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    if me.json().get("aadhaar_verified"):
        return user_token
    resp = client.post(
        "/api/v1/auth/verify-aadhaar",
        json={"aadhaar_number": "123456789012"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 200, resp.text
    return user_token
