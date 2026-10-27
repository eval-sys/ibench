#!/usr/bin/env bash

set -euo pipefail

mkdir -p /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/evidence /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay
cp /workspace/case-context/issues/2/fixtures/reference-after/action.mjs /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/action.mjs
cp /workspace/case-context/issues/2/fixtures/reference-after/cleanup.mjs /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/cleanup.mjs
cp /workspace/case-context/issues/2/fixtures/reference-after/cleanup.sh /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/cleanup.sh
cp /workspace/case-context/issues/2/fixtures/reference-after/cleanup.sql /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/cleanup.sql
cp /workspace/case-context/issues/2/fixtures/reference-after/presentation.json /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/presentation.json
cp /workspace/case-context/issues/2/fixtures/reference-after/setup.mjs /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/setup.mjs
cp /workspace/case-context/issues/2/fixtures/reference-after/setup.sh /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/setup.sh
cp /workspace/case-context/issues/2/fixtures/reference-after/setup.sql /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/replay/setup.sql
printf '%s\n' '{"error":"FIXTURE_NOT_IMPLEMENTED: write a schema-valid verdict"}' > /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/2/verdict.json
mkdir -p /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/evidence /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay
cp /workspace/case-context/issues/3/fixtures/reference-after/action.mjs /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/action.mjs
cp /workspace/case-context/issues/3/fixtures/reference-after/cleanup.mjs /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/cleanup.mjs
cp /workspace/case-context/issues/3/fixtures/reference-after/cleanup.sh /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/cleanup.sh
cp /workspace/case-context/issues/3/fixtures/reference-after/cleanup.sql /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/cleanup.sql
cp /workspace/case-context/issues/3/fixtures/reference-after/presentation.json /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/presentation.json
cp /workspace/case-context/issues/3/fixtures/reference-after/setup.mjs /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/setup.mjs
cp /workspace/case-context/issues/3/fixtures/reference-after/setup.sh /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/setup.sh
cp /workspace/case-context/issues/3/fixtures/reference-after/setup.sql /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/replay/setup.sql
printf '%s\n' '{"error":"FIXTURE_NOT_IMPLEMENTED: write a schema-valid verdict"}' > /logs/artifacts/tasks/github__penpot__penpot__pull__11699/issues/3/verdict.json

