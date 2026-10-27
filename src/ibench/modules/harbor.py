from __future__ import annotations

import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

from harbor.job import Job
from harbor.models.job.config import JobConfig
from harbor.models.job.result import JobResult
from harbor.models.trial.result import TrialResult
from harbor.trial.hooks import TrialEvent
from harbor.utils.env import is_env_template, is_sensitive_env_key, resolve_env_vars, templatize_sensitive_env

from ibench.modules.run_paths import read_trial, relocate_job


def configure_job(
    config_path: Path | None = None,
    *,
    base: JobConfig | None = None,
    agent: str | None = None,
    model: str | None = None,
    environment: str | None = None,
    n_concurrent: int | None = None,
    n_attempts: int | None = None,
    retries: int | None = None,
    scoring: bool = False,
) -> JobConfig:
    config = (
        JobConfig.model_validate_json(config_path.read_bytes())
        if config_path
        else base.model_copy(deep=True) if base is not None else JobConfig(agents=[{"name": "codex"}])
    )
    if len(config.agents) != 1 or config.user_agent is not None:
        raise ValueError("IBench runs require exactly one agent per phase and no simulated user")
    settings = config.agents[0]
    if agent is not None:
        settings.name, settings.import_path = agent, None
    if model is not None:
        settings.model_name = model
    if scoring and settings.name == "oracle":
        raise ValueError("Harbor's oracle agent runs solution/solve.sh and cannot run the real score agent")
    if config.install_only or config.verifier.disable:
        raise ValueError("IBench runs require agent execution and trusted verification")
    if settings.name == "codex":
        for target, candidates in {
            "OPENAI_API_KEY": ("OPENAI_API_KEY", "CODEX_API_KEY"),
            "OPENAI_BASE_URL": ("OPENAI_BASE_URL", "CODEX_API_BASE", "CODEX_BASE_URL"),
        }.items():
            key = next((key for key in candidates if os.getenv(key)), None)
            if key:
                settings.env.setdefault(target, "${" + key + "}")
        endpoint = settings.env.get("OPENAI_BASE_URL", "https://api.openai.com")
        host = urlparse(resolve_env_vars({"endpoint": endpoint})["endpoint"]).hostname
        if host and host not in settings.extra_allowed_hosts:
            settings.extra_allowed_hosts.append(host)
        settings.kwargs.setdefault("web_search", "disabled")
    if environment is not None:
        config.environment = type(config.environment).model_validate(
            {**config.environment.model_dump(), "type": environment, "import_path": None}
        )
    if n_concurrent is not None:
        config.n_concurrent_trials = n_concurrent
    elif config_path is None and base is None:
        config.n_concurrent_trials = 2
    if n_attempts is not None:
        config.n_attempts = n_attempts
    if retries is not None:
        config.retry.max_retries = retries
    for env in [settings.env, config.environment.env, config.verifier.env]:
        persisted = templatize_sensitive_env(env)
        if any(is_sensitive_env_key(key) and not is_env_template(value) for key, value in persisted.items()):
            raise ValueError("use host environment templates such as ${API_KEY} for credentials in job configs")
        env.update(persisted)
    # Revalidate assignments rather than depending on SDK assignment validation.
    return JobConfig.model_validate(config.model_dump())


def trial_error(trial: TrialResult) -> str | None:
    errors = [trial.exception_info, *(step.exception_info for step in trial.step_results or [])]
    error = next((error for error in errors if error), None)
    return f"{error.exception_type}: {error.exception_message}" if error else None


def trial_rewards(trial: TrialResult, phase: str) -> dict[str, float | int]:
    step = next((step for step in trial.step_results or [] if step.step_name == phase), None)
    verifier = step.verifier_result if step else trial.verifier_result
    return verifier.rewards or {} if verifier else {}


def trials(job_path: Path) -> list[tuple[Path, TrialResult]]:
    return [
        (path.parent, read_trial(path))
        for path in sorted(job_path.glob("*/result.json"))
    ]


def require_finished(result: JobResult) -> None:
    stats = result.stats
    if (
        not result.finished_at
        or result.n_total_trials < 1
        or stats.n_completed_trials != result.n_total_trials
        or stats.n_running_trials
        or stats.n_pending_trials
        or stats.n_cancelled_trials
    ):
        raise ValueError("Harbor job is interrupted or incomplete; use ibench resume before scoring")


async def run_job(config: JobConfig, *, collect_resources: bool = False) -> JobResult:
    """Reconcile native jobs; restart unfinished trials without a second archive."""
    job_path = config.jobs_dir / config.job_name
    native_config = job_path / "config.json"
    if native_config.exists():
        for directory in sorted(path for path in job_path.iterdir() if path.is_dir()):
            result_path = directory / "result.json"
            interrupted = not result_path.exists()
            if result_path.exists():
                trial = TrialResult.model_validate_json(result_path.read_bytes())
                interrupted = not trial.finished_at or any(
                    error and error.exception_type == "CancelledError"
                    for error in [trial.exception_info, *(step.exception_info for step in trial.step_results or [])]
                )
            if interrupted:
                shutil.rmtree(directory)
        relocate_job(job_path)
    if collect_resources:
        if (
            any(agent.name != "oracle" or agent.import_path or agent.model_name for agent in config.agents)
            or config.user_agent
        ):
            raise ValueError("Resource calibration requires Oracle agents without a model or scorer")
        resource_environment = "ibench.services.resources:ResourceDockerEnvironment"
        if config.environment.type != "docker" or config.environment.import_path not in (None, resource_environment):
            raise ValueError("Resource profiling currently supports the standard Docker environment only")
        config = config.model_copy(deep=True)
        config.environment.import_path = resource_environment
    job = await Job.create(config)
    if collect_resources:
        from ibench.services.resources import resource_phase, summarize_job_resources

        for event in (TrialEvent.ENVIRONMENT_START, TrialEvent.AGENT_START, TrialEvent.AGENT_END):
            job.add_hook(event, resource_phase)
    try:
        return await job.run()
    finally:
        if collect_resources:
            summarize_job_resources(job_path)
