from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_cors_headers_on_request():
    headers = {
        "Origin": settings.FRONTEND_ORIGIN,
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == settings.FRONTEND_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallows_unconfigured_origin():
    headers = {
        "Origin": "http://malicious-site.example.com",
    }
    response = client.get("/", headers=headers)
    assert response.headers.get("access-control-allow-origin") != "http://malicious-site.example.com"


def test_cors_preflight():
    headers = {
        "Origin": settings.FRONTEND_ORIGIN,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    response = client.options("/", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == settings.FRONTEND_ORIGIN
