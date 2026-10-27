#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
version=$(cat "$project_root/environments/base/VERSION")

docker build \
  --tag "ibench-dev:$version" \
  --build-arg "IBENCH_DEV_VERSION=$version" \
  "$project_root/environments/base"
