#!/usr/bin/env bash
# ------------------------------------------------------------
#  v0.5  ➜ v0.6  通用脚本
#    FLAG_REST=false  只跑 5 条（v0.5）
#    FLAG_REST=true   跑满 8 条（v0.6 之后）
# ------------------------------------------------------------
set -euo pipefail
PORT=8001
BASE="http://127.0.0.1:$PORT"
PB_ID="11111111-2222-3333-4444-555555555555"
J='-H Content-Type:application/json'
FLAG_REST=${FLAG_REST:-false}   # 环境变量控制

step() { printf "\n\033[1m▶ %s\033[0m\n" "$1"; }
ok()   { echo -e "  \033[32m✅ $1\033[0m"; }
err()  { echo -e "  \033[31m❌ $1\033[0m"; exit 1; }

### Router 三正两错 ##################################################
step "Router 200"
curl -s $BASE/chat/problem_ingest $J -d '{"raw_text":"x+y"}' \
| jq -e '.payload.rawLatex=="x+y"' >/dev/null && ok OK || err FAIL

step "Router 422 缺 raw_text"
curl -s -o /tmp/r1.json -w '%{http_code}' $BASE/chat/problem_ingest $J -d '{}' \
| grep -q 422 && jq -e '.[0].loc[1]=="raw_text"' /tmp/r1.json >/dev/null \
  && ok OK || err FAIL

step "Router 404"
curl -s -o /dev/null -w '%{http_code}' $BASE/chat/not_exist $J -d '{}' \
| grep -q 404 && ok OK || err FAIL

step "Router 415 缺 Content-Type"
curl -s -o /dev/null -w '%{http_code}' $BASE/chat/problem_ingest -d '{"raw_text":"x"}' \
| grep -q 415 && ok OK || err FAIL

step "Router OPTIONS (CORS)"
curl -s -o /dev/null -w '%{http_code}' -X OPTIONS $BASE/chat/problem_ingest \
| grep -Eq '200|204' && ok OK || echo "  ⚠️  CORS 未配置，可忽略"

### REST 三条（仅 v0.6 之后打开） ###############################
if $FLAG_REST; then
  step "REST ingest 200"
  curl -s $BASE/problems/ingest $J \
       -d '{"raw_text":"x+y","problem_id":"'"$PB_ID"'"}' \
  | jq -e '.blockId' >/dev/null && ok OK || err FAIL

  step "REST 422 缺 problem_id"
  curl -s -o /tmp/r2.json -w '%{http_code}' $BASE/problems/ingest $J \
       -d '{"raw_text":"x"}' | grep -q 422 \
  && jq -e '.[0].loc[1]=="problem_id"' /tmp/r2.json >/dev/null && ok OK || err FAIL

  step "REST 422 非法 UUID"
  curl -s -o /tmp/r3.json -w '%{http_code}' $BASE/problems/ingest $J \
       -d '{"raw_text":"x","problem_id":"not-uuid"}' | grep -q 422 \
  && jq -e '.[0].msg | contains("uuid")' /tmp/r3.json >/dev/null && ok OK || err FAIL
else
  echo -e "\n🛈  REST 相关 3 条已跳过（FLAG_REST=false）。"
fi 