#!/usr/bin/env bash
# Trusted release verifier entrypoint.
set -euo pipefail

mkdir -p /logs/verifier
if /opt/harbor-verifier/bin/python -m pytest \
  -q \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_verdict.py; then
  exit 0
fi
test -f /logs/verifier/reward.json || printf '{"reward":0,"protocol":0,"repair":0}\n' > /logs/verifier/reward.json
exit 1
