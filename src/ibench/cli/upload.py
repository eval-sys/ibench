import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

import typer

from ibench.services.upload import prepare_upload, upload_plan


def upload(
    runs: Annotated[list[Path], typer.Argument(help="Completed IBench run directories; repeat to upload multiple runs.")],
    public: Annotated[bool, typer.Option("--public/--private", help="Uploaded job visibility.")] = False,
    org: Annotated[str | None, typer.Option(help="Owning Harbor organization; defaults to your personal org.")] = None,
    concurrency: Annotated[int, typer.Option("--concurrency", "-c", min=1, help="Concurrent trial uploads.")] = 10,
    dry_run: Annotated[bool, typer.Option(help="Prepare and validate upload copies without contacting Harbor.")] = False,
) -> None:
    """Upload solver trajectories with scorer repair rewards and standardized job names."""
    try:
        plans = [upload_plan(run) for run in runs]
        if len({plan.result.id for plan in plans}) != len(plans):
            raise ValueError("The same Harbor job was selected more than once")
        if len({plan.name for plan in plans}) != len(plans):
            raise ValueError("Selected runs produce duplicate upload names; upload them separately")
        for plan in plans:
            with TemporaryDirectory(prefix="ibench-upload-") as temporary:
                job = prepare_upload(plan, Path(temporary))
                typer.echo(json.dumps({
                    **plan.summary(), "visibility": "public" if public else "private",
                    "org": org or "personal",
                }))
                if not dry_run:
                    from harbor.cli.upload import upload_command

                    upload_command(
                        job, concurrency=concurrency, public=public, org=org,
                        debug=False, share_org=None, share_user=None, yes=False,
                    )
    except (ValueError, OSError, RuntimeError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
