#!/usr/bin/env bash

set -euo pipefail

workspace=/workspace/app
output=/logs/artifacts/solver
git -C "$workspace" config user.name 'Task Environment'
git -C "$workspace" config user.email task-environment@example.invalid
git -C "$workspace" add -A
git -C "$workspace" add -f pnpm-lock.yaml

git -C "$workspace" -c core.hooksPath=/dev/null commit --allow-empty -m 'Prepared workspace' >/dev/null
git -C "$workspace" rev-parse HEAD > "$output/runtime/prepared-commit-sha.txt"
