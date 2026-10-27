"""Freeze dependencies shipped in Git without resolving replacement packages."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

roots = ["htdocs/includes", "htdocs/public/includes", "htdocs/theme/common", "composer.json.disabled"]
subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *roots], check=True)
paths = subprocess.check_output(["git", "ls-files", "-z", "--", *roots]).decode().split("\0")
manifest = {
    "schema_version": "dolibarr-vendored-dependencies/v1",
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "files": {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in sorted(paths) if path},
}
if not manifest["files"]:
    raise SystemExit("No vendored dependencies found in the checkout")
lock = Path(".vendor-dependencies.lock.json")
exclude = Path(subprocess.check_output(["git", "rev-parse", "--git-path", "info/exclude"], text=True).strip())
exclude.parent.mkdir(parents=True, exist_ok=True)
if not exclude.exists() or lock.name not in exclude.read_text().splitlines():
    with exclude.open("a") as stream:
        stream.write("\n" + lock.name + "\n")
if sys.argv[1] == "resolve":
    lock.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
elif sys.argv[1] == "restore":
    frozen = json.loads(lock.read_text())
    if any(frozen.get(key) != manifest[key] for key in ("schema_version", "files")):
        raise SystemExit("Frozen vendored dependencies do not match this checkout")
else:
    raise SystemExit("Expected resolve or restore")
print(f"Verified {len(manifest['files'])} vendored dependency files at {manifest['source_commit']}")
