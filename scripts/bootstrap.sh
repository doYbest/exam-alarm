#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for required in docker uv; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "缺少 $required" >&2
    exit 1
  fi
done
if [[ ! -f "$repo_dir/backend/.env" ]]; then
  cp "$repo_dir/backend/.env.example" "$repo_dir/backend/.env"
fi
cd "$repo_dir"
docker compose up -d db
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run python -m app.cli.seed_demo
echo "启动 API: cd backend && uv run uvicorn app.main:app --reload"

