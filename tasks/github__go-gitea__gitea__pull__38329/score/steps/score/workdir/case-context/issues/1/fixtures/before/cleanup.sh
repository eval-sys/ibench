#!/usr/bin/env bash
set -euo pipefail
# This entire runtime belongs to this issue; the supplied port-3000 service is untouched.
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
