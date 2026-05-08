from __future__ import annotations

from fastapi.testclient import TestClient

from src.app import create_app


def test_health_endpoint(test_config) -> None:
    app = create_app(test_config)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_client_init_endpoint(test_config) -> None:
    app = create_app(test_config)
    client = TestClient(app)
    response = client.post(
        "/v1/client/init",
        json={
            "api_key": "sk-test",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
        },
    )
    assert response.status_code == 200
    assert response.json()["client_id"].startswith("cli_")
