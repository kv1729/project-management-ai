FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json frontend/next.config.ts frontend/tsconfig.json ./
COPY frontend/eslint.config.mjs frontend/postcss.config.mjs ./
COPY frontend/src ./src
COPY frontend/public ./public

RUN npm ci && npm run build

FROM python:3.12-slim

WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock backend/
COPY backend/app backend/app
COPY --from=frontend-builder /app/frontend/out frontend/out
RUN pip install --no-cache-dir uv \
    && cd backend \
    && uv sync --locked --no-dev

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "--directory", "/app/backend", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
