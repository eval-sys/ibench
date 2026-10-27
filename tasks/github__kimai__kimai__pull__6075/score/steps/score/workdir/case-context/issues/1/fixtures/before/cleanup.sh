#!/usr/bin/env bash
set -euo pipefail
# The development profile loads UserFixtures, including token_super.
# Customer deletion uses Kimai's native cascading deletion of linked projects.
curl --fail --silent --show-error -H 'Authorization: Bearer token_super' \
  'http://localhost:8000/api/customers?visible=3' |
  jq -r '.[] | select((.number == "C-6075-NORTH" and .name == "Northwind Studio") or (.number == "C-6075-EAST" and .name == "Eastwood Design") or (.number == "C-6075-WEST" and .name == "Westbridge Services")) | .id' |
  while IFS= read -r customer_id; do
    curl --fail --silent --show-error -H 'Authorization: Bearer token_super' \
      -X DELETE "http://localhost:8000/api/customers/${customer_id}"
  done
