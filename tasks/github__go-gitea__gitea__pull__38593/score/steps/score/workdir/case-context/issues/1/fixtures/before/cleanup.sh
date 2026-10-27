#!/usr/bin/env bash
set -euo pipefail

# Native purge removes this issue's account, repository, issues and dependencies.
# The public lookup distinguishes a missing account from a service failure.
status=$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  http://localhost:3000/api/v1/users/release-coordinator)
case "$status" in
  404) exit 0 ;;
  200)
    runuser -u git -- /workspace/app/gitea \
      --work-path /tmp/gitea-runtime \
      --config /tmp/gitea-runtime/custom/conf/app.ini \
      admin user delete --username release-coordinator --purge
    ;;
  *) printf 'Could not check release-coordinator account: HTTP %s\n' "$status" >&2; exit 1 ;;
esac
