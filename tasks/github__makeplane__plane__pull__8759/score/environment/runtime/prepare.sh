#!/usr/bin/env bash
set -euo pipefail

test -f apps/api/.env.example
test -f apps/web/.env.example
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

secret_key="$(openssl rand -hex 32)"
printf '\nSECRET_KEY="%s"\n' "$secret_key" >> apps/api/.env
sed -i -E \
  's#^AWS_S3_ENDPOINT_URL=.*#AWS_S3_ENDPOINT_URL="http://plane-rustfs:9000"#; s#^USE_MINIO=.*#USE_MINIO=1#' \
  apps/api/.env
sed -i -E \
  's#^VITE_API_BASE_URL=.*#VITE_API_BASE_URL="http://localhost:3000"#' \
  apps/web/.env

/opt/plane-api/bin/python - <<'PY'
import boto3
import os

s3 = boto3.client("s3", endpoint_url=os.environ["AWS_S3_ENDPOINT_URL"])
bucket_name = os.environ["AWS_S3_BUCKET_NAME"]
if bucket_name not in {bucket["Name"] for bucket in s3.list_buckets()["Buckets"]}:
    s3.create_bucket(Bucket=bucket_name)
PY
