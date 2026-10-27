#!/usr/bin/env bash
set -euo pipefail
fixture_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
bash "$fixture_dir/cleanup.sh"
# Use native document creation and user actions, rather than constructing SQLite rows.
python3 - <<'PYTHON'
import json, os, re, urllib.request, urllib.error
from pathlib import Path
# Automatic boot authentication is supported by Authorizer.ts. Resolve the current
# startup credential; never persist a generated key or a generated document ID.
keys = re.findall(r"BOOT KEY: ([a-f0-9]+)", Path('/logs/artifacts/tasks/github__gristlabs__grist-core__pull__2298/runtime/service.log').read_text())
if not keys:
    raise RuntimeError('No current Grist boot credential in the service log')
def api(path, method='GET', data=None):
    request = urllib.request.Request(os.environ['APP_URL'].rstrip('/') + path, method=method,
        headers={'x-boot-key': keys[-1], 'Content-Type': 'application/json'},
        data=None if data is None else json.dumps(data).encode())
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode()
        return json.loads(text) if text else None
user = api('/api/session/access/active')['user']
if user['email'] != 'you@example.com':
    raise RuntimeError('Expected the upstream default account you@example.com')
org = next(o for o in api('/api/orgs') if o.get('owner', {}).get('id') == user['id'])
workspaces = api('/api/orgs/' + str(org['id']) + '/workspaces')
workspace = next(w for w in workspaces if w['name'] == 'Home')
doc = api('/api/docs', 'POST', {'workspaceId': workspace['id'], 'documentName': 'Widget Layout'})
base = '/api/docs/' + doc
api(base, 'PATCH', {'urlId': 'widget-layout-page-copy'})
views = api(base + '/tables/_grist_Views/data')
sections = api(base + '/tables/_grist_Views_section/data')
view = views['id'][0]
left = next(section for section, parent in zip(sections['id'], sections['parentId']) if parent == view)
table = sections['tableRef'][sections['id'].index(left)]
api(base + '/apply', 'POST', [
    ['RenameTable', 'Table1', 'Items'],
    ['UpdateRecord', '_grist_Views', view, {'name': 'Overview'}],
    ['UpdateRecord', '_grist_Views_section', left, {'title': 'Left'}],
])
right = api(base + '/apply', 'POST', [
    ['CreateViewSection', table, view, 'record', None, None]
])['retValues'][0]['sectionRef']
# This is the saved layout produced by collapsing Left via its visible widget menu.
layout = {'children': [{'leaf': right}], 'collapsed': [{'leaf': left}]}
api(base + '/apply', 'POST', [
    ['UpdateRecord', '_grist_Views_section', right, {'title': 'Right'}],
    ['UpdateRecord', '_grist_Views', view, {'layoutSpec': json.dumps(layout)}],
])
# Give guests editor access to this issue-owned document only. Browser setup can
# use the real public editor without changing the installation's login defaults.
api(base + '/access', 'PATCH', {'delta': {'users': {'everyone@getgrist.com': 'editors'}}})
PYTHON
