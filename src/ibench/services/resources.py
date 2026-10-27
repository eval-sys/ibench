from __future__ import annotations

import asyncio
import json
import math
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from harbor.environments.docker.docker import DockerEnvironment, _sanitize_docker_compose_project_name
from harbor.trial.hooks import TrialHookEvent


def _counters(path: Path) -> dict[str, int]:
    return {key: int(value) for key, value in (line.split() for line in path.read_text().splitlines())}


def read_usage(cgroup: Path) -> dict:
    cpu = _counters(cgroup / "cpu.stat")
    memory = int((cgroup / "memory.current").read_text())
    peak = cgroup / "memory.peak"
    return {
        "cpu_usage_usec": cpu["usage_usec"],
        "cpu_throttled_usec": cpu.get("throttled_usec", 0),
        "cpu_throttled_periods": cpu.get("nr_throttled", 0),
        "memory_bytes": memory,
        "working_set_bytes": max(0, memory - _counters(cgroup / "memory.stat").get("inactive_file", 0)),
        "memory_kernel_peak_bytes": int(peak.read_text()) if peak.exists() else None,
        "oom_kills": _counters(cgroup / "memory.events").get("oom_kill", 0),
    }


def summarize_samples(samples: list[dict]) -> dict:
    cpu = sorted(sample["cpu_cores"] for sample in samples)
    return {
        "samples": len(samples),
        "cpu_peak_cores": max(cpu, default=0),
        "cpu_p95_cores": cpu[math.ceil(len(cpu) * 0.95) - 1] if cpu else 0,
        "memory_sampled_peak_bytes": max((s["memory_bytes"] for s in samples), default=0),
        "working_set_sampled_peak_bytes": max((s["working_set_bytes"] for s in samples), default=0),
    }


async def resource_phase(event: TrialHookEvent) -> None:
    phase = {"environment-start": "setup", "agent-start": "agent", "agent-end": "verification"}[event.event.value]
    directory = event.config.trials_dir / event.trial_name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "resource-phase.json").write_text(
        json.dumps(
            {
                "phase": phase,
                "task_name": event.task_name,
                "task_path": str(event.config.task.path),
            }
        )
    )


