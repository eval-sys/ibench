from pathlib import Path
from typing import Annotated

import typer

from ibench.services.preview import serve_preview
from ibench.services.release import check_release


def check(
    path: Annotated[
        Path,
        typer.Argument(help="Release repository root containing tasks/release.json."),
    ] = Path("."),
) -> None:
    """Check a published release without running its environments."""

    result = check_release(path)
    if result.issues:
        typer.echo(f"Release check failed with {len(result.issues)} issue(s):", err=True)
        for issue in result.issues:
            typer.echo(f"- {issue}", err=True)
        raise typer.Exit(code=1)
    assert result.release is not None
    typer.echo(f"Checked {len(result.release.tasks)} task(s) in {result.release.name}@{result.release.version}.")


def preview(
    path: Annotated[Path, typer.Option("--path", "-p", help="Release repository root.")] = Path("."),
    task: Annotated[str | None, typer.Option("--task", "-t", help="Only show one task.")] = None,
    host: Annotated[str, typer.Option(help="Address to bind.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to bind.", min=1, max=65535)] = 8090,
    open_browser: Annotated[bool, typer.Option("--open/--no-open", help="Open the preview in a browser.")] = True,
) -> None:
    """Browse published tasks and preview every case in a task."""

    try:
        serve_preview(path, task_id=task, host=host, port=port, open_browser=open_browser)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
