#!/usr/bin/env bash
set -euo pipefail

readonly API_URL="http://saleor-api:8000/graphql/"
readonly FIXTURE_KEY="interaction-fixture"
readonly FIXTURE_VALUE="touch-datagrid-scroll"
readonly PRODUCT_TYPE_SLUG="travel-essentials-touch-list"

graphql_request() {
  local query="$1"
  local variables="${2-}"
  local payload response

  if [[ -z "$variables" ]]; then
    variables='{}'
  fi

  payload="$(jq -nc --arg query "$query" --argjson variables "$variables" \
    '{query: $query, variables: $variables}')"
  if [[ -n "${ACCESS_TOKEN:-}" ]]; then
    response="$(curl -fsS "$API_URL" \
      -H 'Content-Type: application/json' \
      -H "Authorization-Bearer: $ACCESS_TOKEN" \
      --data "$payload")"
  else
    response="$(curl -fsS "$API_URL" \
      -H 'Content-Type: application/json' \
      --data "$payload")"
  fi

  if jq -e '.errors and (.errors | length > 0)' >/dev/null <<<"$response"; then
    jq -c '.errors' >&2 <<<"$response"
    return 1
  fi

  printf '%s\n' "$response"
}

login_variables="$(jq -nc '{email: "admin@example.com", password: "admin"}')"
login_response="$(graphql_request \
  'mutation Login($email: String!, $password: String!) { tokenCreate(email: $email, password: $password) { token errors { field code message } } }' \
  "$login_variables")"

if ! jq -e '.data.tokenCreate.errors | length == 0' >/dev/null <<<"$login_response"; then
  jq -c '.data.tokenCreate.errors' >&2 <<<"$login_response"
  exit 1
fi

ACCESS_TOKEN="$(jq -er '.data.tokenCreate.token' <<<"$login_response")"

owned_response="$(graphql_request \
  'query OwnedFixture($metadata: [MetadataFilter!], $slugs: [String!]) {
    products(first: 100, filter: { metadata: $metadata }) { edges { node { id } } }
    productTypes(first: 100, filter: { slugs: $slugs }) { edges { node { id } } }
  }' \
  "$(jq -nc \
    --arg key "$FIXTURE_KEY" \
    --arg value "$FIXTURE_VALUE" \
    --arg slug "$PRODUCT_TYPE_SLUG" \
    '{metadata: [{key: $key, value: $value}], slugs: [$slug]}')")"

product_ids="$(jq -c '[.data.products.edges[].node.id]' <<<"$owned_response")"
if [[ "$(jq 'length' <<<"$product_ids")" -gt 0 ]]; then
  delete_response="$(graphql_request \
    'mutation DeleteProducts($ids: [ID!]!) { productBulkDelete(ids: $ids) { errors { field code message } } }' \
    "$(jq -nc --argjson ids "$product_ids" '{ids: $ids}')")"
  if ! jq -e '.data.productBulkDelete.errors | length == 0' >/dev/null <<<"$delete_response"; then
    jq -c '.data.productBulkDelete.errors' >&2 <<<"$delete_response"
    exit 1
  fi
fi

while IFS= read -r product_type_id; do
  delete_type_response="$(graphql_request \
    'mutation DeleteProductType($id: ID!) { productTypeDelete(id: $id) { errors { field code message } } }' \
    "$(jq -nc --arg id "$product_type_id" '{id: $id}')")"
  if ! jq -e '.data.productTypeDelete.errors | length == 0' >/dev/null <<<"$delete_type_response"; then
    jq -c '.data.productTypeDelete.errors' >&2 <<<"$delete_type_response"
    exit 1
  fi
done < <(jq -r '.data.productTypes.edges[].node.id' <<<"$owned_response")
