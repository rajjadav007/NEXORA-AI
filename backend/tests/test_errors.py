from fastapi.testclient import TestClient
from app.main import app


def test_internal_server_error_response():
    # Inject temporary test route to trigger unhandled exception
    @app.get("/test-error")
    def fail_endpoint():
        raise RuntimeError("Database connection string leaked: postgres://secret_pw@localhost")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-error")

    assert response.status_code == 500
    data = response.json()
    assert data == {"detail": "Internal server error"}
    assert "secret_pw" not in response.text
    assert "Traceback" not in response.text


def test_not_found_error_response():
    client = TestClient(app)
    response = client.get("/non-existent-route-404")
    assert response.status_code == 404
    assert "detail" in response.json()
