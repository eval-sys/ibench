#!/usr/bin/env bash
set -euo pipefail
# Called from the historical checkout after its dependencies have been installed.
test -f be/apps/core/package.json
# Each task has a fresh database. Use this checkout's schema; historical migrations
# can add and consume enum values in one transaction, which PostgreSQL rejects.
pnpm --filter @afilmory/db exec drizzle-kit push --force
exclude_file="$(git rev-parse --git-path info/exclude)"
for path in /be/apps/core/fixture.vite.config.ts /be/apps/core/fixture-seed.ts; do
  grep -Fqx "$path" "$exclude_file" || printf '%s\n' "$path" >> "$exclude_file"
done
cp /opt/dev-env-fixtures/vite.config.ts be/apps/core/fixture.vite.config.ts
pnpm --filter @afilmory/core exec vite-node --config fixture.vite.config.ts src/index.ts \
  --reset-superadmin-password --password Local-Development-2026
cp /opt/dev-env-fixtures/seed.ts be/apps/core/fixture-seed.ts
pnpm --filter @afilmory/core exec vite-node --config fixture.vite.config.ts fixture-seed.ts
