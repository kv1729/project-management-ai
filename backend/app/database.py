import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import UTC, datetime
from contextlib import closing
from pathlib import Path
from typing import Any

from app.schemas import BoardData

DEFAULT_DATABASE_PATH = "/data/project-management.db"
DEMO_USER_ID = "user-1"
DEMO_USERNAME = "user"
DEMO_PASSWORD = "password"

INITIAL_BOARD = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {"id": "card-1", "title": "Align roadmap themes", "details": "Draft quarterly themes with impact statements and metrics."},
        "card-2": {"id": "card-2", "title": "Gather customer signals", "details": "Review support tags, sales notes, and churn feedback."},
        "card-3": {"id": "card-3", "title": "Prototype analytics view", "details": "Sketch initial dashboard layout and key drill-downs."},
        "card-4": {"id": "card-4", "title": "Refine status language", "details": "Standardize column labels and tone across the board."},
        "card-5": {"id": "card-5", "title": "Design card layout", "details": "Add hierarchy and spacing for scanning dense lists."},
        "card-6": {"id": "card-6", "title": "QA micro-interactions", "details": "Verify hover, focus, and loading states."},
        "card-7": {"id": "card-7", "title": "Ship marketing page", "details": "Final copy approved and asset pack delivered."},
        "card-8": {"id": "card-8", "title": "Close onboarding sprint", "details": "Document release notes and share internally."},
    },
}


def database_path() -> Path:
    default_path = Path(__file__).resolve().parents[1] / "data" / "project-management.db"
    return Path(os.getenv("DATABASE_PATH", str(default_path)))


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256$120000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    algorithm, rounds, salt_hex, digest_hex = stored_hash.split("$")
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(path: Path) -> None:
    with closing(connect(path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS boards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                board_json TEXT NOT NULL CHECK (json_valid(board_json)),
                version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        now = utc_now()
        connection.execute(
            "INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)",
            (DEMO_USER_ID, DEMO_USERNAME, password_hash(DEMO_PASSWORD), now, now),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO boards
                (id, user_id, name, board_json, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            ("board-1", DEMO_USER_ID, "Kanban Studio", json.dumps(INITIAL_BOARD), now, now),
        )


def authenticate(path: Path, username: str, password: str) -> str | None:
    with closing(connect(path)) as connection:
        row = connection.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return row["id"]


def read_board(path: Path, user_id: str) -> dict[str, Any] | None:
    with closing(connect(path)) as connection:
        row = connection.execute(
            "SELECT name, board_json, version, updated_at FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "name": row["name"],
        "board": json.loads(row["board_json"]),
        "version": row["version"],
        "updated_at": row["updated_at"],
    }


def update_board(
    path: Path, user_id: str, board: BoardData, expected_version: int
) -> dict[str, Any] | None:
    now = utc_now()
    with closing(connect(path)) as connection, connection:
        result = connection.execute(
            """
            UPDATE boards
            SET board_json = ?, version = version + 1, updated_at = ?
            WHERE user_id = ? AND version = ?
            """,
            (board.model_dump_json(), now, user_id, expected_version),
        )
        if result.rowcount != 1:
            return None
        row = connection.execute(
            "SELECT name, board_json, version, updated_at FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return {
        "name": row["name"],
        "board": json.loads(row["board_json"]),
        "version": row["version"],
        "updated_at": row["updated_at"],
    }
