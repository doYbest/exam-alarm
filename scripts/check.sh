#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv 未安装；请先安装 uv" >&2
  exit 1
fi
cd "$repo_dir/backend"
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest -q
uv run python ../scripts/export_openapi.py --check
cd "$repo_dir/android"
if [[ ! -f gradle/wrapper/gradle-wrapper.jar ]]; then
  echo "缺少 Gradle wrapper jar；Android 构建未验证" >&2
  exit 1
fi
if ! command -v java >/dev/null 2>&1; then
  echo "缺少 JDK；Android 构建未验证" >&2
  exit 1
fi
./gradlew testDebugUnitTest lintDebug assembleDebug
