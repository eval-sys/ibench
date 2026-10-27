# iBench

iBench evaluates how coding agents repair interaction problems in existing
applications. This repository contains the CLI, 44 tasks, and model configurations.

## Setup

```bash
uv sync --locked
cp .env.example .env
bash scripts/build-dev-images.sh
uv run ibench check .
```

Add solver and scorer credentials to `.env`. The example below uses
`OPENAI_API_KEY` and `DEEPSEEK_API_KEY`. Edit the files in `configs/` to choose
other models or endpoints.

## Run

```bash
uv run ibench run \
  --task photo-map-panning \
  --solver-config configs/gpt-6-astra-high.json \
  --score-config configs/deepseek-flash.json \
  --output jobs/example \
  --n-concurrent 2
```

Repeat `--task` to select tasks; omit it to run all 44. Task names and IDs are
listed in `tasks/release.json`. Add `--profile intent-actions` to include
interaction steps alongside the default user goal.

Resume an interrupted run:

```bash
uv run ibench resume jobs/example
```

To defer scoring, run with `--solver-only`, then score the collected patches:

```bash
uv run ibench score jobs/example \
  --config configs/deepseek-flash.json --n-concurrent 2
```

## Inspect

Preview tasks and videos at `http://127.0.0.1:8090`:

```bash
uv run ibench preview --no-open
```

View results and trajectories:

```bash
uv run harbor view jobs/example/jobs
```

See `uv run ibench --help` for debugging, recording, and other commands. Use the
[audit-cases skill](.agents/skills/audit-cases/SKILL.md) to review task quality.

## License

Original iBench code and benchmark material use Apache-2.0. Third-party material
retains its own terms. See [LICENSE](LICENSE), [NOTICE](NOTICE), and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
