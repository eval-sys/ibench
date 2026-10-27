#!/usr/bin/env bash
set -euo pipefail

mkdir -p frontend/resources/public/js /opt/data/assets /logs/artifacts
cp /opt/penpot-runtime/config.js frontend/resources/public/js/config.js
