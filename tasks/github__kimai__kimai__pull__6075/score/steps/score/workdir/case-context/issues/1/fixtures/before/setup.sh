#!/usr/bin/env bash
set -euo pipefail
bash "$(dirname "${BASH_SOURCE[0]}")/cleanup.sh"
# CustomerFixtures generates random names and keys; these isolated records
# provide the stable multi-customer/multi-project precondition instead.
create_customer() {
  curl --fail --silent --show-error -H 'Authorization: Bearer token_super' \
    -X POST 'http://localhost:8000/api/customers' \
    --data-urlencode "name=$1" --data-urlencode "number=$2" \
    -d 'country=US&currency=USD&timezone=UTC&visible=1&billable=1' |
    jq -er '.id'
}
create_project() {
  curl --fail --silent --show-error -H 'Authorization: Bearer token_super' \
    -X POST 'http://localhost:8000/api/projects' \
    --data-urlencode "name=$1" --data-urlencode "customer=$2" \
    -d 'visible=1&billable=1&globalActivities=1' | jq -e '.id' >/dev/null
}
north_id=$(create_customer 'Northwind Studio' 'C-6075-NORTH')
east_id=$(create_customer 'Eastwood Design' 'C-6075-EAST')
create_customer 'Westbridge Services' 'C-6075-WEST' >/dev/null
create_project 'Brand planning' "$north_id"
create_project 'Website design' "$north_id"
create_project 'Content review' "$east_id"
