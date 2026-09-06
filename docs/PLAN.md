# Project Management MVP Plan

## Working Rules

- Work on one part at a time and keep changes limited to that part.
- Check off implementation items only after the relevant tests and success criteria pass.
- Ask for user approval at the explicit gates below before starting the next gated part.
- Keep the MVP simple: one hardcoded sign-in, one board per user, local SQLite, and no unrequested features.
- Never send the OpenRouter key to the browser or commit `.env` files or database files containing local data.
- For every tested code area, maintain at least 80% statements, branches, functions, and lines coverage. Add focused tests for error paths and important state transitions rather than relying only on end-to-end tests.

## Reproducible Setup and Verification

### Runtime and Dependencies

- The application runs in a Docker container. The Docker image builds the static Next.js frontend with Node.js, then serves it from the FastAPI application in a Python 3.12 runtime image.
- Docker Desktop must be installed with its Linux container engine running. Docker Compose v2 is required.
- Docker Compose uses the repository-root `.env` when it exists and stores the SQLite database in the `app-data` named volume at `/data/project-management.db`.
- Backend tests may run without Docker in the local `backend/.venv` environment. This environment is for the backend only and must not be committed.
- From the repository root, create or synchronize that environment with `uv sync --directory backend --group dev`. Activate it in PowerShell with `./backend/.venv/Scripts/Activate.ps1`, or run commands without activation through `uv run --directory backend`.
- Python dependencies are declared in `backend/pyproject.toml`. `backend/uv.lock` records the resolved versions for reproducible installs. Docker installs the locked runtime set with `uv sync --locked --no-dev`; local backend tests use the development dependency group.
- Frontend dependencies are declared in `frontend/package.json` and reproduced from `frontend/package-lock.json` with `npm ci`.

### Environment and OpenRouter

- For local OpenRouter use, set `OPENROUTER_API_KEY` in the repository-root `.env`. The key must never be hardcoded, committed, logged, returned, sent to the frontend, or otherwise exposed outside the server.
- `.env` is ignored by Git. `.env.example` may contain the empty documentation placeholder `OPENROUTER_API_KEY=` but must never contain a real key.
- The selected default model is `openai/gpt-oss-120b`. Its configuration lives in `backend/app/openrouter.py`; the server-side `OPENROUTER_MODEL` environment variable may override the default.
- Automated OpenRouter tests mock `httpx` and do not require a key or network access. The real `2+2` connectivity check is separate, opt-in, and runs only when explicitly invoked with a configured key:

```powershell
docker compose run --rm app uv run --no-sync --directory /app/backend python -m app.openrouter_check
```

### Reproduction Commands

From the repository root:

```powershell
docker compose up --build -d
docker compose down
```

Start and stop scripts provide the same workflow by platform:

- Windows PowerShell: `./scripts/start.ps1` and `./scripts/stop.ps1`
- Windows Command Prompt: `scripts\start.cmd` and `scripts\stop.cmd`
- macOS/Linux: `./scripts/start.sh` and `./scripts/stop.sh`

Run backend tests from `backend/`:

```powershell
uv run --group dev pytest --cov=app --cov-report=term-missing
```

Run frontend checks from `frontend/`:

```powershell
npm ci
npm run lint
npm run build
npx vitest run --coverage
```

Run Playwright against the Docker-served application after starting it:

```powershell
$env:BASE_URL = "http://localhost:8000"
npm run test:e2e
```

Playwright requires a compatible Chromium runtime. If its managed Chromium installation is incomplete or corrupted, close Chrome and Playwright processes, remove the incomplete version under `$env:LOCALAPPDATA\ms-playwright`, and reinstall with `npx playwright install chromium` and, when requested by the installed Playwright version, `npx playwright install chromium-headless-shell`. If extraction remains incomplete but a local Chromium executable is available, set `PLAYWRIGHT_EXECUTABLE_PATH` to its full path before running the suite. This path is an environment-specific recovery option and is not part of the application runtime.

### Platform Limitations

- Docker-dependent commands require Docker Desktop and its Linux engine.
- Windows PowerShell commands were verified in this environment. macOS/Linux scripts are documented but were not executable here.
- The real OpenRouter connectivity check requires a configured key and network access; ordinary automated tests remain offline and mocked.

## Part 1: Plan and Frontend Guide

### Checklist

- [x] Review the repository requirements and the existing frontend.
- [x] Expand this plan with implementation checklists, tests, and success criteria.
- [x] Create `frontend/AGENTS.md` describing the current frontend structure, commands, conventions, and testing expectations.
- [x] Get user approval for this plan before starting Part 2.

### Tests and verification

- [x] Confirm the documented frontend commands match `frontend/package.json`.
- [x] Confirm the documented component and test inventory matches the repository.
- [x] Run no product implementation work during this part.

### Success criteria

- [x] The plan is specific enough to implement one part at a time.
- [x] The frontend guide accurately describes the current demo.
- [x] The user has reviewed and approved the plan.

