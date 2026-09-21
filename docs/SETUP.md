# Local Setup

## Prerequisites

- Docker Desktop with the Linux container engine running
- Docker Compose v2, included with current Docker Desktop releases
- `uv` and Python 3.12 or newer for running backend tests without Docker

The application does not require OpenRouter configuration to start. A root `.env` file is optional and is passed to the container when present.

For Part 8, set `OPENROUTER_API_KEY` in the root `.env` file. The model defaults to `openai/gpt-oss-120b`; `OPENROUTER_MODEL` may override it for local testing. Never send either value to the frontend or commit the `.env` file.

## Python Environment

The backend environment is isolated at `backend/.venv`. From the repository root, activate it in PowerShell before running Python commands:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

From `backend/`, activation can be verified with `python -c "import sys; print(sys.executable)"`. It should point to `backend/.venv`, not the system Python installation. On Windows Command Prompt, use `backend\\.venv\\Scripts\\activate.bat`.

## Start and Stop

From the repository root, use the script for your platform:

- Windows PowerShell: `./scripts/start.ps1` and `./scripts/stop.ps1`
- Windows Command Prompt: `scripts\\start.cmd` and `scripts\\stop.cmd`
- macOS/Linux: `./scripts/start.sh` and `./scripts/stop.sh`

The service is available at `http://localhost:8000`.

## Part 2 Endpoints

- `GET /` serves the statically exported Kanban frontend from the Docker container. When running the backend without a frontend export, it returns the temporary hello-world fallback page.
- `GET /api/hello` returns the JSON hello-world response.

The Docker build creates the frontend export in a Node build stage and serves it from the final FastAPI image. The frontend build uses `frontend/package-lock.json` with `npm ci`.

## Sign-In and Sessions

The current MVP sign-in uses the hardcoded credentials `user` / `password`. The backend endpoint `/api/auth/login` returns an in-memory bearer token. The frontend stores the token in browser `localStorage` and sends it to the board API. Tokens are intentionally lost when the backend process restarts; users can sign in again.

## Part 6 Board API

The backend exposes authenticated board routes. A client first posts `{"username":"user","password":"password"}` to `/api/auth/login`, then sends the returned bearer token to `/api/board`. Board updates include the loaded `version`; stale versions return `409`.

The Docker Compose named volume `app-data` stores `/data/project-management.db` across container rebuilds and restarts.

## OpenRouter Connectivity Check

The OpenRouter integration is server-side only and is not called when FastAPI starts or when the browser loads. With `OPENROUTER_API_KEY` configured in the root `.env`, run the opt-in check from the repository root:

```powershell
docker compose run --rm app uv run --no-sync --directory /app/backend python -m app.openrouter_check
```

This sends the prompt `2+2` to OpenRouter and prints the provider response. The command exits with status 1 for missing configuration, timeout, network, provider, or malformed-response errors. Automated tests mock the HTTP request and never require a key or network access.

## AI Board Operations

Authenticated clients can send a question to `POST /api/ai/board` with the bearer token returned by login. The request may include up to 20 prior user/assistant messages. The backend supplies the authenticated user's current board to the provider, validates any complete board replacement, and persists it with version checking. See `docs/AI.md` for the contract and update semantics.

## Frontend Browser Tests

Run the browser suite against the Docker-served app with `BASE_URL=http://localhost:8000`. The suite runs in your installed Google Chrome, so Chrome is a prerequisite and no Playwright browser download is needed. To use another browser, set `BROWSER_CHANNEL` (for example `msedge`, or `chromium` after `npx playwright install chromium`); to use a specific executable, set `PLAYWRIGHT_EXECUTABLE_PATH` to its full path. Set either before running `npm run test:e2e`.

After signing in, the frontend loads the board from `GET /api/board` and saves edits through `PUT /api/board`. Rename, add, delete, and drag-and-drop changes are persisted; refreshing the page restores the saved board.

## Backend Tests

From `backend/`:

```bash
uv run --group dev pytest --cov=app --cov-report=term-missing
```

The test configuration requires at least 80% total coverage. Docker-dependent smoke tests and scripts require Docker Desktop to be running.
