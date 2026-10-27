#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import subprocess
import urllib.error
import urllib.request

page = urllib.request.urlopen('http://localhost:3000/').read().decode()
if 'name="db_type"' in page:
    raise SystemExit(0)
try:
    urllib.request.urlopen('http://localhost:3000/api/v1/users/morgan-code')
except urllib.error.HTTPError as error:
    if error.code == 404:
        raise SystemExit(0)
    raise
subprocess.run(['runuser', '-u', 'git', '--', '/workspace/app/gitea',
    '--work-path', '/tmp/gitea-runtime', '--config', '/tmp/gitea-runtime/custom/conf/app.ini',
    'admin', 'user', 'delete', '--username', 'morgan-code', '--purge'], check=True)
PY
