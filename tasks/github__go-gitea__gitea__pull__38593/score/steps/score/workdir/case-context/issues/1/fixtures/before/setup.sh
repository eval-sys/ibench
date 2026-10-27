#!/usr/bin/env bash
set -euo pipefail

# The environment profile starts an uninstalled SQLite instance. Use its native
# installer once, submitting its current defaults (and preserving disabled SSH).
python3 - <<'PYTHON'
import configparser
import json
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

cfg = configparser.ConfigParser(interpolation=None)
with open('/tmp/gitea-runtime/custom/conf/app.ini') as config_file:
    cfg.read_string('[DEFAULT]\n' + config_file.read())
if not cfg.getboolean('security', 'INSTALL_LOCK', fallback=False):
    class InstallDefaults(HTMLParser):
        def __init__(self):
            super().__init__()
            self.fields = {}
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag != 'input' or 'name' not in attrs:
                return
            if attrs.get('type') == 'checkbox' and 'checked' not in attrs:
                return
            self.fields[attrs['name']] = attrs.get('value', 'on' if attrs.get('type') == 'checkbox' else '')
    parser = InstallDefaults()
    with urllib.request.urlopen('http://localhost:3000/', timeout=30) as response:
        parser.feed(response.read().decode())
    assert parser.fields.get('db_type') == 'sqlite3', 'Unexpected installation surface'
    if cfg.getboolean('server', 'DISABLE_SSH', fallback=False):
        parser.fields['ssh_port'] = '0'
    request = urllib.request.Request('http://localhost:3000/', data=urllib.parse.urlencode(parser.fields).encode())
    with urllib.request.urlopen(request, timeout=60) as response:
        response.read()
    for attempt in range(60):
        try:
            with urllib.request.urlopen('http://localhost:3000/api/v1/version', timeout=2) as response:
                assert json.load(response).get('version')
            break
        except Exception:
            time.sleep(0.5)
    else:
        raise RuntimeError('Gitea installation did not become ready')
PYTHON

# Recreate only this issue's account and repository, even after an interrupted run.
bash "$(dirname "${BASH_SOURCE[0]}")/cleanup.sh"
runuser -u git -- /workspace/app/gitea \
  --work-path /tmp/gitea-runtime \
  --config /tmp/gitea-runtime/custom/conf/app.ini \
  admin user create --username release-coordinator --fullname 'Release Coordinator' \
  --email release-coordinator@example.test --password 'ReleasePlan42!' \
  --must-change-password=false

python3 - <<'PYTHON'
import base64
import json
import urllib.request

# All IDs are returned by the current native API setup, never saved between runs.
auth = base64.b64encode(b'release-coordinator:ReleasePlan42!').decode()
headers = {'Authorization': 'Basic ' + auth, 'Content-Type': 'application/json'}
with urllib.request.urlopen(urllib.request.Request(
        'http://localhost:3000/api/v1/user/repos',
        data=json.dumps({'name': 'release-planning', 'description': 'Release planning and review', 'private': False}).encode(),
        headers=headers), timeout=30) as response:
    repo = json.load(response)
assert repo['owner']['login'] == 'release-coordinator'
issues = []
for title, body in [
    ('Prepare release notes', 'Complete release review before closing this work.'),
    ('Publish release', 'Complete release review before closing this work.'),
    ('Complete release review', 'Review remains open and blocks the release tasks.'),
]:
    with urllib.request.urlopen(urllib.request.Request(
            'http://localhost:3000/api/v1/repos/release-coordinator/release-planning/issues',
            data=json.dumps({'title': title, 'body': body}).encode(), headers=headers), timeout=30) as response:
        issue = json.load(response)
    assert issue['state'] == 'open'
    issues.append(issue)
for target in issues[:2]:
    with urllib.request.urlopen(urllib.request.Request(
            'http://localhost:3000/api/v1/repos/release-coordinator/release-planning/issues/' + str(target['number']) + '/dependencies',
            data=json.dumps({'owner': 'release-coordinator', 'repo': 'release-planning', 'index': issues[2]['number']}).encode(),
            headers=headers), timeout=30) as response:
        json.load(response)
print('Created two open release tasks, both blocked by an open release review.')
PYTHON
