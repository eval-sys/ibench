#!/usr/bin/env bash
set -euo pipefail

pg_isready -q -h saleor-db -U saleor -d saleor
test "$(psql "$DATABASE_URL" -Atqc 'SELECT 1')" = 1
test "$(redis-cli -h saleor-cache ping)" = PONG
curl -fsS http://saleor-api:8000/health/ > /dev/null

response="$(curl -fsS http://saleor-api:8000/graphql/ \
  -H 'content-type: application/json' \
  --data-binary '{"query":"{ shop { name } }"}')"
python3 -c 'import json,sys; assert json.load(sys.stdin)["data"]["shop"]["name"]' <<<"$response"
