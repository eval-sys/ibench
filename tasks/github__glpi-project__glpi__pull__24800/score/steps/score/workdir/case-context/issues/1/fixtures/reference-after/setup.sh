#!/usr/bin/env bash
set -euo pipefail
# The shared HTTP helper creates the complete personal view (Status only).
bash "$(dirname -- "${BASH_SOURCE[0]}")/cleanup.sh" setup
