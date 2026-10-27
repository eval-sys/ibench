DEV_ENV_REPOSITORY_URL=https://github.com/Dolibarr/dolibarr.git
DEV_ENV_LOCKS=(
  .vendor-dependencies.lock.json
)

dev_env_checkout() {
  local workspace=$1 revision=$2
  test ! -e "$workspace"
  git init "$workspace"
  git -C "$workspace" remote add origin "$DEV_ENV_REPOSITORY_URL"
  git -C "$workspace" fetch --depth=1 origin "$revision"
  git -C "$workspace" checkout --detach FETCH_HEAD
  test "$(git -C "$workspace" rev-parse HEAD)" = "$revision"
  test -z "$(git -C "$workspace" status --porcelain)"
}

dev_env_restore_locks() {
  local workspace=$1 source=$2 lock
  for lock in "${DEV_ENV_LOCKS[@]}"; do
    test -f "$source/locks/$lock"
    mkdir -p "$workspace/$(dirname "$lock")"
    cp "$source/locks/$lock" "$workspace/$lock"
  done
  rm -rf -- "$source/locks"
}

dev_env_setup() {
  local workspace=$1 mode=$2
  (cd "$workspace" && DEV_ENV_LOCK_MODE="$mode" bash -ec "$DEV_ENV_SETUP")
}

dev_env_start() {
  (cd "$1" && exec nohup bash -ec "$DEV_ENV_START" >"$2" 2>&1) &
  DEV_ENV_SERVICE_PID=$!
}

dev_env_wait_ready() {
  local workspace=$1 service_pid=$2 service_log=$3
  for _ in $(seq 1 120); do
    (cd "$workspace" && bash -ec "$DEV_ENV_READY") >/dev/null 2>&1 && return 0
    kill -0 "$service_pid" 2>/dev/null || break
    sleep 2
  done
  tail -n 80 "$service_log" >&2
  return 1
}

dev_env_start_ready() {
  dev_env_start "$1" "$2"
  dev_env_wait_ready "$1" "$DEV_ENV_SERVICE_PID" "$2"
}
