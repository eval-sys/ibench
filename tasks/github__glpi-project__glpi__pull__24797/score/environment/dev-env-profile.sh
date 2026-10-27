#!/usr/bin/env bash
set -euo pipefail
cd /workspace/app
case "${1:?setup, start or ready}" in
  setup)
    composer install --no-interaction --prefer-dist
    npm ci --no-audit --no-fund
    npm run dependencies:postinstall
    npm run build
    php bin/console tools:locales:compile --allow-superuser --no-interaction
    git diff --exit-code -- composer.lock package-lock.json
    php bin/console database:install --allow-superuser --no-interaction       --reconfigure --force --db-host=mariadb --db-name=glpi       --db-user=glpi --db-password=glpi --default-language=en_GB --no-telemetry
    chown -R www-data:www-data config files public/lib public/build
    ;;
  start)
    exec apache2ctl -D FOREGROUND
    ;;
  ready)
    curl --fail --silent --show-error --max-time 2 http://localhost:8000/ >/dev/null
    runuser -u www-data -- php bin/console system:status --service=db       | jq -e '.status == "OK" and .main.status == "OK"' >/dev/null
    ;;
  *) exit 2 ;;
esac