class ResourceDockerEnvironment(DockerEnvironment):
    """Sample local cgroup v2 counters; flush before Docker deletes the cgroups."""

    async def start(self, force_build: bool) -> None:
        if not Path("/sys/fs/cgroup/cgroup.controllers").exists():
            raise ValueError("Resource profiling requires a local Linux Docker daemon with cgroup v2")
        self._resource_stop = asyncio.Event()
        self._resource_containers: dict[str, dict] = {}
        self._resource_samples: list[dict] = []
        self._resource_errors: set[str] = set()
        self._resource_worker = asyncio.create_task(self._watch_resources())
        await super().start(force_build)

    async def _docker(self, *args: str) -> str:
        process = await asyncio.create_subprocess_exec(
            "docker",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
        if process.returncode:
            raise RuntimeError(stderr.decode().strip())
        return stdout.decode()

    async def _sample_resources(self) -> None:
        ids = (
            await self._docker(
                "ps",
                "--filter",
                f"label=com.docker.compose.project={_sanitize_docker_compose_project_name(self.session_id)}",
                "--format",
                "{{.ID}}",
            )
        ).split()
        timestamp, monotonic = datetime.now(UTC).isoformat(), time.monotonic()
        phase_path = self.trial_paths.trial_dir / "resource-phase.json"
        identity = json.loads(phase_path.read_text()) if phase_path.exists() else {"phase": "setup"}
        measurements = {}
        for container_id in ids:
            if container_id not in self._resource_containers:
                details = json.loads(
                    await self._docker(
                        "inspect",
                        "--format",
                        (
                            '{"pid":{{.State.Pid}},"service":"{{index .Config.Labels "com.docker.compose.service"}}",'
                            '"cpu_nano":{{.HostConfig.NanoCpus}},"cpu_quota":{{.HostConfig.CpuQuota}},'
                            '"cpu_period":{{.HostConfig.CpuPeriod}},"memory_limit_bytes":{{.HostConfig.Memory}}}'
                        ),
                        container_id,
                    )
                )
                groups = Path(f"/proc/{details['pid']}/cgroup").read_text().splitlines()
                group = next(line.removeprefix("0::") for line in groups if line.startswith("0::"))
                details.update(cgroup=Path("/sys/fs/cgroup") / group.lstrip("/"), samples=[], previous=None)
                self._resource_containers[container_id] = details
            container = self._resource_containers[container_id]
            try:
                usage = read_usage(container["cgroup"])
            except FileNotFoundError:
                # A service may exit between discovery and reading its counters.
                continue
            previous = container["previous"]
            cores = (
                max(0, (usage["cpu_usage_usec"] - previous[0]) / ((monotonic - previous[1]) * 1e6)) if previous else 0
            )
            container["previous"] = (usage["cpu_usage_usec"], monotonic)
            sample = {"timestamp": timestamp, "phase": identity["phase"], "cpu_cores": cores, **usage}
            container["samples"].append(sample)
            measurements[container_id] = {"service": container["service"], **sample}
        if measurements:
            total = {
                "timestamp": timestamp,
                **identity,
                **{
                    key: sum(s[key] for s in measurements.values())
                    for key in (
                        "cpu_cores",
                        "memory_bytes",
                        "working_set_bytes",
                    )
                },
                "containers": measurements,
            }
            self._resource_samples.append(total)
            with (self.trial_paths.trial_dir / "resource-samples.jsonl").open("a") as output:
                output.write(json.dumps(total) + "\n")

    async def _watch_resources(self) -> None:
        while not self._resource_stop.is_set():
            try:
                await self._sample_resources()
            except Exception as error:
                self._resource_errors.add(str(error))
            try:
                await asyncio.wait_for(self._resource_stop.wait(), timeout=1)
            except TimeoutError:
                pass

    async def stop(self, delete: bool) -> None:
        try:
            if hasattr(self, "_resource_worker"):
                self._resource_stop.set()
                await self._resource_worker
                try:
                    await self._sample_resources()
                except Exception as error:
                    self._resource_errors.add(str(error))
                self._save_resources()
                del self._resource_worker
        finally:
            await super().stop(delete)

    def _save_resources(self) -> None:
        if not self._resource_samples:
            self._resource_errors.add("No cgroup samples collected; check local Docker access and container discovery")
        containers = {}
        for container_id, container in self._resource_containers.items():
            samples = container["samples"]
            quota, period = container["cpu_quota"], container["cpu_period"]
            containers[container_id] = {
                "service": container["service"],
                "cpu_limit_cores": container["cpu_nano"] / 1e9 or (quota / period if quota > 0 and period else None),
                "memory_limit_bytes": container["memory_limit_bytes"] or None,
                **summarize_samples(samples),
                **{
                    key: max((s[key] or 0 for s in samples), default=0)
                    for key in (
                        "cpu_usage_usec",
                        "cpu_throttled_usec",
                        "cpu_throttled_periods",
                        "oom_kills",
                    )
                },
                "memory_kernel_peak_bytes": max(
                    (s["memory_kernel_peak_bytes"] for s in samples if s["memory_kernel_peak_bytes"] is not None),
                    default=None,
                ),
                "phases": {
                    phase: summarize_samples([s for s in samples if s["phase"] == phase])
                    for phase in ("setup", "agent", "verification")
                },
            }
        report = {
            "schema_version": "ibench-resource-usage/v1",
            "docker_project": self.session_id,
            "status": "partial" if self._resource_errors or not self._resource_samples else "complete",
            "errors": sorted(self._resource_errors),
            "sample_interval_sec": 1,
            "scope": "trial containers; excludes Docker image builds and host runner",
            "host_cpus": len(os.sched_getaffinity(0)),
            "containers": containers,
            "total": summarize_samples(self._resource_samples),
            "phases": {
                phase: summarize_samples([s for s in self._resource_samples if s["phase"] == phase])
                for phase in ("setup", "agent", "verification")
            },
        }
        identity = self.trial_paths.trial_dir / "resource-phase.json"
        if identity.exists():
            report.update({key: value for key, value in json.loads(identity.read_text()).items() if key != "phase"})
        (self.trial_paths.trial_dir / "resource-usage.json").write_text(json.dumps(report, indent=2) + "\n")


def summarize_job_resources(job_path: Path) -> None:
    trials = [
        dict(trial=path.parent.name, **json.loads(path.read_text()))
        for path in sorted(job_path.glob("*/resource-usage.json"))
    ]
    tasks = {}
    for trial in trials:
        name = trial.get("task_name", trial["trial"])
        task = tasks.setdefault(name, {"trials": [], "cpu_peak_cores": 0, "memory_sampled_peak_bytes": 0})
        task["trials"].append(trial["trial"])
        for key in ("cpu_peak_cores", "memory_sampled_peak_bytes"):
            task[key] = max(task[key], trial["total"][key])
    (job_path / "resource-usage.json").write_text(
        json.dumps(
            {
                "schema_version": "ibench-job-resource-usage/v1",
                "tasks": tasks,
                "trials": trials,
            },
            indent=2,
        )
        + "\n"
    )


def profile_resources(
    root: Path,
    output: Path,
    *,
    selections: tuple[str, ...] | None = None,
    n_concurrent: int = 1,
) -> Path:
    from harbor.models.job.config import JobConfig

    from ibench.modules.harbor import require_finished, run_job, trial_error, trials
    from ibench.services.release.compiler import load_release, prepare_solve

    root, output = root.resolve(), output.resolve()
    manifest = load_release(root, selections)
    if output.exists() or output.is_relative_to(root / "tasks"):
        raise ValueError("resource output must be a new directory outside the published tasks")
    output.mkdir(parents=True)
    compiled = []
    for task in manifest.tasks:
        directory = prepare_solve(
            root, task, output / "compiled" / task.id, manifest.default_instruction_profile
        )
        solution = directory / "steps/solve/solution"
        solution.mkdir()
        (solution / "solve.sh").write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\n"
            "# Setup already installed/built the app and checked that it is ready.\n"
            "test -d /workspace/app/.git\n"
            "test -s /logs/artifacts/solver/runtime/prepared-commit-sha.txt\n"
        )
        compiled.append({"path": directory})
    config = JobConfig(
        job_name="oracle",
        jobs_dir=output / "jobs",
        tasks=compiled,
        agents=[{"name": "oracle"}],
        environment={"type": "docker"},
        n_concurrent_trials=n_concurrent,
        n_attempts=1,
        retry={"max_retries": 0},
    )
    result = asyncio.run(run_job(config, collect_resources=True))
    require_finished(result)
    job_path = output / "jobs/oracle"
    for directory, trial in trials(job_path):
        if error := trial_error(trial):
            raise ValueError(f"Oracle setup/build failed: {error}; inspect {directory}")
        report = json.loads((directory / "resource-usage.json").read_text())
        if report["status"] != "complete":
            raise ValueError(f"incomplete resource collection; inspect {directory / 'resource-usage.json'}")
    return job_path / "resource-usage.json"
