import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import database, main
from app.main import app
from app.schemas import BoardData


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    database_file = tmp_path / "nested" / "project.db"
    monkeypatch.setattr(main, "database_path", lambda: database_file)
    main.tokens.clear()
    return TestClient(app)


def login(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login", json={"username": "user", "password": "password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_database_is_created_and_seeded(client: TestClient, tmp_path: Path) -> None:
    token = login(client)
    response = client.get("/api/board", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json()["name"] == "Kanban Studio"
    assert response.json()["version"] == 1
    assert len(response.json()["board"]["columns"]) == 5
    database_file = next(tmp_path.glob("**/project.db"))
    assert database_file.exists()


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"username": "user", "password": "wrong"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_board_requires_valid_bearer_token(client: TestClient) -> None:
    missing = client.get("/api/board")
    invalid = client.get("/api/board", headers=auth_header("invalid"))

    assert missing.status_code == 401
    assert invalid.status_code == 401


def test_board_update_persists_and_increments_version(client: TestClient) -> None:
    token = login(client)
    headers = auth_header(token)
    original = client.get("/api/board", headers=headers).json()
    original["board"]["columns"][0]["title"] = "Queued"

    updated = client.put(
        "/api/board",
        headers=headers,
        json={"board": original["board"], "version": original["version"]},
    )

    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert updated.json()["board"]["columns"][0]["title"] == "Queued"
    loaded = client.get("/api/board", headers=headers)
    assert loaded.json()["board"]["columns"][0]["title"] == "Queued"


def test_stale_board_update_returns_conflict(client: TestClient) -> None:
    token = login(client)
    headers = auth_header(token)
    board = client.get("/api/board", headers=headers).json()

    first = client.put(
        "/api/board", headers=headers, json={"board": board["board"], "version": 1}
    )
    stale = client.put(
        "/api/board", headers=headers, json={"board": board["board"], "version": 1}
    )

    assert first.status_code == 200
    assert stale.status_code == 409


def test_invalid_board_shape_is_rejected(client: TestClient) -> None:
    token = login(client)
    response = client.put(
        "/api/board",
        headers=auth_header(token),
        json={"board": {"columns": [], "cards": {}}, "version": 1},
    )

    assert response.status_code == 422


def test_board_rejects_unreferenced_cards(client: TestClient) -> None:
    token = login(client)
    board = client.get("/api/board", headers=auth_header(token)).json()
    board["board"]["cards"]["orphan"] = {
        "id": "orphan",
        "title": "Orphan",
        "details": "Not in a column",
    }

    response = client.put(
        "/api/board",
        headers=auth_header(token),
        json={"board": board["board"], "version": 1},
    )

    assert response.status_code == 422


def test_database_helpers_verify_password_and_enable_foreign_keys(tmp_path: Path) -> None:
    path = tmp_path / "db" / "project.db"
    database.initialize(path)

    with closing(database.connect(path)) as connection:
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        row = connection.execute(
            "SELECT password_hash FROM users WHERE username = 'user'"
        ).fetchone()

    assert foreign_keys == 1
    assert database.verify_password("password", row[0])
    assert not database.verify_password("wrong", row[0])
    assert database.authenticate(path, "missing", "password") is None


def test_database_update_returns_none_for_missing_user_or_version(tmp_path: Path) -> None:
    path = tmp_path / "project.db"
    database.initialize(path)
    board = database.read_board(path, database.DEMO_USER_ID)

    assert board is not None
    parsed_board = BoardData.model_validate(board["board"])
    assert database.update_board(path, "missing", parsed_board, 1) is None
    assert database.update_board(path, database.DEMO_USER_ID, parsed_board, 99) is None


def test_database_json_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "project.db"
    database.initialize(path)

    with closing(sqlite3.connect(path)) as connection:
        board_json = connection.execute("SELECT board_json FROM boards").fetchone()[0]

    assert json.loads(board_json)["columns"]
