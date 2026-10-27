#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly API_URL="http://saleor-api:8000/graphql/"
readonly FIXTURE_KEY="interaction-fixture"
readonly FIXTURE_VALUE="touch-datagrid-scroll"
readonly PRODUCT_TYPE_SLUG="travel-essentials-touch-list"

bash "$SCRIPT_DIR/cleanup.sh"

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

type_variables="$(jq -nc \
  --arg slug "$PRODUCT_TYPE_SLUG" \
  '{input: {
    name: "Travel Essentials",
    slug: $slug,
    kind: "NORMAL",
    hasVariants: false,
    isShippingRequired: true
  }}')"
type_response="$(graphql_request \
  'mutation CreateProductType($input: ProductTypeInput!) {
    productTypeCreate(input: $input) {
      productType { id }
      errors { field code message }
    }
  }' \
  "$type_variables")"

if ! jq -e '.data.productTypeCreate.errors | length == 0' >/dev/null <<<"$type_response"; then
  jq -c '.data.productTypeCreate.errors' >&2 <<<"$type_response"
  exit 1
fi

product_type_id="$(jq -er '.data.productTypeCreate.productType.id' <<<"$type_response")"
product_names=(
  "Travel Adapter"
  "Travel Blanket"
  "Travel Bottle"
  "Travel Cable Case"
  "Travel Card Holder"
  "Travel Daypack"
  "Travel Eye Mask"
  "Travel Flask"
  "Travel Journal"
  "Travel Laundry Bag"
  "Travel Luggage Tag"
  "Travel Organizer"
  "Travel Pillow"
  "Travel Rain Shell"
  "Travel Shoe Bag"
  "Travel Sling"
  "Travel Towel"
  "Travel Umbrella"
  "Travel Wallet"
  "Travel Wash Bag"
)

for index in "${!product_names[@]}"; do
  item_number="$(printf '%02d' "$((index + 1))")"
  product_variables="$(jq -nc \
    --arg name "${product_names[$index]}" \
    --arg slug "seasonal-travel-item-$item_number" \
    --arg external_reference "travel-essentials-touch-item-$item_number" \
    --arg product_type "$product_type_id" \
    --arg fixture_key "$FIXTURE_KEY" \
    --arg fixture_value "$FIXTURE_VALUE" \
    '{input: {
      name: $name,
      slug: $slug,
      externalReference: $external_reference,
      productType: $product_type,
      metadata: [{key: $fixture_key, value: $fixture_value}]
    }}')"
  product_response="$(graphql_request \
    'mutation CreateProduct($input: ProductCreateInput!) {
      productCreate(input: $input) {
        product { id }
        errors { field code message }
      }
    }' \
    "$product_variables")"

  if ! jq -e '.data.productCreate.errors | length == 0' >/dev/null <<<"$product_response"; then
    jq -c '.data.productCreate.errors' >&2 <<<"$product_response"
    exit 1
  fi
done

verify_response="$(graphql_request \
  'query VerifyFixture($metadata: [MetadataFilter!]) {
    products(first: 100, filter: { metadata: $metadata }) { totalCount }
  }' \
  "$(jq -nc \
    --arg key "$FIXTURE_KEY" \
    --arg value "$FIXTURE_VALUE" \
    '{metadata: [{key: $key, value: $value}]}')")"

if [[ "$(jq -r '.data.products.totalCount' <<<"$verify_response")" != "20" ]]; then
  echo "Expected 20 fixture products" >&2
  exit 1
fi
