from pathlib import Path

import pytest

from app import ai, database
from app.schemas import AIRequest, BoardData


def make_request() -> AIRequest:
    return AIRequest(
        question="Move the analytics card to In Progress",
        history=[
            {"role": "user", "content": "What is on the board?"},
            {"role": "assistant", "content": "There are eight cards."},
        ],
    )


def test_build_messages_contains_board_question_and_history(
    tmp_path: Path,
) -> None:
    database_file = tmp_path / "project.db"
    database.initialize(database_file)
    current = database.read_board(database_file, database.DEMO_USER_ID)
    assert current is not None

    messages = ai.build_messages(
        make_request(), BoardData.model_validate(current["board"])
    )

    assert messages[0]["role"] == "system"
    assert "assistant_response" in messages[0]["content"]
    assert messages[1:3] == [
        {"role": "user", "content": "What is on the board?"},
        {"role": "assistant", "content": "There are eight cards."},
    ]
    assert "Current board JSON:" in messages[-1]["content"]
    assert "Move the analytics card to In Progress" in messages[-1]["content"]


def test_parse_output_rejects_malformed_or_partial_board() -> None:
    with pytest.raises(ai.AIError, match="structured output"):
        ai.parse_output("not json")

    with pytest.raises(ai.AIError, match="structured output"):
        ai.parse_output('{"assistant_response":"ok","unknown":true}')

    with pytest.raises(ai.AIError, match="structured output"):
        ai.parse_output(
            '{"assistant_response":"ok","board_update":{"columns":[]}}'
        )


def test_response_only_does_not_change_board(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_file = tmp_path / "project.db"
    database.initialize(database_file)
    monkeypatch.setattr(
        ai.openrouter,
        "complete_messages",
        lambda messages: '{"assistant_response":"No changes needed.","board_update":null}',
    )

    result = ai.answer_board_request(
        database.DEMO_USER_ID, make_request(), database_file
    )

    assert result.assistant_response == "No changes needed."
    assert result.board_updated is False
    assert result.version == 1
    assert database.read_board(database_file, database.DEMO_USER_ID)["version"] == 1


def test_valid_board_update_persists_and_increments_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_file = tmp_path / "project.db"
    database.initialize(database_file)
    current = database.read_board(database_file, database.DEMO_USER_ID)
    assert current is not None
    updated_board = BoardData.model_validate(current["board"])
    updated_board.columns[0].title = "Queued"
    response = {
        "assistant_response": "Renamed the first column.",
        "board_update": updated_board.model_dump(),
    }
    monkeypatch.setattr(ai.openrouter, "complete_messages", lambda messages: __import__("json").dumps(response))

    result = ai.answer_board_request(
        database.DEMO_USER_ID, make_request(), database_file
    )

    assert result.board_updated is True
    assert result.version == 2
    assert result.board.columns[0].title == "Queued"


def test_provider_and_conflict_fail_without_persisting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_file = tmp_path / "project.db"
    database.initialize(database_file)
    monkeypatch.setattr(
        ai.openrouter,
        "complete_messages",
        lambda messages: (_ for _ in ()).throw(ai.openrouter.OpenRouterError("offline")),
    )

    with pytest.raises(ai.AIError, match="request failed"):
        ai.answer_board_request(database.DEMO_USER_ID, make_request(), database_file)

    current = database.read_board(database_file, database.DEMO_USER_ID)
    assert current is not None
    board_update = BoardData.model_validate(current["board"]).model_dump_json()
    monkeypatch.setattr(
        ai.openrouter,
        "complete_messages",
        lambda messages: '{"assistant_response":"change","board_update":'
        + board_update
        + "}",
    )
    monkeypatch.setattr(ai, "update_board", lambda *args: None)

    with pytest.raises(ai.AIBoardConflictError, match="changed"):
        ai.answer_board_request(database.DEMO_USER_ID, make_request(), database_file)
    assert database.read_board(database_file, database.DEMO_USER_ID)["version"] == current["version"]