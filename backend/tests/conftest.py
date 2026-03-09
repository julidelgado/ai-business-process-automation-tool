import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.session import engine
from app.main import app
from app.models.entities import Base


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": get_settings().api_key, "X-Actor": "pytest"}
