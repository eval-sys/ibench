#!/usr/bin/env bash
set -euo pipefail

root="$(dirname "$0")"
source "$root/dev-env.sh"
rm -- "$root/dev-env.sh" "$0"
workspace=/workspace/app
dev_env_checkout "$workspace" ae9b8a5fe6e43bfe3d4dd07c24efe6c0ddca729c
dev_env_restore_locks "$workspace" "$root"
git -C "$workspace" config user.name 'Task Environment'
git -C "$workspace" config user.email task-environment@example.invalid
git -C "$workspace" add -f -- "${DEV_ENV_LOCKS[@]}"
GIT_AUTHOR_DATE=2000-01-01T00:00:00Z GIT_COMMITTER_DATE=2000-01-01T00:00:00Z \
  git -C "$workspace" -c core.hooksPath=/dev/null commit --allow-empty -m 'Frozen dependency locks' >/dev/null

output=/logs/artifacts/solver
mkdir -p "$output/runtime"
trap 'chmod -R a+rwX "$output" 2>/dev/null || true' EXIT
build_log=/logs/artifacts/solver/runtime/setup.log
mkdir -p "$(dirname "$build_log")"
(
  set -euxo pipefail
  dev_env_setup "$workspace" restore
) >"$build_log" 2>&1
bash "$root/after-build.sh"
rm -- "$root/after-build.sh"
dev_env_start_ready "$workspace" /logs/artifacts/solver/runtime/service.log
