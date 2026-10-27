#!/usr/bin/env bash
set -euo pipefail

case "${1:?expected setup, start or ready}" in
  setup)
    cp .env.example .env
    composer install --no-dev --no-interaction --prefer-dist
    npm ci --no-audit --no-fund
    npm run production
    git diff --exit-code -- composer.lock package-lock.json
    mkdir -p storage/framework/{cache/data,sessions,views} storage/logs public/uploads
    php artisan migrate --force
    php artisan db:seed --force
    php artisan snipeit:demo-settings
    php artisan passport:keys
    chmod 600 storage/oauth-private.key storage/oauth-public.key
    php artisan config:cache
    php artisan view:clear
    chown -R www-data:www-data storage bootstrap/cache public/uploads
    ;;
  start)
    exec apache2ctl -D FOREGROUND
    ;;
  ready)
    curl --fail --silent --show-error http://localhost:8000/health > /dev/null
    ;;
  *) exit 2 ;;
esac
