# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Project Management MVP: a Kanban board with drag-and-drop, a fake single-user sign-in, and an AI chat sidebar that can create/edit/move cards. NextJS frontend + Python FastAPI backend, packaged as one Docker container. See `AGENTS.md` for full business requirements and technical decisions, and `docs/PLAN.md` for the phased implementation plan (this project is built in gated parts — check the plan before assuming a feature is in scope).

## Commands

### Backend (run from `backend/`)

```
uv run uvicorn app.main:app --reload                              # dev server
uv run --group dev pytest --cov=app --cov-report=term-missing     # tests, enforces 80% coverage
```

### Frontend (run from `frontend/`)

```
npm run dev              # Next.js dev server
npm run build             # production build (static export to frontend/out)
npm run lint              # ESLint
npm run test:unit         # Vitest once
npm run test:unit:watch   # Vitest watch mode
npm run test:e2e          # Playwright (needs BASE_URL, see below)
npm run test:all          # unit then e2e
```

To run a single Vitest file/test: `npx vitest run path/to/file.test.tsx -t "test name"`.
To run a single pytest test: `uv run --group dev pytest tests/test_file.py::test_name`.

Vitest enforces >=80% statements/branches/functions/lines on production components and board logic; pytest enforces the same via `pyproject.toml` (`fail_under = 80`).

### Docker (run from repo root)

```
docker compose up --build -d
docker compose down
```

Equivalent platform scripts: `scripts/start.ps1` / `scripts/stop.ps1` (Windows PowerShell), `scripts/start.cmd` / `scripts/stop.cmd` (cmd), `scripts/start.sh` / `scripts/stop.sh` (macOS/Linux). These are thin `docker compose` wrappers only — no application logic belongs there.

### Playwright against the Docker container

```
$env:BASE_URL = "http://localhost:8000"
npm run test:e2e
```

Playwright runs in the installed Google Chrome (`channel: "chrome"` in `frontend/playwright.config.ts`); do not run `npx playwright install` — the managed Chromium download hangs during extraction on this machine. `BROWSER_CHANNEL` or `PLAYWRIGHT_EXECUTABLE_PATH` override the browser.

### OpenRouter connectivity check (opt-in, requires a real key in root `.env`)

```
docker compose run --rm app uv run --no-sync --directory /app/backend python -m app.openrouter_check
```

This is the only thing that makes a live OpenRouter call; all other AI tests mock `httpx`/OpenRouter.

## Architecture

**One container, two halves.** The Dockerfile builds the Next.js frontend as a static export (`npm run build` → `frontend/out`), then copies it into a Python 3.12 image alongside the FastAPI backend. `backend/app/main.py` serves the API under `/api/*` and mounts `frontend/out` as static files at `/` (falling back to an inline HTML stub if `frontend/out` doesn't exist, e.g. in local backend-only dev). There is no separate frontend server in production — the frontend always talks to the backend same-origin.

**Auth is intentionally minimal.** One hardcoded demo user (`user`/`password`, seeded on DB init in `database.py` as `DEMO_USER_ID`/`DEMO_USERNAME`/`DEMO_PASSWORD`) but the schema supports multiple users for the future. Login issues an opaque bearer token held in an in-memory dict (`tokens` in `main.py` — not persisted, resets on restart). All authenticated routes resolve `user_id` from that token via `current_user()`; ownership is always derived from the token, never from a client-supplied user id.

**Board persistence uses optimistic concurrency.** Each user has exactly one board row (`boards.user_id UNIQUE`) storing the whole board as JSON (`board_json`) plus a `version` integer. Every write (`PUT /api/board`) must supply the `version` it read; `update_board()` does a single `UPDATE ... WHERE user_id = ? AND version = ?` and returns `None` (→ 409 Conflict) if no row matched. There are no per-card/per-column API operations — the frontend sends the full board document each time. See `docs/DATABASE.md` for the schema rationale.

**Board data is validated end-to-end by one Pydantic shape.** `BoardData` (`backend/app/schemas.py`) enforces: columns have unique ids, every card id appears in exactly one column's `cardIds`, and the `cards` map's keys/values are consistent. This same `BoardData` model is used for API request/response bodies AND to validate AI-generated board updates before they're persisted — invalid AI output is rejected rather than partially applied.

**AI flow (`backend/app/ai.py` + `backend/app/openrouter.py`):** `POST /api/ai/board` loads the user's current board, builds a message list (system prompt + trimmed history + current board JSON + user question), and calls OpenRouter (`openai/gpt-oss-120b` by default, overridable via `OPENROUTER_MODEL`). The model must return strict JSON matching `AIOutput` (`assistant_response` + optional `board_update`, `extra="forbid"`). If `board_update` is present, it's validated as a full `BoardData` and persisted through the same optimistic-concurrency `update_board()` path as manual edits — a stale board raises `AIBoardConflictError` → 409. The OpenRouter key lives only in the backend process (root `.env`, read via `os.getenv`); it must never reach the browser, logs, or committed files. See `docs/AI.md` for the prompt/schema contract.

**Frontend state flows one way: server is truth.** `AuthGate.tsx` owns session/token state and initial board load; `KanbanBoard.tsx` owns in-memory board state, drag handling (`@dnd-kit`), and edit callbacks; `src/lib/kanban.ts` holds pure board types and movement logic (kept separate from components so it's independently unit-testable); `src/lib/api.ts` is the single typed client for `/api/*`. Every edit (rename, add, delete, drag-drop, AI update) round-trips through the backend and reconciles local state to the server's returned `board`/`version` rather than trusting the optimistic local mutation as final.

## Conventions

- Use latest/idiomatic library versions; keep it simple — no speculative abstraction, no unrequested features, no unnecessary defensive code (see `AGENTS.md` coding standards).
- No emojis anywhere, including in docs.
- Root-cause debugging only: reproduce and prove the cause before fixing, don't guess-and-check.
- Frontend: import via `@/*` alias for `src/*`; keep board rules in `src/lib/kanban.ts`, not duplicated in components; keep board updates immutable.
- Backend: keep API routes/wiring in `app/`, tests in `tests/`; use typed Pydantic request/response models.
- Never commit `.env` or database files. `.env.example` documents required keys with empty values only.
- Work matches the current approved part of `docs/PLAN.md` — don't add functionality from a later, unapproved part (e.g. multi-board support, real multi-user auth).
