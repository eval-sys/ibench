#!/usr/bin/env bash
set -euo pipefail

: "${API_URL:?API_URL is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"

fixture_email="catalogue.manager.6868@example.com"
fixture_password="CatalogueRow!6868"
fixture_product_reference="catalogue-row-anchor-6868-product"
fixture_product_type_slug="lighting-6868"
fixture_product_type_name="Lighting"

ensure_fixture_account() {
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO account_user (
  id,
  is_superuser,
  email,
  is_staff,
  is_active,
  password,
  date_joined,
  first_name,
  last_name,
  private_metadata,
  metadata,
  jwt_token_key,
  language_code,
  search_document,
  updated_at,
  uuid,
  external_reference,
  is_confirmed,
  number_of_orders
)
VALUES (
  nextval('public.userprofile_user_id_seq'),
  TRUE,
  'catalogue.manager.6868@example.com',
  TRUE,
  TRUE,
  'pbkdf2_sha256$1000000$saleorFixture6868$6EsBgfQz6TLgb9WMgJ26NCU7lC5CfpbZfKDJT1pmTsY=',
  NOW(),
  'Catalogue',
  'Manager',
  '{}'::jsonb,
  '{}'::jsonb,
  'catalog6868k',
  'en',
  '',
  NOW(),
  '68680000-0000-4000-8000-000000000001'::uuid,
  'catalogue-manager-6868',
  TRUE,
  0
)
ON CONFLICT (email) DO UPDATE SET
  is_superuser = EXCLUDED.is_superuser,
  is_staff = EXCLUDED.is_staff,
  is_active = EXCLUDED.is_active,
  password = EXCLUDED.password,
  first_name = EXCLUDED.first_name,
  last_name = EXCLUDED.last_name,
  jwt_token_key = EXCLUDED.jwt_token_key,
  external_reference = EXCLUDED.external_reference,
  is_confirmed = EXCLUDED.is_confirmed,
  updated_at = NOW();
SQL
}

graphql_request() {
  local query="$1"
  local variables="$2"
  local -a headers=(--header 'Content-Type: application/json')

  if [[ -n "${fixture_token:-}" ]]; then
    headers+=(--header "Authorization: Bearer ${fixture_token}")
  fi

  jq -n --arg query "$query" --argjson variables "$variables" \
    '{query: $query, variables: $variables}' |
    curl --fail --silent --show-error \
      "${headers[@]}" \
      --data-binary @- \
      "$API_URL"
}

ensure_fixture_account

login_query='mutation Login($email: String!, $password: String!) {
  tokenCreate(email: $email, password: $password) {
    token
    errors { code message }
  }
}'
login_variables=$(jq -n --arg email "$fixture_email" --arg password "$fixture_password" \
  '{email: $email, password: $password}')
fixture_token=""
login_response=$(graphql_request "$login_query" "$login_variables")
fixture_token=$(jq -er '.data.tokenCreate.token' <<<"$login_response")

product_query='query FixtureProduct($externalReference: String!) {
  product(externalReference: $externalReference) { id }
}'
product_variables=$(jq -n --arg externalReference "$fixture_product_reference" \
  '{externalReference: $externalReference}')
product_response=$(graphql_request "$product_query" "$product_variables")
product_id=$(jq -r '.data.product.id // empty' <<<"$product_response")

if [[ -n "$product_id" ]]; then
  delete_product_query='mutation DeleteFixtureProduct($id: ID!) {
    productDelete(id: $id) { errors { code field message } }
  }'
  delete_product_variables=$(jq -n --arg id "$product_id" '{id: $id}')
  delete_product_response=$(graphql_request "$delete_product_query" "$delete_product_variables")
  jq -e '.data.productDelete.errors | length == 0' <<<"$delete_product_response" >/dev/null
fi

product_types_query='query FixtureProductTypes($search: String!) {
  productTypes(first: 100, filter: { search: $search }) {
    edges { node { id slug } }
  }
}'
product_types_variables=$(jq -n --arg search "$fixture_product_type_name" '{search: $search}')
product_types_response=$(graphql_request "$product_types_query" "$product_types_variables")
mapfile -t product_type_ids < <(
  jq -r --arg slug "$fixture_product_type_slug" \
    '.data.productTypes.edges[]?.node | select(.slug == $slug) | .id' \
    <<<"$product_types_response"
)

for product_type_id in "${product_type_ids[@]}"; do
  delete_type_query='mutation DeleteFixtureProductType($id: ID!) {
    productTypeDelete(id: $id) { errors { code field message } }
  }'
  delete_type_variables=$(jq -n --arg id "$product_type_id" '{id: $id}')
  delete_type_response=$(graphql_request "$delete_type_query" "$delete_type_variables")
  jq -e '.data.productTypeDelete.errors | length == 0' <<<"$delete_type_response" >/dev/null
done

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
DELETE FROM account_user
WHERE email = 'catalogue.manager.6868@example.com'
   OR external_reference = 'catalogue-manager-6868'
   OR uuid = '68680000-0000-4000-8000-000000000001'::uuid;
SQL