## Part 2: Docker and FastAPI Scaffolding

### Checklist

- [x] Define the container layout, Python version, and `uv` workflow.
- [x] Add the FastAPI application with a health or hello-world route.
- [x] Add a minimal static HTML response served by the backend at `/`.
- [x] Add Docker configuration for installing dependencies and starting the server.
- [x] Add start and stop scripts for Windows, macOS, and Linux using the agreed Docker workflow.
- [x] Document required environment variables and local prerequisites in `docs/SETUP.md`.

### Tests

- [x] Add backend tests for the hello-world/API route.
- [x] Add a smoke test that builds and starts the container, requests `/`, and calls the API route.
- [x] Test the start and stop scripts on the available host platform, documenting unavailable platforms. Windows PowerShell scripts passed; macOS/Linux scripts were not executable in this environment.
- [x] Enforce the 80% coverage target for backend code.

### Success criteria

- [x] A clean checkout can build and start the container locally.
- [x] `/` serves the example HTML and the API responds successfully from the container.
- [x] The container stops cleanly and does not require a manually created database or directory.

## Part 3: Serve the Existing Frontend

### Checklist

- [x] Configure Next.js for a static export compatible with FastAPI static serving.
- [x] Build the frontend as part of the container build.
- [x] Copy the generated static assets into the backend's serving location.
- [x] Serve the Kanban demo at `/` through FastAPI.
- [x] Preserve client-side drag-and-drop, column rename, add-card, and delete-card behavior.
- [x] Add a backend-only fallback when the static export is absent.

### Tests

- [x] Keep focused Vitest tests for pure Kanban logic and component workflows.
- [x] Expand component tests for blank titles, cancellation, and drag-preview behavior.
- [x] Run Playwright against the built/static application, not only the Next.js dev server.
- [x] Verify the full frontend unit test run meets the 80% coverage target for statements, branches, functions, and lines.
- [x] Run lint, type checking/build, unit tests, and browser tests.

### Success criteria

- [x] A production container serves the real Kanban demo at `/`.
- [x] Static assets load during the browser test suite.
- [x] Existing user-visible board workflows continue to work through the container.

## Part 4: Fake User Sign-In

### Checklist

- [x] Add a sign-in screen shown before the board.
- [x] Accept only the MVP credentials `user` and `password`.
- [x] Store the minimal client session state needed for the local MVP in browser `localStorage`.
- [x] Protect the board view and provide a logout action.
- [x] Show clear validation for invalid credentials without exposing the expected password.
- [x] Keep the design and accessibility consistent with the existing frontend.

### Tests

- [x] Unit-test credential validation and session state transitions.
- [x] Component-test initial signed-out state, invalid credentials, successful sign-in, and logout.
- [x] Add Playwright coverage for the complete sign-in and logout workflow, including refresh behavior.
- [x] Confirm the Part 4 static frontend protects the board view. Backend authentication is deferred to the API work in Part 6.
- [x] Maintain the 80% coverage target for changed frontend code.

### Success criteria

- [x] Users cannot see the board before signing in.
- [x] `user`/`password` reveals the board and invalid credentials do not.
- [x] Logout reliably returns to sign-in and clears the MVP session.

## Part 5: Database Model Proposal

### Checklist

- [x] Propose how SQLite stores users, boards, and serialized board JSON in `docs/DATABASE.md`.
- [x] Define identifiers, ownership, ordering, timestamps, and update semantics.
- [x] Define the JSON shape and validation rules for a board.
- [x] Document initialization, migrations/schema creation, and local database file placement.
- [x] Document concurrency and transaction expectations for the local MVP.
- [x] Save the proposal in `docs/DATABASE.md`.
- [x] Obtain explicit user sign-off before implementation; user approved proceeding to Part 6.

### Tests and verification

- [x] Review the schema against all board operations and the one-board-per-user limitation.
- [x] Document representative board JSON and invalid payload examples.
- [x] Do not implement database changes until the proposal is approved.

### Success criteria

- [x] The schema can represent every current and planned board operation without ambiguous ordering.
- [x] The JSON contract and persistence approach are documented.
- [x] The user has approved the database design.

## Part 6: Backend Board API

### Checklist

- [x] Create the SQLite database automatically when it does not exist.
- [x] Add backend models and validation for users, boards, columns, cards, and board JSON.
- [x] Add authenticated routes to read the signed-in user's board.
- [x] Add an authenticated route to replace board state with version checking; individual UI operations remain represented by the validated document until Part 7.
- [x] Enforce ownership through the authenticated user token rather than a browser-supplied user ID.
- [x] Return consistent authentication, validation, and conflict errors.
- [x] Keep writes transactional and preserve valid board ordering.

### Tests

- [x] Test database creation and initialization from an empty temporary path.
- [x] Test route success, validation, authentication, and conflict behavior.
- [x] Test persistence across application restart or a fresh database connection.
- [x] Test malformed and structurally invalid board JSON.
- [x] Maintain at least 80% backend coverage across statements, branches, functions, and lines.

