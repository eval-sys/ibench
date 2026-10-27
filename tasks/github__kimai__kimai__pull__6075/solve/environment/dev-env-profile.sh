#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
case "${1:?setup, start or ready}" in
  setup)
    if [ ! -f .env.local ]; then
      printf 'APP_SECRET=%s\n' "$(php -r 'echo bin2hex(random_bytes(32));')" > .env.local
    fi
    composer install --no-interaction --prefer-dist
    pnpm install --frozen-lockfile --ignore-scripts
    pnpm run build
    APP_ENV=dev APP_DEBUG=0 php bin/console kimai:reset:dev --no-interaction
    php bin/console doctrine:schema:validate --skip-sync --no-interaction
    php bin/console doctrine:migrations:up-to-date --no-interaction
    php bin/console cache:clear --env=prod --no-debug
    git diff --exit-code -- composer.lock pnpm-lock.yaml symfony.lock
    chown -R www-data:www-data var public/build public/bundles
    ;;
  start)
    exec apache2ctl -D FOREGROUND
    ;;
  ready)
    curl --fail --location --silent --show-error --max-time 2 http://localhost:8000/en/login >/dev/null
    mariadb --host=mariadb --user=kimai --password=kimai --database=kimai --batch --skip-column-names --execute='SELECT 1' | grep -qx 1
    ;;
  *) exit 2 ;;
esac
