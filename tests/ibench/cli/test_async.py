import subprocess
import sys
from pathlib import Path


def test_termination_runs_async_cleanup(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import asyncio
import os
import signal
from pathlib import Path
import typer
from ibench.cli.audit import run_async

async def operation():
    try:
        asyncio.get_running_loop().call_soon(os.kill, os.getpid(), signal.SIGTERM)
        await asyncio.Event().wait()
    finally:
        Path('cleanup.txt').write_text('released environment')

try:
    run_async(operation())
except typer.Exit as error:
    raise SystemExit(error.exit_code)
""",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 143, result.stderr
    assert (tmp_path / "cleanup.txt").read_text() == "released environment"
