#!/usr/bin/env bash
# ------------------------------------------------------------
#  v0.5.0  回归脚本（4 条）—— 仅 /chat/problem_ingest 相关
# ------------------------------------------------------------
set -euo pipefail

PORT=8001                     # 你说要用 8001
BASE="http://127.0.0.1:$PORT" # 统一前缀
J='-H Content-Type:application/json'

pass() { echo -e "  \033[32m✅ $1\033[0m"; }
fail() { echo -e "  \033[31m❌ $1\033[0m"; exit 1; }

echo "▶ 1. 正常 200"
curl -s $BASE/chat/problem_ingest $J -d '{"raw_text":"x+y"}' \
| jq -e '.payload.rawLatex=="x+y"' >/dev/null \
  && pass "200 OK" || fail "200 用例失败"

echo "▶ 2. 缺 raw_text → 422"
code=$(curl -s -o /tmp/err.json -w '%{http_code}' \
       $BASE/chat/problem_ingest $J -d '{}')
jq -e '.detail[0].loc[1]=="raw_text"' /tmp/err.json >/dev/null
[ "$code" = 422 ] && pass "422 OK" || fail "422 用例失败"

echo "▶ 3. 真·错路由 → 404"
[ "$(curl -s -o /dev/null -w '%{http_code}' $BASE/this_path_really_does_not_exist)" = 404 ] \
  && pass "404 OK" || fail "404 用例失败"

echo "▶ 4. 不给 Content-Type → FastAPI 解析失败 ⇒ 422"
code=$(curl -s -o /tmp/err.json -w '%{http_code}' \
       $BASE/chat/problem_ingest -d '{"raw_text":"x"}')
jq -e '.detail[0].type=="dict_type"' /tmp/err.json >/dev/null
[ "$code" = 422 ] && pass "422 (解析错误) OK" || fail "Content-Type 用例失败"

echo -e "\n\033[1mALL 4 PASSED\033[0m" 