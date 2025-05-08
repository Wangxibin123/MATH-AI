#!/usr/bin/env bash
set -euo pipefail

echo "🚀  installing deps (+dev)…"
poetry install --with dev -q

echo "🎯  pre-commit full run…"
poetry run pre-commit run --all-files

echo "🧹  Ruff lint…"
poetry run ruff check .

echo "🧠  MyPy type-check…"
poetry run mypy apps packages

echo "🧪  pytest…"
poetry run pytest -q
echo "✅  unit + static checks passed"

echo "🌐  boot FastAPI stub & test endpoint…"
poetry run uvicorn apps.gateway.main:app --port 8000 --reload &
PID=$!
# 等 2 秒确保 Uvicorn ready
sleep 2
curl -s -X POST http://127.0.0.1:8000/chat/problem_ingest \
     -H "Content-Type: application/json" \
     -d '{"raw_text":"x+y"}' | jq . >/dev/null
kill $PID
echo "✅  FastAPI stub endpoint OK"
