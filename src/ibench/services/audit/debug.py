from __future__ import annotations

import asyncio
import contextlib
import tempfile
from pathlib import Path

from harbor.environments.docker.docker import DockerEnvironment
from harbor.trial.trial import Trial

from ibench.agents.sleep import SleepAgent
from ibench.modules.harbor import trial_error
from ibench.services.audit.inputs import AuditInput, copy_scripts, prepare_audit, write_json


class DebugDockerEnvironment(DockerEnvironment):
    """Defer Harbor teardown, including failed setup, to the session owner."""

    async def stop(self, delete: bool) -> None:
        pass

    async def close(self) -> None:
        await super().stop(delete=True)


class DebugSession:
    """One live SDK environment; async context exit saves scripts and cleans up."""

    def __init__(self, audit: AuditInput, trial: Trial):
        self.audit, self.trial = audit, trial
        self.environment = trial.agent_environment
        self.status = "starting"
        self.error: str | None = None
        self.worker = asyncio.create_task(trial.run())

    @classmethod
    async def create(
        cls,
        root: Path,
        selection: str,
        output: Path,
        *,
        revision: str = "merged",
        patch: Path | None = None,
        fixture: str = "reference-after",
        scripts: Path | None = None,
        cases: tuple[str, ...] | None = None,
    ) -> DebugSession:
        audit = prepare_audit(
            root, selection, output, revision=revision, patch=patch, fixture=fixture, scripts=scripts, cases=cases
        )
        trial = await Trial.create(audit.trial_config(debug=True))
        return cls(audit, trial)

    async def _wait_ready(self) -> bool:
        agent = self.trial.agent
        assert isinstance(agent, SleepAgent)
        ready = asyncio.create_task(agent.ready.wait())
        try:
            await asyncio.wait({ready, self.worker}, return_when=asyncio.FIRST_COMPLETED)
            if self.worker.done():
                if self.status in ("closing", "closed"):
                    return False
                self.error = trial_error(self.worker.result()) or "trial ended before debugging was ready"
                self.status = "setup_failed"
                return False
            for case in self.audit.cases:
                await self.environment.upload_dir(self.audit.scripts / self.audit.case_key(case), case.replay_root)
            self.status = "ready"
            return True
        finally:
            ready.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await ready

    async def _close(self) -> None:
        if self.status == "closed":
            return
        prepared = self.status in ("ready", "trial_ended")
        self.status = "closing"
        try:
            if prepared:
                # Save current scripts before Harbor archives its live artifact mount.
                with tempfile.TemporaryDirectory(prefix="ibench-collect-") as temporary:
                    staging = Path(temporary)
                    for index, case in enumerate(self.audit.cases):
                        downloaded = staging / str(index)
                        await self.environment.download_dir(case.replay_root, downloaded)
                        copy_scripts(downloaded, self.audit.output / "edited-scripts" / self.audit.case_key(case))
                identity = await self.environment.exec(
                    "git rev-parse HEAD && git status --porcelain",
                    cwd="/workspace/app",
                    user="root",
                    timeout_sec=30,
                )
                write_json(
                    self.audit.output / "edited-scripts/collection.json",
                    {
                        "task_id": self.audit.task.id,
                        "revision": self.audit.revision,
                        "case_ids": [c.case_id for c in self.audit.cases],
                        "workspace": {
                            "stdout": identity.stdout,
                            "stderr": identity.stderr,
                            "return_code": identity.return_code,
                        },
                    },
                )
        except Exception as error:
            self.error = f"could not save edited scripts: {error}"
            (self.audit.output / "collection-error.txt").write_text(self.error + "\n")
        finally:
            self.trial.agent.release.set()
            try:
                await asyncio.wait_for(self.worker, timeout=60)
            except TimeoutError:
                self.worker.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self.worker
            # Failed trials collected before debug edits; retain their final logs too.
            try:
                await self.environment.exec("chmod -R a+rwX /logs/artifacts", user="root", timeout_sec=30)
                await self.environment.download_dir("/logs/artifacts", self.audit.output / "closed-artifacts")
            except Exception as error:
                (self.audit.output / "collection-error.txt").write_text(str(error) + "\n")
            await self.environment.close()
            self.status = "closed"

    async def __aenter__(self) -> DebugSession:
        try:
            await self._wait_ready()
        except BaseException:
            await self._close()
            raise
        return self

    async def __aexit__(self, *exc) -> None:
        await self._close()


async def run_debug(root: Path, selection: str, output: Path, **options) -> None:
    session = await DebugSession.create(root, selection, output, **options)
    state = {
        "publication": str(root.resolve()),
        "status": "starting",
        "error": None,
        "trial": str(session.trial.paths.trial_dir),
        "docker_project": session.environment.session_id,
    }

    def save_state() -> None:
        state.update(status=session.status, error=session.error)
        write_json(session.audit.output / "session.json", state)

    save_state()
    print(f"Debug session: {session.audit.output} (starting)", flush=True)
    try:
        async with session:
            save_state()
            print(f"Debug {session.status}. {session.error or ''}", flush=True)
            print(f"docker ps --filter label=com.docker.compose.project={session.environment.session_id}", flush=True)
            print("Use docker exec / docker cp. Ctrl-C saves scripts and closes this environment.", flush=True)
            for case in session.audit.cases:
                print(f"Replay scripts: {case.replay_root}", flush=True)
            await asyncio.shield(session.worker)
            if session.status == "ready":
                session.error = trial_error(session.worker.result()) or "debug trial ended"
                session.status = "trial_ended"
                save_state()
            await asyncio.Event().wait()
    finally:
        save_state()
        print(f"Debug closed. Artifacts: {session.audit.output}", flush=True)
        if (session.audit.output / "edited-scripts/collection.json").exists():
            print(f"Saved replay scripts: {session.audit.output / 'edited-scripts'}", flush=True)
        if session.error and (session.audit.output / "collection-error.txt").exists():
            raise ValueError(session.error)
