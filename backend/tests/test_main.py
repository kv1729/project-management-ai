from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_root_serves_hello_world_html(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Kanban Studio" in response.text or "Project Management MVP" in response.text


def test_root_serves_exported_frontend_when_available(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index_file = tmp_path / "index.html"
    index_file.write_text("<html><body>Exported Kanban</body></html>")
    monkeypatch.setattr(main, "frontend_dir", tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert response.text == "<html><body>Exported Kanban</body></html>"


def test_root_serves_fallback_when_frontend_export_is_missing(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main, "frontend_dir", tmp_path / "missing-out")

    response = client.get("/")

    assert response.status_code == 200
    assert "The FastAPI server is running" in response.text


def test_hello_api_returns_json_message(client: TestClient) -> None:
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello from the Project Management MVP API"
    }


def test_unknown_route_returns_not_found(client: TestClient) -> None:
    response = client.get("/missing")

    assert response.status_code == 404
