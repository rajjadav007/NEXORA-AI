from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "nexora-ai-api",
    }


def test_api_version_prefix():
    # Valid prefix
    valid_res = client.get(f"{settings.API_V1_PREFIX}/health")
    assert valid_res.status_code == 200

    # Non-existent or old v0 path returns 404
    invalid_res = client.get("/api/v0/health")
    assert invalid_res.status_code == 404
