#!/usr/bin/env bash
set -euo pipefail
# Stop only the issue fixture, then restore the prepared profile service.
runtime=/tmp/gitea-actions-status
if [[ -f "$runtime/server.pid" ]]; then
  read -r server_pid < "$runtime/server.pid"
  if [[ "$server_pid" =~ ^[0-9]+$ ]] && [[ -r "/proc/$server_pid/cmdline" ]] && tr '\0' ' ' < "/proc/$server_pid/cmdline" | grep -Fq -- "$runtime"; then
    kill "$server_pid" || true
    for _ in {1..50}; do
      if ! kill -0 "$server_pid" 2>/dev/null || [[ "$(cut -d' ' -f3 "/proc/$server_pid/stat" 2>/dev/null || true)" == Z ]]; then break; fi
      sleep 0.1
    done
    if kill -0 "$server_pid" 2>/dev/null; then kill -KILL "$server_pid" || true; fi
  fi
fi
rm -rf -- "$runtime"

if ! curl --silent --fail http://localhost:3000/api/healthz >/dev/null; then
  runuser -u git -- bash -c 'nohup setsid /workspace/app/gitea --work-path /tmp/gitea-runtime --config /tmp/gitea-runtime/custom/conf/app.ini web > /tmp/gitea-runtime/server.log 2>&1 < /dev/null &'
  for _ in {1..100}; do
    if curl --silent --fail http://localhost:3000/api/healthz >/dev/null; then break; fi
    sleep 0.2
  done
fi
