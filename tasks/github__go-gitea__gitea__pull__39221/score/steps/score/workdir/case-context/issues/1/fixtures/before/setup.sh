#!/usr/bin/env bash
set -euo pipefail

bash "$(dirname "${BASH_SOURCE[0]}")/cleanup.sh"
issue_runtime=/tmp/gitea-secret-naming
install -d -o git -g git "$issue_runtime" "$issue_runtime/custom" "$issue_runtime/custom/conf"

# The shared service has no database and disables Actions. Isolate these missing preconditions.
cat > "$issue_runtime/custom/conf/app.ini" <<'INI'
APP_NAME = Gitea
RUN_USER = git
RUN_MODE = prod
WORK_PATH = /tmp/gitea-secret-naming

[database]
DB_TYPE = sqlite3
PATH = /tmp/gitea-secret-naming/data/gitea.db

[repository]
ROOT = /tmp/gitea-secret-naming/repositories

[server]
HTTP_ADDR = 0.0.0.0
HTTP_PORT = 3001
ROOT_URL = http://localhost:3001/
STATIC_ROOT_PATH = /workspace/app
DISABLE_SSH = true

[security]
INSTALL_LOCK = false

[service]
ENABLE_CAPTCHA = false

[mailer]
ENABLED = false

[actions]
ENABLED = true

[cron]
ENABLED = false

[log]
MODE = console
LEVEL = Info
INI
chown git:git "$issue_runtime/custom/conf/app.ini"

python3 - <<'PY'
import subprocess
with open('/tmp/gitea-secret-naming/application.log', 'ab', buffering=0) as log:
    subprocess.Popen([
        'runuser', '-u', 'git', '--', '/workspace/app/gitea',
        '--work-path', '/tmp/gitea-secret-naming',
        '--config', '/tmp/gitea-secret-naming/custom/conf/app.ini', 'web',
    ], stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
PY

for attempt in {1..100}; do
  if curl --fail --silent --output /dev/null http://localhost:3001/; then break; fi
  sleep 0.1
done
curl --fail --silent --show-error --output "$issue_runtime/install-response.html" http://localhost:3001/ \
  --data-urlencode db_type=sqlite3 \
  --data-urlencode db_path=/tmp/gitea-secret-naming/data/gitea.db \
  --data-urlencode app_name=Gitea \
  --data-urlencode repo_root_path=/tmp/gitea-secret-naming/repositories \
  --data-urlencode run_user=git \
  --data-urlencode domain=localhost \
  --data-urlencode ssh_port=0 \
  --data-urlencode http_port=3001 \
  --data-urlencode app_url=http://localhost:3001/ \
  --data-urlencode log_root_path=/tmp/gitea-secret-naming/log \
  --data-urlencode enable_open_id_sign_in=on \
  --data-urlencode enable_open_id_sign_up=on \
  --data-urlencode default_allow_create_organization=on \
  --data-urlencode default_enable_timetracking=on \
  --data-urlencode no_reply_address=noreply.localhost \
  --data-urlencode password_algorithm=pbkdf2

python3 - <<'PY'
import json
import time
import urllib.request
for _ in range(100):
    try:
        with urllib.request.urlopen('http://localhost:3001/api/healthz', timeout=2) as response:
            data = json.load(response)
        if data['status'] == 'pass' and 'database:ping' in data.get('checks', {}):
            break
    except (OSError, ValueError):
        pass
    time.sleep(0.1)
else:
    raise RuntimeError('Gitea installation did not become ready')
PY

runuser -u git -- /workspace/app/gitea \
  --work-path "$issue_runtime" --config "$issue_runtime/custom/conf/app.ini" \
  admin user create --username casey --email casey@example.test \
  --password 'RiverStone!482' --must-change-password=false
