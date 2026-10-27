#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start, or ready}" in
setup)
  generated=()
  mapfile -d '' -t generated < <(git ls-files -z -- 'packages/*/src/components.d.ts')
  ignore_generated() {
    ((${#generated[@]} == 0)) || {
      git restore --worktree -- "${generated[@]}"
      git update-index --assume-unchanged -- "${generated[@]}"
    }
  }
  trap ignore_generated EXIT
  pnpm install --force --frozen-lockfile
  bash -ec 'test -f .env || cp .env.example .env'
  bash -ec 'pnpm --dir packages/hoppscotch-backend exec prisma migrate deploy'
  bash -ec 'pnpm --filter hoppscotch-backend build'
  bash -ec 'pnpm --filter @hoppscotch/selfhost-web build'
  bash -ec 'pnpm --filter hoppscotch-sh-admin build'
  ignore_generated
  trap - EXIT
  ;;
start)
  exec /opt/dev-env-runtime/start.sh
  ;;
ready)
  bash -ec 'pg_isready -q -h hoppscotch-db -U postgres -d hoppscotch'
  bash -ec 'curl -fsS http://echo:8080/healthz > /dev/null'
  bash -ec 'curl -fsS http://localhost:3000/ > /dev/null'
  bash -ec 'curl -fsS http://localhost:3100/ > /dev/null'
  bash -ec 'curl -fsS http://localhost:3170/ping > /dev/null'
  status="$(curl -fsS http://localhost:3170/v1/onboarding/status)"
  if [[ "$(jq -r '.onboardingCompleted' <<<"$status")" != true ]]; then
    curl -fsS http://localhost:3170/v1/onboarding/config \
      -H 'Content-Type: application/json' \
      --data "$(
        jq -cn '{
          VITE_ALLOWED_AUTH_PROVIDERS: "EMAIL",
          MAILER_SMTP_ENABLE: "true",
          MAILER_USE_CUSTOM_CONFIGS: "true",
          MAILER_ADDRESS_FROM: "Hoppscotch <noreply@hoppscotch.test>",
          MAILER_SMTP_HOST: "hoppscotch-mailpit",
          MAILER_SMTP_PORT: "1025",
          MAILER_SMTP_SECURE: "false",
          MAILER_TLS_REJECT_UNAUTHORIZED: "false",
          MAILER_SMTP_IGNORE_TLS: "true"
        }'
      )" >/dev/null
  fi
  curl -fsS http://localhost:3170/v1/onboarding/status \
    | jq -e '.onboardingCompleted == true and .canReRunOnboarding == true' >/dev/null
  curl -fsS http://localhost:3170/v1/auth/providers \
    | jq -e '.providers == ["EMAIL"]' >/dev/null
  curl -fsS http://hoppscotch-mailpit:8025/api/v1/info | jq -e '.Database' >/dev/null
  ;;
*) printf "unknown dev environment action: %s\n" "$1" >&2; exit 2 ;;
esac
