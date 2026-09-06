from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main, openrouter
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    database_file = tmp_path / "project.db"
    monkeypatch.setattr(main, "database_path", lambda: database_file)
    main.tokens.clear()
    return TestClient(app)


def login(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login", json={"username": "user", "password": "password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_ai_route_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/ai/board", json={"question": "Summarize"})

    assert response.status_code == 401


def test_ai_route_returns_response_and_updated_board(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = login(client)
    board = client.get("/api/board", headers={"Authorization": f"Bearer {token}"}).json()["board"]
    board["columns"][0]["title"] = "Queued"
    monkeypatch.setattr(
        openrouter,
        "complete_messages",
        lambda messages: '{"assistant_response":"Moved it.","board_update":' + __import__("json").dumps(board) + "}",
    )

    response = client.post(
        "/api/ai/board",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Move it", "history": []},
    )

    assert response.status_code == 200
    assert response.json()["assistant_response"] == "Moved it."
    assert response.json()["board_updated"] is True
    assert response.json()["version"] == 2
    assert response.json()["board"]["columns"][0]["title"] == "Queued"


def test_ai_route_maps_provider_and_conflict_errors(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = login(client)
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(
        openrouter,
        "complete_messages",
        lambda messages: (_ for _ in ()).throw(openrouter.OpenRouterError("offline")),
    )

    provider_error = client.post(
        "/api/ai/board", headers=headers, json={"question": "Summarize"}
    )
    assert provider_error.status_code == 502
    assert provider_error.json()["detail"] == "OpenRouter request failed"

    monkeypatch.setattr(
        openrouter,
        "complete_messages",
        lambda messages: '{"assistant_response":"ok","board_update":null}',
    )
    monkeypatch.setattr(main, "answer_board_request", lambda *args: (_ for _ in ()).throw(main.AIBoardConflictError("conflict")))
    conflict = client.post(
        "/api/ai/board", headers=headers, json={"question": "Summarize"}
    )
    assert conflict.status_code == 409