#!/usr/bin/env bash
set -euo pipefail

docker compose up --build -d
printf 'Project Management MVP is running at http://localhost:8000\n'
