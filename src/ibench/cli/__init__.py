from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from ibench.cli import audit, release, runner, upload

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
app.command()(audit.debug)
app.command()(audit.replay)
app.command()(release.check)
app.command()(runner.oracle)
app.command()(runner.run)
app.command()(runner.score)
app.command()(runner.resume)
app.command()(runner.profile_resources)
app.command()(release.preview)
app.command()(upload.upload)


@app.callback()
def main(
    env_file: Annotated[Path, typer.Option(help="Load credentials from this file; existing environment wins.")] = Path(
        ".env"
    ),
) -> None:
    """Tools for published IBench releases."""
    load_dotenv(env_file, override=False)
