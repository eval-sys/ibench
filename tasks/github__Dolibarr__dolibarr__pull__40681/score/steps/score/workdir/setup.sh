#!/usr/bin/env bash

set -euo pipefail

root="$(dirname "$0")"
source "$root/dev-env.sh"
rm -- "$root/dev-env.sh" "$0"
workspace=/workspace/app
output=/logs/artifacts/tasks/github__Dolibarr__dolibarr__pull__40681
mkdir -p "$output/runtime" "$output/evidence"
trap 'chmod -R a+rwX /logs/artifacts 2>/dev/null || true' EXIT

candidate="$root/candidate"
if [[ -f "$candidate.patch" ]]; then
  dev_env_checkout "$workspace" 30d915ad3ff1fa7d14dddc585fd7a4b4ade2bb36
  git -C "$workspace" apply --binary --index "$candidate.patch"
  rm -- "$candidate.patch"
else
  dev_env_checkout "$workspace" "$(<"$candidate")"
  rm -- "$candidate"
fi
dev_env_restore_locks "$workspace" "$root"
git -C "$workspace" add -f -- "${DEV_ENV_LOCKS[@]}"

git -C "$workspace" config user.name 'Task Environment'
git -C "$workspace" config user.email task-environment@example.invalid
GIT_AUTHOR_DATE=2000-01-01T00:00:00Z GIT_COMMITTER_DATE=2000-01-01T00:00:00Z \
  git -C "$workspace" -c core.hooksPath=/dev/null commit --allow-empty -m 'Candidate changes' >/dev/null
git -C "$workspace" rev-parse HEAD > "$output/runtime/candidate-commit-sha.txt"

dev_env_setup "$workspace" restore >"$output/runtime/setup.log" 2>&1
git -C "$workspace" add -A
git -C "$workspace" -c core.hooksPath=/dev/null commit --allow-empty -m 'Prepared candidate' >/dev/null
git -C "$workspace" rev-parse HEAD > "$output/runtime/candidate-commit-sha.txt"
lock=.vendor-dependencies.lock.json
mkdir -p "$output/runtime/locks/$(dirname "$lock")"
cp "$workspace/$lock" "$output/runtime/locks/$lock"

dev_env_start_ready "$workspace" "$output/runtime/service.log"
bash "$root"/verifier-inputs.sh
rm -- "$root"/verifier-inputs.sh
