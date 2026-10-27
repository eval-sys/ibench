import asyncio
import signal
from collections.abc import Awaitable
from pathlib import Path
from typing import Annotated

import typer

from ibench.services.audit import run_debug, run_replay


def run_async[T](operation: Awaitable[T]) -> T:
    """Let SDK finally blocks run when a foreground CLI receives SIGTERM."""

    async def guarded() -> T:
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        previous = signal.getsignal(signal.SIGTERM)
        loop.add_signal_handler(signal.SIGTERM, task.cancel)
        try:
            return await operation
        finally:
            loop.remove_signal_handler(signal.SIGTERM)
            signal.signal(signal.SIGTERM, previous)

    try:
        return asyncio.run(guarded())
    except asyncio.CancelledError as error:
        raise typer.Exit(143) from error


def debug(
    task: Annotated[str, typer.Argument(help="Task id or name.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="New session directory.")],
    path: Annotated[Path, typer.Option("--path", "-p")] = Path("."),
    revision: Annotated[str, typer.Option(help="base, merged, or full SHA.")] = "merged",
    patch: Annotated[Path | None, typer.Option(help="Patch applied to base; requires --revision base.")] = None,
    fixture: Annotated[str, typer.Option(help="before or reference-after.")] = "reference-after",
    scripts: Annotated[Path | None, typer.Option(help="Collected script bundle with issues/<n>/ directories.")] = None,
    cases: Annotated[list[str] | None, typer.Option("--case", help="Full case id; repeat to select.")] = None,
) -> None:
    """Start a SleepAgent environment; use Docker to debug. Ctrl-C saves scripts and closes it."""
    try:
        run_async(
            run_debug(
                path,
                task,
                output,
                revision=revision,
                patch=patch,
                fixture=fixture,
                scripts=scripts,
                cases=tuple(cases) if cases else None,
            )
        )
    except (ValueError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error


def replay(
    task: Annotated[str, typer.Argument(help="Task id or name.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="New attempt directory, never overwritten.")],
    path: Annotated[Path, typer.Option("--path", "-p")] = Path("."),
    revision: Annotated[str, typer.Option(help="base, merged, or full SHA.")] = "merged",
    patch: Annotated[Path | None, typer.Option(help="Patch applied to base; requires --revision base.")] = None,
    fixture: Annotated[str, typer.Option(help="before or reference-after.")] = "reference-after",
    scripts: Annotated[Path | None, typer.Option(help="Saved script bundle with issues/<n>/ directories.")] = None,
    cases: Annotated[list[str] | None, typer.Option("--case", help="Full case id; repeat to select.")] = None,
) -> None:
    """Record with the published trusted replay in a fresh environment; no Require judge."""
    try:
        result = run_async(
            run_replay(
                path,
                task,
                output,
                revision=revision,
                patch=patch,
                fixture=fixture,
                scripts=scripts,
                cases=tuple(cases) if cases else None,
            )
        )
    except (ValueError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    typer.echo(f"Replay {'passed' if result.success else 'failed'}. Results: {result.output / 'results.json'}")
    typer.echo("Capture/protocol only; Require has not been judged.")
    if not result.success:
        if result.error:
            typer.echo(result.error, err=True)
        raise typer.Exit(1)
