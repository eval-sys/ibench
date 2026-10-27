#!/usr/bin/env bash
set -euo pipefail

# Harbor may install a separate Node runtime for its agent.
export PATH=/opt/node/bin:$PATH

case "${1:?expected setup, start, or ready}" in
setup)
  pwd > /tmp/application-root
  bundle install --jobs 4 --retry 3
  pnpm install --frozen-lockfile --prod=false
  bin/rake db:migrate
  bin/rake assets:precompile
  git diff --quiet HEAD -- Gemfile.lock pnpm-lock.yaml
  ;;
start)
  cd "$(cat /tmp/application-root)"
  exec bin/pitchfork -E production -c config/pitchfork.conf.rb
  ;;
ready)
  pg_isready -q -t 1 -h postgres -U discourse -d discourse
  test "$(timeout 1s redis-cli -h redis ping)" = PONG
  curl -fsS --max-time 1 http://localhost:3000/srv/status >/dev/null
  curl -fsS --max-time 1 http://localhost:3000/site.json >/dev/null
  # Read the same native ProcessSet heartbeat without booting Rails in a 5s health check.
  python3 - <<'PYREADY'
import json
import socket
import subprocess
import time


def redis(*args):
    return json.loads(subprocess.check_output(
        ["redis-cli", "-h", "redis", "-n", "1", "--json", *args], text=True, timeout=1
    ))


for process in redis("SMEMBERS", "processes"):
    info, beat = redis("HMGET", process, "info", "beat")
    if info and beat and json.loads(info)["hostname"] == socket.gethostname() and float(beat) > time.time() - 60:
        break
else:
    raise SystemExit("Sidekiq is not ready")
PYREADY
  ;;
*) printf 'unknown environment action: %s\n' "$1" >&2; exit 2 ;;
esac
