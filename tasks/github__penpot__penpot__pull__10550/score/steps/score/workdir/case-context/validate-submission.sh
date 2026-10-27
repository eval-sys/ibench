#!/usr/bin/env bash

set -euo pipefail

scratch="$(mktemp -d /tmp/submission-check.XXXXXX)"
trap 'rm -rf "$scratch"' EXIT

IBENCH_SCORE_OUTPUT_ROOT=/logs/artifacts/tasks/github__penpot__penpot__pull__10550 \
IBENCH_SCORE_INPUT_ROOT=/workspace/case-context \
IBENCH_SCORE_WORKSPACE=/workspace/app \
IBENCH_SCORE_TASK_ID=github__penpot__penpot__pull__10550 \
IBENCH_SCORE_LOCK_PATHS='["frontend/pnpm-lock.yaml", "render-wasm/pnpm-lock.yaml", "render-wasm/Cargo.lock", "exporter/pnpm-lock.yaml"]' \
IBENCH_SCORE_REWARD_FILE="$scratch/reward.json" \
IBENCH_SCORE_ISSUE_RESULTS_FILE="$scratch/issue-results.json" \
IBENCH_SCORE_PROTOCOL_ONLY=1 \
  /opt/harbor-verifier/bin/python -m pytest -q \
    /workspace/case-context/test_verdict.py
