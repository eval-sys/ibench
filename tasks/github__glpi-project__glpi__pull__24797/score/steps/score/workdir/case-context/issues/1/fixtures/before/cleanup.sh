#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mariadb --host=mariadb --user=glpi --password=glpi glpi < "$fixture_dir/cleanup.sql"
