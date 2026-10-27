#!/usr/bin/env bash
set -euo pipefail
# Only this issue's document (including its copied page) is removed.
python3 - <<'PYTHON'
import json, re, urllib.request, urllib.error
from pathlib import Path
# Automatic boot authentication is supported by Authorizer.ts. Resolve the current
# startup credential; never persist a generated key or a generated document ID.
keys = re.findall(r"BOOT KEY: ([a-f0-9]+)", Path('/logs/artifacts/tasks/github__gristlabs__grist-core__pull__2298/runtime/service.log').read_text())
if not keys:
    raise RuntimeError('No current Grist boot credential in the service log')
def api(path, method='GET', data=None):
    request = urllib.request.Request('http://localhost:8484' + path, method=method,
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
for doc in workspace['docs']:
    if doc.get('urlId') == 'widget-layout-page-copy' or doc['name'] == 'Widget Layout':
        if doc['name'] != 'Widget Layout':
            raise RuntimeError('The reserved document URL belongs to another document')
        api('/api/docs/' + doc['id'], 'DELETE')
PYTHON
