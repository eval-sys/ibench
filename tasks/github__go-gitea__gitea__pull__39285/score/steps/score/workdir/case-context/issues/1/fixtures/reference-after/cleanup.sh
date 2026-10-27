#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import subprocess
import os
import urllib.error
import urllib.request

base = os.environ.get('APP_URL', 'http://localhost:3000').rstrip('/')
page = urllib.request.urlopen(base + '/').read().decode()
if 'name="db_type"' in page:
    raise SystemExit(0)
try:
    urllib.request.urlopen(base + '/api/v1/users/morgan-code')
except urllib.error.HTTPError as error:
    if error.code == 404:
        raise SystemExit(0)
    raise
subprocess.run(['runuser', '-u', 'git', '--', '/workspace/app/gitea',
    '--work-path', '/tmp/gitea-runtime', '--config', '/tmp/gitea-runtime/custom/conf/app.ini',
    'admin', 'user', 'delete', '--username', 'morgan-code', '--purge'], check=True)
PY
