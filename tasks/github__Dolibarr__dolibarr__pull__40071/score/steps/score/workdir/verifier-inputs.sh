#!/usr/bin/env bash

set -euo pipefail

mkdir -p /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/evidence /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay
cp /workspace/case-context/issues/1/fixtures/reference-after/action.mjs /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/action.mjs
cp /workspace/case-context/issues/1/fixtures/reference-after/cleanup.mjs /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/cleanup.mjs
cp /workspace/case-context/issues/1/fixtures/reference-after/cleanup.sh /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/cleanup.sh
cp /workspace/case-context/issues/1/fixtures/reference-after/cleanup.sql /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/cleanup.sql
cp /workspace/case-context/issues/1/fixtures/reference-after/presentation.json /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/presentation.json
cp /workspace/case-context/issues/1/fixtures/reference-after/setup.mjs /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/setup.mjs
cp /workspace/case-context/issues/1/fixtures/reference-after/setup.sh /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/setup.sh
cp /workspace/case-context/issues/1/fixtures/reference-after/setup.sql /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/replay/setup.sql
printf '%s\n' '{"error":"FIXTURE_NOT_IMPLEMENTED: write a schema-valid verdict"}' > /logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40071/issues/1/verdict.json

