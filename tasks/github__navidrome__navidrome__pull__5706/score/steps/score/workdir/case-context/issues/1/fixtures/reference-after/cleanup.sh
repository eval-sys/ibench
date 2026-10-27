#!/usr/bin/env bash
set -euo pipefail
# Keep the empty directory until the targeted scan marks its tracks missing.
fixture_music=/tmp/navidrome-runtime/music/composer-studies
mkdir -p "$fixture_music"
rm -f "$fixture_music/01-amber.flac" "$fixture_music/02-blue.flac" \
  "$fixture_music/03-cedar.flac" "$fixture_music/04-dawn.flac"
/workspace/app/navidrome scan --full --target 1:composer-studies \
  --datafolder /tmp/navidrome-runtime/data --musicfolder /tmp/navidrome-runtime/music
# Resolve IDs on every run; never delete all missing files or persist tokens.
python3 - <<'PYTHON'
import json
import os
from urllib.request import Request, urlopen
from urllib.parse import urlencode
base = os.environ.get('APP_URL', 'http://localhost:4533').rstrip('/')
login = Request(base + '/auth/login', data=json.dumps({
    'username': 'admin', 'password': 'admin123'
}).encode(), headers={'Content-Type': 'application/json'})
with urlopen(login, timeout=30) as response:
    token = json.load(response)['token']
headers = {'X-ND-Authorization': 'Bearer ' + token}
query = urlencode({'path': 'composer-studies/', '_start': 0, '_end': 100})
with urlopen(Request(base + '/api/missing?' + query, headers=headers), timeout=30) as response:
    records = json.load(response)
owned_paths = {'composer-studies/' + name for name in (
    '01-amber.flac', '02-blue.flac', '03-cedar.flac', '04-dawn.flac')}
ids = [row['id'] for row in records if row['path'] in owned_paths and row['missing']]
if ids:
    query = urlencode([('id', value) for value in ids])
    with urlopen(Request(base + '/api/missing?' + query, method='DELETE', headers=headers), timeout=30) as response:
        response.read()
PYTHON
rmdir "$fixture_music"
