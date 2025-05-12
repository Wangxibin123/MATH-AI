#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"       # 进 math-copilot 根
export PATH="$HOME/.local/bin:$HOME/.poetry/bin:$PATH"

# 0) 用 /tmp 的全新 DB
rm -f /tmp/math_copilot_dev.db
export DB_URL="sqlite:////tmp/math_copilot_dev.db"

echo "① install"
poetry install --with dev -q

echo "② alembic upgrade head"
poetry run alembic -c apps/gateway/alembic.ini upgrade head

echo "③ ruff & mypy"
poetry run ruff check .
poetry run mypy apps packages

echo "④ pytest 40 条全跑"
OUT=$(poetry run pytest -q)
echo "$OUT"
echo "$OUT" | grep -qE '^40 passed' || { echo "❌  未通过 40/0/0 检查"; exit 1; }

echo "✅  All green." 