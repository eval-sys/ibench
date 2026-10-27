#!/usr/bin/env bash
set -euo pipefail

cp api/.env.example api/.env
cp /opt/dify-runtime/web.env web/.env.local
uv run --frozen --directory api flask db upgrade
