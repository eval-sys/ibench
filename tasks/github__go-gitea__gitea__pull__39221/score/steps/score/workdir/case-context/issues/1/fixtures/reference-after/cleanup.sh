#!/usr/bin/env bash
set -euo pipefail

# Only the instance using this issue's work path is owned by this fixture.
python3 - <<'PY'
import os
from pathlib import Path
import signal
import time

runtime = Path('/tmp/gitea-runtime')
for entry in Path('/proc').iterdir():
    if not entry.name.isdigit():
        continue
    try:
        args = (entry / 'cmdline').read_bytes().split(b'\0')
        owned = (args[0] == b'/workspace/app/gitea'
                 and b'--work-path' in args
                 and args[args.index(b'--work-path') + 1] == str(runtime).encode())
        if not owned:
            continue
        pid = int(entry.name)
        os.kill(pid, signal.SIGTERM)
        for _ in range(100):
            if not entry.exists() or (entry / 'stat').read_text().split()[2] == 'Z':
                break
            time.sleep(0.1)
        else:
            raise RuntimeError('The isolated Gitea instance did not stop')
    except (FileNotFoundError, ProcessLookupError):
        pass
PY
rm -rf /tmp/gitea-runtime
