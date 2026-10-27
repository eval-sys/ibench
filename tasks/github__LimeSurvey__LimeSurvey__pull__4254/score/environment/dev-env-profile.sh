#!/usr/bin/env bash
set -euo pipefail
case "${1:?expected setup, start or ready}" in
  setup)
    # Keep the repository's CKEditor bundle; exclude only Redactor assets.
    git sparse-checkout set --no-cone --stdin <<'PATTERNS'
/*
!/application/extensions/yiiwheels/widgets/redactor/assets/
PATTERNS
    composer install --no-dev --no-interaction --prefer-dist
    if [[ ${DEV_ENV_LOCK_MODE:-restore} == resolve && ! -f yarn.lock ]]; then
      yarn install --non-interactive
    else
      test -f yarn.lock
      yarn install --frozen-lockfile --non-interactive
    fi
    yarn --cwd assets/packages/adminbasics install --frozen-lockfile --non-interactive
    yarn --cwd assets/packages/adminbasics build
    gulp_tasks=(build build_theme build_survey_theme_fruity build_survey_theme_ls6)
    if node -e "process.exit('build_bootstrap' in require('./gulpfile.js') ? 0 : 1)"; then
      gulp_tasks=(build_bootstrap build_admintheme build_survey_theme_fruity build_survey_theme_fruity_twentythree)
    fi
    yarn gulp "${gulp_tasks[@]}"
    # The editor is absent on older upstream commits. Its tracked npm lock is
    # recovered with the exact source checkout and must remain unchanged.
    if [[ -f editor/package.json ]]; then
      npm --prefix editor ci --no-audit --no-fund
      npm --prefix editor run build
    fi
    git diff --exit-code -- composer.lock yarn.lock assets/packages/adminbasics/yarn.lock editor/package-lock.json
    php <<'PHP'
<?php
    define('BASEPATH', '.');
    $defaults = require 'application/config/config-defaults.php';
    $email = require 'application/config/email.php';
    $config = require 'application/config/config-sample-mysql.php';
    $config['components']['db']['connectionString'] = 'mysql:host=mariadb;port=3306;dbname=limesurvey;';
    $config['components']['db']['username'] = 'limesurvey';
    $config['components']['db']['password'] = 'limesurvey';
    $config['components']['urlManager']['urlFormat'] = 'path';
    $config['config'] += [
        'defaultuser' => $defaults['defaultuser'],
        'defaultpass' => $defaults['defaultpass'],
        'siteadminemail' => $email['siteadminemail'],
        'defaulthtmleditormode' => 'none',
        'editorEnabled' => true,
    ];
    file_put_contents('application/config/config.php', "<?php\nreturn " . var_export($config, true) . ";\n");
PHP
    mkdir -p tmp/runtime tmp/assets upload
    # Native install and demo reset supply upstream accounts and surveys on a fresh database.
    if ! mariadb -h mariadb -u limesurvey -plimesurvey limesurvey -Nse "SELECT stg_value FROM lime_settings_global WHERE stg_name='DBVersion'" >/dev/null 2>&1; then
      php application/commands/console.php installfromconfig application/config/config.php verbose
      php application/commands/console.php demomode yes
    fi
    chown -R www-data:www-data tmp upload
    ;;
  start) exec apache2ctl -D FOREGROUND ;;
  ready)
    curl --fail --silent --show-error http://localhost:8000/index.php/admin/authentication/sa/login >/dev/null
    mariadb -h mariadb -u limesurvey -plimesurvey limesurvey -Nse "SELECT stg_value FROM lime_settings_global WHERE stg_name='DBVersion'" | python3 -c 'import sys; assert int(sys.stdin.read().strip()) > 0'
    ;;
  *) exit 2 ;;
esac
