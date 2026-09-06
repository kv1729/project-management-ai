import json
from typing import Any

from app import openrouter
from app.database import read_board, update_board
from app.schemas import AIOutput, AIRequest, AIResponse, BoardData


MAX_HISTORY_MESSAGES = 20


class AIError(RuntimeError):
    """Raised when an AI request cannot be completed safely."""


class AIBoardNotFoundError(AIError):
    pass


class AIBoardConflictError(AIError):
    pass


SYSTEM_PROMPT = """You manage a project board. Return JSON only with exactly these fields:
assistant_response: a concise helpful response string
board_update: null or a complete board object with columns and cards

Never return markdown, partial board updates, unknown fields, or operation lists.
Only change the board when the user requests a board change. Preserve all existing
cards and columns unless the request requires a valid complete board replacement."""


def build_messages(request: AIRequest, board: BoardData) -> list[dict[str, str]]:
    context = (
        "Current board JSON:\n"
        + board.model_dump_json()
        + "\n\nUser question:\n"
        + request.question
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(message.model_dump() for message in request.history)
    messages.append({"role": "user", "content": context})
    return messages


def parse_output(content: str) -> AIOutput:
    try:
        return AIOutput.model_validate_json(content)
    except ValueError as error:
        raise AIError("OpenRouter returned invalid structured output") from error


def answer_board_request(
    user_id: str, request: AIRequest, database_file: Any
) -> AIResponse:
    current = read_board(database_file, user_id)
    if current is None:
        raise AIBoardNotFoundError("Board not found")

    board = BoardData.model_validate(current["board"])
    try:
        content = openrouter.complete_messages(build_messages(request, board))
    except openrouter.OpenRouterError as error:
        raise AIError("OpenRouter request failed") from error

    output = parse_output(content)
    if output.board_update is None:
        return AIResponse(
            assistant_response=output.assistant_response,
            board_updated=False,
            board=board,
            version=current["version"],
            updated_at=current["updated_at"],
        )

    updated = update_board(database_file, user_id, output.board_update, current["version"])
    if updated is None:
        raise AIBoardConflictError("Board changed while the AI was responding")
    return AIResponse(
        assistant_response=output.assistant_response,
        board_updated=True,
        board=BoardData.model_validate(updated["board"]),
        version=updated["version"],
        updated_at=updated["updated_at"],
    )