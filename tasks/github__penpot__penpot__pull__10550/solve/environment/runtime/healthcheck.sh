#!/usr/bin/env bash
set -euo pipefail

test "$(curl -fsS http://localhost:3000/readyz)" = "OK"
test "$(curl -fsS http://localhost:6061/readyz)" = "OK"
curl -fsS http://localhost:3000/ > /dev/null
