from pathlib import Path
import secrets

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.ai import AIBoardConflictError, AIBoardNotFoundError, AIError, answer_board_request
from app.database import authenticate, database_path, initialize, read_board, update_board
from app.schemas import AIRequest, AIResponse, BoardResponse, BoardUpdateRequest, LoginRequest, LoginResponse

app = FastAPI(title="Project Management MVP API")
frontend_dir = Path(__file__).resolve().parents[2] / "frontend" / "out"
tokens: dict[str, str] = {}


@app.get("/", response_class=HTMLResponse, response_model=None)
def read_root() -> HTMLResponse | FileResponse:
  index_file = frontend_dir / "index.html"
  if index_file.exists():
    return FileResponse(index_file)

  return HTMLResponse(
    """<!doctype html
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Project Management MVP</title>
  </head>
  <body>
    <main>
      <h1>Project Management MVP</h1>
      <p>The FastAPI server is running.</p>
    </main>
  </body>
</html>"""
  )


@app.get("/api/hello")
def read_hello() -> dict[str, str]:
    return {"message": "Hello from the Project Management MVP API"}


def current_user(authorization: str | None) -> str:
  if not authorization or not authorization.lower().startswith("bearer "):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
  user_id = tokens.get(authorization[7:].strip())
  if user_id is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
  return user_id


@app.post("/api/auth/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
  path = database_path()
  initialize(path)
  user_id = authenticate(path, request.username, request.password)
  if user_id is None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
  token = secrets.token_urlsafe(32)
  tokens[token] = user_id
  return LoginResponse(access_token=token)


@app.get("/api/board", response_model=BoardResponse)
def get_board(authorization: str | None = Header(default=None)) -> BoardResponse:
  user_id = current_user(authorization)
  path = database_path()
  initialize(path)
  result = read_board(path, user_id)
  if result is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
  return BoardResponse(**result)


@app.put("/api/board", response_model=BoardResponse)
def save_board(
  request: BoardUpdateRequest,
  authorization: str | None = Header(default=None),
) -> BoardResponse:
  user_id = current_user(authorization)
  path = database_path()
  initialize(path)
  result = update_board(path, user_id, request.board, request.version)
  if result is None:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Board version is stale or board does not exist",
    )
  return BoardResponse(**result)


@app.post("/api/ai/board", response_model=AIResponse)
def ask_board_ai(
  request: AIRequest,
  authorization: str | None = Header(default=None),
) -> AIResponse:
  user_id = current_user(authorization)
  path = database_path()
  initialize(path)
  try:
    return answer_board_request(user_id, request, path)
  except AIBoardNotFoundError as error:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
  except AIBoardConflictError as error:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
  except AIError as error:
    raise HTTPException(
      status_code=status.HTTP_502_BAD_GATEWAY,
      detail=str(error),
    ) from error


if frontend_dir.exists():
  app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
