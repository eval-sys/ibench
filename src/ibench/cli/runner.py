from pathlib import Path
from typing import Annotated

import typer

from ibench.modules.harbor import configure_job
from ibench.services.runner import RunResult, read_run, resume_run, run_oracle, run_release, score_run


def oracle(
    task_id: Annotated[str, typer.Argument(help="Published task id to calibrate.")],
    agent: Annotated[str, typer.Option("--agent", "-a", help="Real Harbor agent used by the score task.")],
    path: Annotated[Path, typer.Option("--path", "-p", help="Release repository root.")] = Path("."),
    model: Annotated[str | None, typer.Option("--model", "-m")] = None,
    jobs_dir: Annotated[Path, typer.Option("--jobs-dir", "-o")] = Path("jobs"),
    environment: Annotated[str | None, typer.Option("--env", "-e")] = None,
    config: Annotated[Path | None, typer.Option("--config", help="Native Harbor JobConfig JSON for scoring.")] = None,
) -> None:
    """Run a published score task against its known-good merge commit."""

    try:
        result = run_oracle(
            path,
            task_id,
            agent=agent,
            model=model,
            jobs_dir=jobs_dir,
            environment=environment,
            config_path=config,
        )
    except (ValueError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Oracle passed with reward {result.reward}. Harbor job: {result.job_path}")


def _report(result: RunResult) -> None:
    typer.echo(f"Run {result.phase}. Results: {result.output / 'results.json'}")
    if not result.success:
        typer.echo("Some trials failed or have no score; inspect results.json.", err=True)
        raise typer.Exit(code=1)


def run(
    output: Annotated[Path, typer.Option("--output", "-o", help="New run directory.")],
    path: Annotated[Path, typer.Option("--path", "-p", help="Release repository root.")] = Path("."),
    tasks: Annotated[
        list[str] | None, typer.Option("--task", "-t", help="Task id or name; repeat to select tasks.")
    ] = None,
    profile: Annotated[str | None, typer.Option(help="Instruction profile: intent or intent-actions.")] = None,
    solver_agent: Annotated[str | None, typer.Option(help="Solver agent; defaults to codex.")] = None,
    solver_model: Annotated[str | None, typer.Option()] = None,
    score_agent: Annotated[str | None, typer.Option(help="Score agent; defaults to codex.")] = None,
    score_model: Annotated[str | None, typer.Option()] = None,
    solver_config: Annotated[Path | None, typer.Option(help="Native Harbor JobConfig JSON for solving.")] = None,
    score_config: Annotated[Path | None, typer.Option(help="Native Harbor JobConfig JSON for scoring.")] = None,
    environment: Annotated[str | None, typer.Option("--env", "-e", help="Harbor backend; defaults to docker.")] = None,
    n_concurrent: Annotated[int | None, typer.Option("--n-concurrent", "-n", min=1)] = None,
    n_attempts: Annotated[int | None, typer.Option(min=1, help="Solver attempts per task.")] = None,
    solver_retries: Annotated[int | None, typer.Option(min=0)] = None,
    score_retries: Annotated[int | None, typer.Option(min=0)] = None,
    solver_only: Annotated[bool, typer.Option(help="Stop after collecting patches; score or resume later.")] = False,
) -> None:
    """Compile selected tasks, solve them, and score each candidate with the Harbor SDK."""
    try:
        solver = configure_job(
            solver_config,
            agent=solver_agent,
            model=solver_model,
            environment=environment,
            n_concurrent=n_concurrent,
            n_attempts=n_attempts,
            retries=solver_retries,
        )
        scorer = configure_job(
            score_config,
            agent=score_agent,
            model=score_model,
            environment=environment,
            n_concurrent=n_concurrent,
            retries=score_retries,
            scoring=True,
        )
        result = run_release(
            path,
            output,
            solver=solver,
            scorer=scorer,
            selections=tuple(tasks) if tasks else None,
            profile=profile,
            solver_only=solver_only,
        )
    except (ValueError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    _report(result)


def score(
    output: Annotated[Path, typer.Argument(help="Existing IBench run directory.")],
    overwrite: Annotated[bool, typer.Option(help="Replace the existing score job and grade all candidates again.")] = False,
    agent: Annotated[str | None, typer.Option("--agent", "-a")] = None,
    model: Annotated[str | None, typer.Option("--model", "-m")] = None,
    config: Annotated[Path | None, typer.Option(help="Native Harbor JobConfig JSON for scoring.")] = None,
    environment: Annotated[str | None, typer.Option("--env", "-e")] = None,
    n_concurrent: Annotated[int | None, typer.Option("--n-concurrent", "-n", min=1)] = None,
    retries: Annotated[int | None, typer.Option(min=0)] = None,
) -> None:
    """Score a run in place using its frozen tasks, without rerunning the solver."""
    try:
        scorer = configure_job(
            config,
            base=read_run(output).scorer,
            agent=agent,
            model=model,
            environment=environment,
            n_concurrent=n_concurrent,
            retries=retries,
            scoring=True,
        )
        result = score_run(output, scorer=scorer, overwrite=overwrite)
    except (ValueError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    _report(result)


def profile_resources(
    output: Annotated[Path, typer.Option("--output", "-o", help="New resource calibration directory.")],
    path: Annotated[Path, typer.Option("--path", "-p", help="Release repository root.")] = Path("."),
    tasks: Annotated[list[str] | None, typer.Option("--task", "-t", help="Task id or name; repeat to select.")] = None,
    n_concurrent: Annotated[int, typer.Option("--n-concurrent", "-n", min=1)] = 1,
) -> None:
    """Measure setup/build resources with Oracle only, without a model or scorer."""
    from ibench.services.resources import profile_resources as run_profile

    try:
        report = run_profile(path, output, selections=tuple(tasks) if tasks else None, n_concurrent=n_concurrent)
    except (ValueError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Oracle resource profile completed. Report: {report}")


def resume(
    output: Annotated[Path, typer.Argument(help="Existing IBench run directory containing run.json.")],
    solver_only: Annotated[bool, typer.Option(help="Stop at the solve/score boundary.")] = False,
) -> None:
    """Resume the current Harbor job and continue remaining phases."""
    try:
        result = resume_run(output, solver_only=solver_only)
    except (ValueError, OSError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    _report(result)
