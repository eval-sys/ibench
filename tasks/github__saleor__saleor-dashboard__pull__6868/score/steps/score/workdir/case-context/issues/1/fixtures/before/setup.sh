#!/usr/bin/env bash
set -euo pipefail

: "${API_URL:?API_URL is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"

fixture_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
bash "$fixture_directory/cleanup.sh"

fixture_email="catalogue.manager.6868@example.com"
fixture_password="CatalogueRow!6868"

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
);
SQL

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

create_type_query='mutation CreateFixtureProductType($input: ProductTypeInput!) {
  productTypeCreate(input: $input) {
    productType { id slug }
    errors { code field message }
  }
}'
create_type_variables='{
  "input": {
    "name": "Lighting",
    "slug": "lighting-6868",
    "kind": "NORMAL",
    "hasVariants": false,
    "isShippingRequired": true,
    "isDigital": false
  }
}'
create_type_response=$(graphql_request "$create_type_query" "$create_type_variables")
jq -e '.data.productTypeCreate.errors | length == 0' <<<"$create_type_response" >/dev/null
product_type_id=$(jq -er '.data.productTypeCreate.productType.id' <<<"$create_type_response")

create_product_query='mutation CreateFixtureProduct($input: ProductCreateInput!) {
  productCreate(input: $input) {
    product { id name slug }
    errors { code field message }
  }
}'
create_product_variables=$(jq -n --arg productType "$product_type_id" '{
  input: {
    name: "Aurora Desk Lamp",
    slug: "aurora-desk-lamp-6868",
    productType: $productType,
    externalReference: "catalogue-row-anchor-6868-product"
  }
}')
create_product_response=$(graphql_request "$create_product_query" "$create_product_variables")
jq -e '.data.productCreate.errors | length == 0' <<<"$create_product_response" >/dev/null
jq -e '.data.productCreate.product.name == "Aurora Desk Lamp"' <<<"$create_product_response" >/dev/null
