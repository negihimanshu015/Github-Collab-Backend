import os
import pytest
from fastapi.testclient import TestClient


# Configure environment BEFORE importing the app
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "testsecretkey")
os.environ.setdefault("GEMINI_API_KEY", "dummy-gemini")
os.environ.setdefault("GITHUB_ACCESS_TOKEN", "dummy-github")
os.environ.setdefault("ASSEMBLYAI_API_KEY", "dummy-assemblyai")


from src.main import app  # noqa: E402
from src.db.session import Base, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Fresh DB schema for the test session
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth_token(client):
    email = "user@example.com"
    password = "password123"

    # Register
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "github_username": "octocat",
        },
    )
    if r.status_code == 400 and "already" in r.json().get("detail", "").lower():
        # already exists, login instead
        pass
    elif r.status_code != 200:
        pytest.fail(f"Registration failed: {r.status_code} {r.text}")

    # Login
    lr = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert lr.status_code == 200, lr.text
    token = lr.json()["access_token"]
    return token


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