### Success criteria

- [x] API clients can persist and retrieve the signed-in user's board.
- [x] Unauthorized access is rejected and ownership is derived from the authenticated token.
- [x] A missing database is created automatically and all API tests pass.

## Part 7: Connect Frontend and Backend

### Checklist

- [x] Add a small typed frontend API client for authentication and board operations.
- [x] Load the persisted board after sign-in and show loading/error states.
- [x] Send rename, add, delete, and drag-and-drop changes to the backend.
- [x] Reconcile successful responses and versions so the UI reflects canonical server state.
- [x] Handle failed requests with visible errors and serialized saves.
- [x] Keep API configuration same-origin and compatible with local Docker serving.

### Tests

- [x] Unit-test request/response parsing and API error handling with mocked fetches.
- [x] Component-test authenticated loading and API-backed board rendering.
- [x] Add integration coverage through the Docker-backed API for persistence workflows.
- [x] Add Playwright coverage for sign-in, reload persistence, edits, and existing board workflows.
- [x] Maintain the 80% coverage target for changed frontend and backend code.

### Success criteria

- [x] The board survives a page reload and container restart when the database remains available.
- [x] All board edits use the backend as the source of truth.
- [x] User-facing failures are visible and do not corrupt board state.

## Part 8: OpenRouter Connectivity

### Checklist

- [x] Add backend configuration for `OPENROUTER_API_KEY` and the `openai/gpt-oss-120b` model.
- [x] Keep the key server-side and fail clearly when configuration is missing.
- [x] Add a small backend service for an OpenRouter request.
- [x] Add a controlled connectivity check using the prompt `2+2`.
- [x] Set request timeouts and handle provider/network errors.
- [x] Document how to run the connectivity check without exposing the key.

### Tests

- [x] Unit-test request construction with the provider client mocked.
- [x] Test missing configuration, provider errors, malformed responses, and successful parsing.
- [x] Keep the real `2+2` check opt-in and excluded from ordinary automated test runs.
- [x] Maintain at least 80% coverage for the AI service and changed backend code.

### Success criteria

- A configured local environment can complete the `2+2` connectivity check.
- Automated tests never require a live OpenRouter key or network access.
- Provider failures return actionable, non-secret error information.

## Part 9: Structured AI Board Operations

### Checklist

- [x] Define the conversation message contract and history limits.
- [x] Send the current user's board JSON, user question, and conversation history on every AI request.
- [x] Define a strict structured output schema containing the assistant response and an optional board update.
- [x] Validate structured output before applying any board update.
- [x] Apply updates only to the authenticated user's board and persist them transactionally.
- [x] Reject or safely report invalid, partial, or provider-generated board mutations.
- [x] Document the prompt, schema, and update semantics.

### Tests

- [x] Test payload construction including board JSON and conversation history.
- [x] Test valid response-only and valid response-plus-update outputs.
- [x] Test schema violations, malformed JSON, provider refusal/errors, and unauthorized updates.
- [x] Test that board updates are atomic and do not partially persist.
- [x] Maintain at least 80% coverage for the AI orchestration and board mutation paths.

### Success criteria

- Every AI request has the required board and conversation context.
- Only schema-valid updates can change the board.
- The API returns a stable assistant response and an explicit update result.

## Part 10: AI Chat Sidebar

### Checklist

- [x] Add an accessible, responsive sidebar chat widget to the authenticated board view.
- [x] Render user and assistant messages with loading, error, and empty states.
- [x] Send questions and conversation history through the backend AI route.
- [x] Refresh or reconcile the board when the backend returns an update.
- [x] Prevent duplicate submissions while a request is pending.
- [x] Preserve the existing board workflow on desktop and mobile.
- [x] Keep all provider credentials and prompt logic out of the browser.

### Tests

- [x] Component-test message rendering, submit behavior, loading state, errors, and returned board updates.
- [x] Test keyboard and accessible-name workflows for the chat controls.
- [x] Add Playwright coverage for asking a question, receiving a response, and seeing an AI board update.
- [x] Mock AI responses in automated tests; keep live provider checks opt-in.
- [x] Maintain the 80% coverage target across changed frontend and backend code.

### Success criteria

- [x] Authenticated users can use the sidebar to ask questions and see assistant responses.
- [x] AI-generated board changes appear in the UI without a manual reload.
- [x] The chat is usable on supported desktop and mobile viewports and does not expose secrets.

## Final MVP Gate

- [ ] Run the complete documented unit, integration, browser, lint, build, and coverage checks.
- [ ] Verify the container starts from a clean environment with only documented configuration.
- [ ] Verify the database and API preserve board state across restart.
- [ ] Verify sign-in, board editing, AI chat, and AI-driven updates end to end.
- [ ] Record any known limitations in the README or `docs/`.

The reproducible setup and verification procedures above are prerequisites for this gate. The known limitations to carry into the gate are the platform-specific script coverage and the opt-in nature of the real OpenRouter check.