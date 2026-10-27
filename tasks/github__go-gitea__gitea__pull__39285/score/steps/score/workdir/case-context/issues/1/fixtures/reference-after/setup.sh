#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import base64
import configparser
from html.parser import HTMLParser
import json
import subprocess
import os
import time
import urllib.error
import urllib.parse
import urllib.request

base = os.environ.get('APP_URL', 'http://localhost:3000').rstrip('/')
config_path = '/tmp/gitea-runtime/custom/conf/app.ini'
username = 'morgan-code'
password = 'BranchTabs39285!'
cli = ['runuser', '-u', 'git', '--', '/workspace/app/gitea', '--work-path', '/tmp/gitea-runtime', '--config', config_path]

class InstallForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'input' and a.get('name') and 'disabled' not in a:
            if a.get('type') in ('checkbox', 'radio') and 'checked' not in a:
                return
            self.values[a['name']] = a.get('value', 'on' if a.get('type') == 'checkbox' else '')

# The environment profile starts uninstalled. Use Gitea's installer once,
# retaining its form defaults and the profile's disabled SSH/LFS services.
page = urllib.request.urlopen(base + '/').read().decode()
if 'name="db_type"' in page:
    form = InstallForm()
    form.feed(page)
    cfg = configparser.ConfigParser()
    cfg.read_string('[DEFAULT]\n' + open(config_path).read())
    if cfg.getboolean('server', 'DISABLE_SSH', fallback=False):
        form.values['ssh_port'] = '0'
    if not cfg.getboolean('server', 'LFS_START_SERVER', fallback=False):
        form.values['lfs_root_path'] = ''
    request = urllib.request.Request(base + '/', data=urllib.parse.urlencode(form.values).encode())
    result = urllib.request.urlopen(request, timeout=90).read().decode()
    if 'name="db_type"' in result:
        raise RuntimeError('Gitea installer did not complete')

for attempt in range(60):
    try:
        urllib.request.urlopen(base + '/api/v1/version', timeout=2)
        break
    except (urllib.error.URLError, ConnectionError):
        time.sleep(0.5)
else:
    raise RuntimeError('Gitea did not become ready after installation')

def api(method, path, payload=None):
    auth = base64.b64encode((username + ':' + password).encode()).decode()
    headers = {'Content-Type': 'application/json'}
    if not path.startswith('/users/'):
        headers['Authorization'] = 'Basic ' + auth
    request = urllib.request.Request(base + '/api/v1' + path, method=method,
        headers=headers,
        data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, b''
        raise

status, _ = api('GET', '/users/' + username)
if status == 404:
    subprocess.run(cli + ['admin', 'user', 'create', '--username', username,
        '--password', password, '--email', 'morgan-code@example.org',
        '--fullname', 'Morgan', '--must-change-password=false'], check=True)
status, _ = api('GET', '/repos/' + username + '/project-notes')
if status == 404:
    api('POST', '/user/repos', {'name': 'project-notes', 'description': 'Project notes',
        'private': False, 'auto_init': True, 'default_branch': 'main', 'readme': 'Default'})
print('Repository ready: morgan-code/project-notes (main)')
PY
