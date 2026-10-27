#!/usr/bin/env bash
set -euo pipefail

case "${1:?setup, start or ready required}" in
  setup)
    composer install --prefer-dist --no-progress --no-interaction
    npm ci --no-audit --no-fund
    composer run compile-plurals
    npm run rtlcss
    git diff --exit-code -- composer.lock package-lock.json

    # Adapt the same-commit upstream Apache configuration to the stage checkout.
    sed -e "s|/var/www/FreshRSS|$PWD|g" -e 's/^Listen 80$/Listen 3210/' \
      Docker/FreshRSS.Apache.conf > /etc/apache2/sites-available/freshrss.conf
    a2ensite freshrss
    mkdir -p "$DATA_PATH"
    php cli/prepare.php
    if [[ ! -f "$DATA_PATH/applied_migrations.txt" ]]; then
      php cli/do-install.php --default-user admin --environment production \
        --base-url http://localhost:3210 --language en --auth-type form \
        --api-enabled --disable-update --db-type pgsql --db-host postgres \
        --db-user freshrss --db-password profile-development --db-base freshrss
      php cli/create-user.php --user admin --password profile-development --language en --no-default-feeds
    fi
    chown -R www-data:www-data "$DATA_PATH"
    apache2ctl configtest
    ;;
  start)
    # Debian's standard envvars script probes optional unset variables.
    set +u
    source /etc/apache2/envvars
    set -u
    exec apache2 -D FOREGROUND
    ;;
  ready)
    pg_isready -q -d "$DATABASE_URL"
    php /workspace/app/cli/health.php --url=http://localhost:3210/api/
    ;;
  *) exit 2 ;;
esac
