"""Frozen setup and separate lifecycle using Oppia's native build/server APIs."""

import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import yaml

sys.path.insert(0, os.getcwd())
from scripts import common, install_third_party_libs

common.require_cwd_to_be_oppia()
install_third_party_libs.test_python_version()


def build():
    # The SDK is image tooling; namespace integration is checkout preparation.
    google = Path(common.THIRD_PARTY_PYTHON_LIBS_DIR) / "google"
    for name in ("appengine", "pyglib"):
        target = google / name
        if not target.exists():
            shutil.copytree(Path(common.GOOGLE_APP_ENGINE_SDK_HOME) / "google" / name, target)
    install_third_party_libs.make_google_module_importable_by_python(str(google))
    from scripts import build as native

    # Native generate_python_package also recompiles and reinstalls dependencies.
    # Keep its archive command; let this checkout's Main own the build lifecycle.
    native.generate_python_package = lambda: subprocess.run(
        [sys.executable, "setup.py", "-q", "sdist", "-d", "build"], check=True
    )
    native.main(["--prod_env"])
    # App Engine isolates the app environment from the launcher's environment.
    config_path = Path("app.yaml")
    config = yaml.safe_load(config_path.read_text())
    config["env_variables"].update(REDIS_HOST=os.environ["REDIS_HOST"], ES_HOST=os.environ["ES_HOST"])
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))


def start():
    from core import feconf

    from scripts import servers

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    with contextlib.ExitStack() as stack:
        processes = [
            stack.enter_context(servers.managed_firebase_auth_emulator(recover_users=True)),
            stack.enter_context(servers.managed_cloud_datastore_emulator(clear_datastore=False)),
        ]
        env = dict(
            os.environ,
            PIP_NO_DEPS="True",
            PIP_NO_INDEX="True",
            PIP_FIND_LINKS="/workspace/runtime-packages",
            PIP_CONSTRAINT="/opt/runtime-tooling-constraints.txt",
        )
        processes.append(
            stack.enter_context(
                servers.managed_dev_appserver(
                    "app.yaml",
                    env=env,
                    automatic_restart=False,
                    skip_sdk_update_check=True,
                    port=feconf.GAE_DEVELOPMENT_SERVER_PORT,
                )
            )
        )
        while all(p.poll() is None for p in processes):
            time.sleep(1)
        raise RuntimeError("An application service exited")


def ready():
    subprocess.run(["redis-cli", "-h", os.environ["REDIS_HOST"], "ping"], check=True, stdout=subprocess.DEVNULL)
    with urllib.request.urlopen(
        "http://" + os.environ["ES_HOST"] + ":9200/_cluster/health?wait_for_status=yellow", timeout=5
    ) as response:
        assert json.load(response)["status"] in ("yellow", "green")
    with urllib.request.urlopen("http://localhost:9099/", timeout=5) as response:
        assert json.load(response)["authEmulator"]["ready"] is True
    with urllib.request.urlopen("http://localhost:8089/", timeout=5) as response:
        assert response.status == 200
    with urllib.request.urlopen("http://localhost:8181/", timeout=15) as response:
        assert response.status == 200
    with urllib.request.urlopen("http://localhost:8181/csrfhandler", timeout=15) as response:
        assert response.status == 200


{"build": build, "start": start, "ready": ready}[sys.argv[1]]()
