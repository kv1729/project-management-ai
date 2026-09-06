# Backend Development Guide

The backend is a FastAPI application managed with `uv`. The current Part 2 scaffold lives in `app/main.py` and exposes a temporary HTML hello-world page at `/` and a JSON hello-world route at `/api/hello`.

## Commands

Run from `backend/`:

- `uv run uvicorn app.main:app --reload`: start the local development server
- `uv run --group dev pytest --cov=app --cov-report=term-missing`: run tests and enforce the 80% coverage threshold

The backend uses Python 3.12 or newer. Keep provider credentials and future application secrets in the repository-root `.env` file; never commit them or expose them to the browser.

## Conventions

- Keep API routes and application wiring in `app/`.
- Put backend tests in `tests/`.
- Use typed request and response models as API contracts are added.
- Keep database, authentication, and AI behavior scoped to their approved plan parts.