#!/usr/bin/env bash
set -euo pipefail
# Reuse the admin account prepared by /opt/dev-env-profile.sh and native IDM bootstrap.
# Resolve the personal drive each time: its runtime ID is not a fixture key.
dav_url=$(curl --fail --silent --show-error --insecure -u admin:admin \
  https://localhost:9200/graph/v1.0/me/drives | \
  jq -er '.value[] | select(.driveType == "personal" and .driveAlias == "personal/admin") | .root.webDavUrl')
# This file is the only persistent state owned by this issue.
printf 'Meeting notes\n\nDiscuss the project schedule and next steps.\n' | \
  curl --fail --silent --show-error --insecure -u admin:admin \
  -X PUT -H 'Content-Type: text/plain' --data-binary @- "$dav_url/Meeting%20notes.txt"
