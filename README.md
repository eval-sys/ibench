# iBench

iBench evaluates coding agents on interaction problems in existing applications.
This repository contains the CLI, 44 benchmark tasks, model configurations, and
an audit skill for reviewing task definitions and execution evidence.

## Setup

Use Linux with Docker Engine, Docker Compose v2, Git, and uv. The project uses
Python 3.12–3.14; Python 3.13 is used in CI. Docker must be accessible to the
user running the CLI. Task setup downloads the pinned upstream repositories and
application dependencies.

```bash
uv sync --locked
cp .env.example .env
bash scripts/build-dev-images.sh
uv run ibench check .
```

Fill in the credentials needed by your solver and scorer in `.env`. The CLI
loads this file automatically; existing environment variables take precedence.
Credentials in job configurations use environment-variable references.

The build script creates `ibench-dev:20261011-1` from `environments/base/`.
Every task depends on this local image, which includes Chrome, agent-browser,
and the verifier tools. Build it on each machine that runs tasks.

## Run a task

This example uses Astra High through Codex as the solver, and DeepSeek Flash
through Codex as the scorer. Set `OPENAI_API_KEY` and `DEEPSEEK_API_KEY` first.
For an OpenAI-compatible solver endpoint, also set `OPENAI_BASE_URL`.

```bash
uv run ibench run \
  --task photo-map-panning \
  --solver-config configs/gpt-6-astra-high.json \
  --score-config configs/deepseek-flash.json \
  --output jobs/example \
  --n-concurrent 2
```

Task selection accepts the public `name` or stable `id` in
`tasks/release.json`. Repeat `--task` for a subset, or omit it for all tasks.
The default instruction profile, `intent`, provides the user's goal.
`--profile intent-actions` also provides the recorded interaction steps.

Available solver configurations:

| Configuration | Harness | Credential variable |
| --- | --- | --- |
| `configs/gpt-6-astra-high.json` | Codex | `OPENAI_API_KEY` |
| `configs/claude-opus-5-5-high.json` | Claude Code | `CLAUDE_CODE_OAUTH_TOKEN` |
| `configs/kimi-k3-high.json` | Kimi Code | `FIREWORKS_API_KEY` |
| `configs/glm-5.3-flash-high.json` | ZCode | `GLM_API_KEY` |
| `configs/deepseek-flash-dsh-high.json` | DSH | `DEEPSEEK_API_KEY` |
| `configs/qwen3.8-max-high.json` | Codex | `QWEN_API_KEY` |

Model and harness versions are pinned in the configurations. Adapt model names,
provider endpoints, concurrency, and credentials to your available services.
`--n-concurrent` overrides concurrency for both solve and score.

## Score and resume

Add `--solver-only` to `ibench run` to collect patches and defer scoring:

```bash
uv run ibench score jobs/example \
  --config configs/deepseek-flash.json --n-concurrent 2
```

Continue an interrupted run with:

```bash
uv run ibench resume jobs/example
```

Completed trials are reused. Interrupted trials restart from their task inputs;
resume does not continue an agent from an arbitrary point in its conversation.
To replace an existing score job and grade all collected candidates again, use
`ibench score jobs/example --overwrite`.

Each run contains frozen inputs, two native Harbor jobs, and runner state:

```text
jobs/example/
├── compiled/solve/
├── compiled/score/
├── jobs/solve/
├── jobs/score/
├── run.json
└── results.json
```

The solver's committed changes are collected as `candidate.patch`. The scorer
starts a fresh environment with that patch and evaluates the published cases.
`repair` describes whether the repair meets the acceptance criteria; `protocol`
describes whether the required verification protocol was followed.

## Preview and inspect

```bash
uv run ibench preview --no-open
uv run harbor view jobs/example/jobs
```

The task preview serves at `http://127.0.0.1:8090` by default. It includes task
definitions, scripts, before/reference-after videos, and video guides. Read
markers are stored in the browser. Harbor's viewer displays runtime jobs and
agent trajectories.

## Debug and record

Start a task environment without a solver or judge:

```bash
uv run ibench debug photo-map-panning --output jobs/map-debug
```

Keep the command running and use the printed Docker project and container
details to inspect the application. Ctrl-C saves edited replay fixtures and
cleans up the session. Record saved scripts in a fresh environment:

```bash
uv run ibench replay photo-map-panning \
  --scripts jobs/map-debug/edited-scripts --output jobs/map-replay
```

Both commands accept `--revision base`, `merged` (default), or a full commit SHA.
`--patch FILE` applies a patch to `--revision base`. Use `--fixture before` for
the reproduction fixtures; the default is `reference-after`.

Replay verifies capture and protocol integrity. It does not judge the repair
requirements. To evaluate the reference repair with a real scorer:

```bash
uv run ibench oracle photo-map-panning \
  --agent codex --config configs/deepseek-flash.json
```

Oracle uses `reference.patch` when provided by the task, otherwise its pinned
merge commit. Published task files are not modified by these commands.

## Resource calibration

```bash
uv run ibench profile-resources --task photo-map-panning \
  --output jobs/resources --n-concurrent 1
```

Calibration uses the scripted Oracle without a model or scorer. It records CPU
and memory samples inside task containers during setup, agent execution, and
verification. Docker image builds and the host runner are excluded. This
command requires Linux Docker with cgroup v2. Normal runs do not collect these
resource samples.

## Upload results

```bash
uv run harbor auth login
uv run ibench upload jobs/example --dry-run
uv run ibench upload jobs/example --public
```

Uploads are private by default. Pass multiple run paths to upload several jobs.
The uploaded solver trajectories receive the corresponding scorer's repair
reward. Failed attempts, including empty patches and scorer failures, receive
`reward = repair = protocol = 0`. Execution-only endpoint fields are removed
from upload configurations by field. Source run files are unchanged.

## Develop and audit

```bash
uv sync --locked --group dev
uv run pytest
uv run ruff check src tests
```

Preview assets are checked in. Rebuild them after changing styles or vendor
dependencies:

```bash
npm ci
npm run build:assets
```

The [audit-cases skill](.agents/skills/audit-cases/SKILL.md) includes self-contained
definition, replay, and rollout rules, with examples in its `experiences/`
directory. Review natural-language definitions before replay or trajectory
evidence. New audit records are local outputs; historical audit reports and
model runs are not included in this repository.

## License

Original iBench code and benchmark material use Apache-2.0. Referenced projects
and bundled third-party material retain their own terms. See [LICENSE](LICENSE),
[NOTICE](NOTICE), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
