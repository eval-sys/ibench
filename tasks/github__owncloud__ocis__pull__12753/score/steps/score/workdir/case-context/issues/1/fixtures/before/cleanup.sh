#!/usr/bin/env bash
set -euo pipefail
dav_url=$(curl --fail --silent --show-error --insecure -u admin:admin \
  https://localhost:9200/graph/v1.0/me/drives | \
  jq -er '.value[] | select(.driveType == "personal" and .driveAlias == "personal/admin") | .root.webDavUrl')
status=$(curl --silent --show-error --insecure -u admin:admin \
  -X DELETE -o /dev/null -w '%{http_code}' "$dav_url/Meeting%20notes.txt")
case "$status" in
  200|204|404) ;; 
  *) echo "Could not remove the issue-owned document (HTTP $status)" >&2; exit 1 ;;
esac
