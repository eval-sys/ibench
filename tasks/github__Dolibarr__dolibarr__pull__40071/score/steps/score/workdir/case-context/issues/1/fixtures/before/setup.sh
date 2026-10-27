#!/usr/bin/env bash
set -euo pipefail
# No issue-owned server state: reuse the immutable demo loaded by
# /opt/dev-env-profile.sh through dev/initdemo/initdemo.sh.
# MariaDB is the application database; no PostgreSQL fixture is required.
true
