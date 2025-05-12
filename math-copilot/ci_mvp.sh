#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"               # 切到仓库根
export PATH="$HOME/.local/bin:$HOME/.poetry/bin:$PATH"

# -------- 新建 DB --------
rm -f /tmp/math_copilot_dev.db
export DB_URL="sqlite:////tmp/math_copilot_dev.db"

echo "① Install deps"
poetry install --with dev -q

echo "② Alembic upgrade head"
poetry run alembic -c apps/gateway/alembic.ini upgrade head

echo "③ Ruff & MyPy"
poetry run ruff check .
poetry run mypy apps packages

echo "④ Pytest expect 41 passed"
OUT=$(poetry run pytest -q)
echo "$OUT"
echo "$OUT" | grep -qE '^41 passed' \
  || { echo '❌ 预期 41 passed，但结果不同'; exit 1; }

echo "✅  Workflow MVP 绿灯！" 