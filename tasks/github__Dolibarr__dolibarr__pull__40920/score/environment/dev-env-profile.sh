#!/usr/bin/env bash
set -euo pipefail
case "${1:?expected setup or start}" in
  setup)
    python3 /opt/vendor-lock.py "${DEV_ENV_LOCK_MODE:-resolve}"
    source_root="$PWD"
    mkdir -p /var/lib/dolibarr/documents /var/lib/dolibarr/sessions htdocs/conf
    # The native CLI installer owns conf.php and its application defaults.
    touch htdocs/conf/conf.php
    (
      cd htdocs/install
      php step1.php set en_US "$source_root/htdocs" /var/lib/dolibarr/documents \
        http://localhost:8000 '' '' mysqli mariadb dolibarr dolibarr local-development 3306 llx_ 0 0
    )
    cat > /root/.my.cnf <<EOF
[client]
host=mariadb
EOF
    chmod 600 /root/.my.cnf
    # Use native reload and its supported DIALOG frontend override in this disposable DB.
    dump="$(find dev/initdemo -maxdepth 1 -name 'mysqldump_dolibarr_*.sql' | sort -V | tail -1)"
    test -n "$dump"
    DIALOG=/bin/true bash dev/initdemo/initdemo.sh confirm "$(basename "$dump")" dolibarr 3306 root local-root-password
    # A shipped major-version demo can precede this checkout's maintenance release.
    dump_version="$(basename "$dump" .sql)"
    dump_version="${dump_version#mysqldump_dolibarr_}"
    app_version="$(php -r 'require "htdocs/filefunc.inc.php"; echo DOL_VERSION;')"
    if [ "$dump_version" != "$app_version" ]; then
      (
        cd htdocs/install
        php upgrade.php "$dump_version" "$app_version"
        php upgrade2.php "$dump_version" "$app_version"
        php step5.php "$dump_version" "$app_version"
      )
    fi
    mariadb -h mariadb -u dolibarr -plocal-development dolibarr -e 'SELECT COUNT(*) FROM llx_user' > /dev/null
    touch /var/lib/dolibarr/documents/install.lock
    chown -R www-data:www-data /var/lib/dolibarr htdocs/conf
    cat > /etc/apache2/sites-available/dolibarr.conf <<EOF
<VirtualHost *:8000>
    ServerName localhost
    DocumentRoot $source_root/htdocs
    <Directory $source_root/htdocs>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    ErrorLog /var/log/apache2/error.log
    CustomLog /var/log/apache2/access.log combined
</VirtualHost>
EOF
    a2ensite dolibarr > /dev/null
    apache2ctl configtest
    ;;
  start)
    exec apache2ctl -D FOREGROUND
    ;;
  *) exit 2 ;;
esac
