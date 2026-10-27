#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# This checkout uses MariaDB, so execute its fixed fixture SQL with the native CLI.
bash "$fixture_dir/cleanup.sh"
mariadb --host=mariadb --user=glpi --password=glpi glpi < "$fixture_dir/setup.sql"
