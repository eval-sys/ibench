#!/usr/bin/env bash
set -euo pipefail

pg_isready -q -h penpot-postgres -U penpot -d penpot
test "$(redis-cli -h penpot-valkey ping)" = "PONG"
test -w /opt/data/assets
test -x "$(cd /workspace/app/exporter && node --input-type=module -e "import { chromium } from 'playwright'; console.log(chromium.executablePath())")"
