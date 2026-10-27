#!/usr/bin/env bash
set -euo pipefail
case "${1:?expected setup, start or ready}" in
  setup)
    # Native requests may lazily create these runtime keys after preparation.
    # Keep them out of source patches without ignoring application code.
    cat >> .git/info/exclude <<'EOF'
/sites/default/documents/certificates/oaprivate.key
/sites/default/documents/certificates/oapublic.key
/sites/default/documents/logs_and_misc/methods/sevena
/sites/default/documents/logs_and_misc/methods/sevenb
EOF
    composer install --no-dev --no-interaction --prefer-dist
    composer check-platform-reqs --no-dev
    npm ci --no-audit --no-fund
    npm run build
    composer dump-autoload --optimize
    git diff --exit-code -- composer.lock package-lock.json
    chown -R www-data:www-data sites
    runuser -u www-data -- env OPENEMR_ENABLE_INSTALLER_AUTO=1 php contrib/util/installScripts/InstallerAuto.php server=mariadb loginhost=% rootpass=local-root-password
    ;;
  start)
    exec apache2ctl -D FOREGROUND
    ;;
  ready)
    # At this baseline sql.inc.php overwrites the health entrypoint's $config
    # with DatabaseConnectionOptions, so its installed flag is always false.
    # Read the native installation flag directly; OAuth is outside this scope.
    runuser -u www-data -- php -r 'require "/workspace/app/sites/default/sqlconf.php"; exit($config === 1 ? 0 : 1);'
    curl --fail --silent --show-error http://localhost:8000/meta/health/readyz \
      | jq --exit-status '.checks | .database == true and .filesystem == true and .session == true and .cache == true' > /dev/null
    ;;
  *) exit 2 ;;
esac
