from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.APP_NAME
    assert data["environment"] == settings.APP_ENV
    assert data["status"] == "online"
    assert data["api_v1"] == settings.API_V1_PREFIX
