#!/usr/bin/env bash
set -euo pipefail
# Oppia uses a physical directory name and a sibling tool directory.
if [[ "$1" == setup && ! -L /workspace/app ]]; then
  mv /workspace/app /workspace/oppia
  ln -s oppia /workspace/app
fi
cd /workspace/oppia
case "$(sed -n 's/^runtime: *//p' app_dev.yaml)" in
  python310) ln -sfn /opt/oppia-python-310 /opt/oppia-python ;;
  python312) ln -sfn /opt/oppia-python-312 /opt/oppia-python ;;
  *) echo "Unsupported Oppia Python runtime in app_dev.yaml" >&2; exit 1 ;;
esac
export PATH="/opt/oppia-python/bin:/opt/oppia-tools/node-16.13.0/bin:/opt/oppia-tools/yarn-1.22.15/bin:/opt/java/bin:$PATH"
case "${1:?setup, start or ready required}" in
  setup)
    python -c 'from scripts import install_third_party_libs; install_third_party_libs.test_python_version()'
    ln -sfn /opt/oppia-tools /workspace/oppia_tools
    python -m pip install --require-hashes --no-deps -r requirements_dev.txt
    python -m pip install --require-hashes --no-deps --target third_party/python_libs -r requirements.txt --upgrade
    # SDK startup creates its own venv. Supply the same hashed artifacts locally.
    python -m pip download --require-hashes --no-deps -r requirements.txt -d /workspace/runtime-packages
    python -m pip download --no-deps pip==25.3 setuptools==80.9.0 wheel==0.45.1 -d /workspace/runtime-packages
    PATH="/opt/oppia-tools/node-20.11.1/bin:$PATH" yarn install --frozen-lockfile --non-interactive
    python /opt/oppia-runtime.py build
    git diff --exit-code -- yarn.lock requirements.txt requirements_dev.txt
    ;;
  start) exec python -u /opt/oppia-runtime.py start ;;
  ready) exec python /opt/oppia-runtime.py ready ;;
  *) exit 2 ;;
esac
