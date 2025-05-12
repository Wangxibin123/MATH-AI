#!/usr/bin/env bash
# 本地 CI —— 全绿才算真通过
set -euo pipefail

echo "1️⃣  安装依赖 (+dev)…"
poetry install --with dev -q

echo "2️⃣  pre-commit 全量检查…"
poetry run pre-commit run --all-files

echo "3️⃣  Ruff Lint…"
poetry run ruff check .

echo "4️⃣  MyPy Type-Check…"
poetry run mypy apps packages

echo "5️⃣  pytest 单元…"
poetry run pytest -q
echo "   ✅  unit & static all pass"

echo "6️⃣  启动 FastAPI（Stub）并自测…"
poetry run uvicorn apps.gateway.main:app --port 8000 --reload --log-level warning &
PID=$!
sleep 3           # 等 Uvicorn 热身
set +e             # curl 出错时继续往下好抓日志
RESP=$(curl -s -w '%{http_code}' -X POST http://127.0.0.1:8000/chat/problem_ingest \
       -H "Content-Type: application/json" \
       -d '{"raw_text":"x+y"}')
CODE=${RESP: -3}   # 取最后 3 位
BODY=${RESP::-3}   # 取前面 JSON
kill $PID
set -e
if [[ "$CODE" != "200" ]]; then
  echo "❌  FastAPI 返回码 $CODE，body=$BODY"; exit 42
fi
echo "   ✅  FastAPI /chat/problem_ingest OK"
echo "🎉  本地 CI 全绿！"
