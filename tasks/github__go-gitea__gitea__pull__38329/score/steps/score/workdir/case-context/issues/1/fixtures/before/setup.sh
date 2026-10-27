#!/usr/bin/env bash
set -euo pipefail
fixture_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
bash "$fixture_dir/cleanup.sh"
runtime=/tmp/gitea-actions-status
mkdir -p "$runtime/custom/conf" "$runtime/data" "$runtime/repositories"
cat > "$runtime/custom/conf/app.ini" <<'INI'
APP_NAME = Gitea
RUN_USER = git
RUN_MODE = prod
WORK_PATH = /tmp/gitea-actions-status
[database]
DB_TYPE = sqlite3
PATH = /tmp/gitea-actions-status/data/gitea.db
[repository]
ROOT = /tmp/gitea-actions-status/repositories
DEFAULT_BRANCH = main
[server]
HTTP_ADDR = 0.0.0.0
HTTP_PORT = 3001
ROOT_URL = http://localhost:3001/
STATIC_ROOT_PATH = /workspace/app
DISABLE_SSH = true
[security]
INSTALL_LOCK = true
[service]
ENABLE_CAPTCHA = false
DISABLE_REGISTRATION = true
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
chown -R git:git "$runtime"
runuser -u git -- /workspace/app/gitea --work-path "$runtime" --config "$runtime/custom/conf/app.ini" migrate > "$runtime/migrate.log" 2>&1
runuser -u git -- /workspace/app/gitea --work-path "$runtime" --config "$runtime/custom/conf/app.ini" admin user create --username morgan --password 'RiverStone47!' --email morgan@example.test --fullname Morgan --admin --must-change-password=false > "$runtime/user.log" 2>&1
runuser -u git -- bash -c 'nohup setsid /workspace/app/gitea --work-path /tmp/gitea-actions-status --config /tmp/gitea-actions-status/custom/conf/app.ini web > /tmp/gitea-actions-status/server.log 2>&1 < /dev/null & echo $! > /tmp/gitea-actions-status/server.pid'
for _ in {1..100}; do
  if curl --silent --fail http://localhost:3001/api/healthz >/dev/null; then break; fi
  sleep 0.2
done
curl --silent --show-error --fail http://localhost:3001/api/healthz >/dev/null
python3 - <<'PYSETUP'
import base64, json, time, urllib.request
root = 'http://localhost:3001/api/v1'
auth = base64.b64encode(b'morgan:RiverStone47!').decode()
def request(method, path, data=None):
    req = urllib.request.Request(root + path, data=json.dumps(data).encode() if data is not None else None, method=method,
      headers={'Authorization': 'Basic ' + auth, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        content = response.read()
        return json.loads(content) if content else None
request('POST', '/user/repos', {'name': 'build-checks', 'description': 'Repository build checks', 'auto_init': True, 'default_branch': 'main'})
workflow = """name: Build checks
on: [push, workflow_dispatch]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check project
        run: echo "Project checks complete"
"""
request('POST', '/repos/morgan/build-checks/contents/.gitea/workflows/checks.yml', {
    'content': base64.b64encode(workflow.encode()).decode(), 'message': 'Add project build checks', 'branch': 'main'})
# Resolve runs from the repository just created, never from a persisted runtime ID.
for _ in range(100):
    runs = request('GET', '/repos/morgan/build-checks/actions/runs')['workflow_runs']
    if runs:
        break
    time.sleep(0.2)
else:
    raise RuntimeError('Workflow run was not created by the native repository push event')
if len(runs) != 1 or runs[0]['status'] not in ('waiting', 'queued'):
    raise RuntimeError('Expected one waiting workflow run: ' + repr(runs))
PYSETUP
