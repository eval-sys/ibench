![](https://github.com/user-attachments/assets/02cec655-1dbb-435c-b458-8b5fb7edff39)


# Interaction Bench

**Can coding agents figure out why people struggle with interfaces?**

[![Website](https://img.shields.io/badge/Website-ibench.ai-4285F4?style=for-the-badge&logo=google-chrome&logoColor=white)](https://ibench.ai)
[![Leaderboard](https://img.shields.io/badge/Leaderboard-000000?style=for-the-badge&logo=mdbook&color=105864)](https://ibench.ai/leaderboard)
[![Docs](https://img.shields.io/badge/Docs-000000?style=for-the-badge&logo=gitbook&logoColor=white&color=24292F)](https://ibench.ai/docs)
[![Discord](https://img.shields.io/badge/Join_our_discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/AYFPHvv2jT)
[![GitHub](https://img.shields.io/badge/GitHub-eval--sys%2Fibench-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/eval-sys/ibench)

Interaction Bench (**ibench**) evaluates whether coding agents can investigate and repair **interaction defects** in real applications — problems a person feels while using the product, not failures a unit test already catches.

This repository ships the CLI, **44** published tasks across **25** open-source apps, solver/scorer configs, and the harness needed to run reproducible evaluations.

> **v0.1 preview.** On the public [leaderboard](https://ibench.ai/leaderboard), the best reported pass rate is **34.1%** (`GPT-6 Astra`). Scores measure repairs judged against reviewed behavioral requirements in fresh environments — not unit-test green.



## News

- 📣 **27 Oct 2026** — Introduced Interaction Bench: tasks from real open-source maintenance cases, graded from fresh execution evidence. Read the [announcement](https://ibench.ai/blog/introducing-interaction-bench).

---

## What you can do with Interaction Bench

- **Evaluate interaction repair**, not just code that compiles: agents get the user intention, source, and a runnable offline environment — the diagnosed bug and reference fix are withheld.
- **Run real product tasks**: each task comes from a merged pull request that fixed a usability problem in an open-source app (map panning, form feedback, publish toasts, and similar).
- **Grade from behavior**: a separate scoring agent replays the interaction on the patched app and checks expert-defined behavioral requirements; alternate repairs can pass without copying the reference patch.
- **Reproduce end to end**: locked environments, published configs under `configs/`, resume for interrupted runs, and deferred scoring with `--solver-only`.
- **Inspect locally**: preview task intents, rubrics, and reference recordings; view Harbor trajectories after a run.

### What it evaluates

In scope are **usability** problems that show up in use — for example memory demands, unclear feedback, or limited control. Out of scope are appearance-only changes and overall experience ratings. See the [about](https://ibench.ai/about) and [methodology](https://ibench.ai/methodology) pages for the full framing.

### How a run works

1. **Start with a real task** — intent, source, and an offline environment from a real maintenance case.
2. **Investigate and repair** — the agent explores the app and code, decides what should change, and submits a patch.
3. **Judge the repair** — a grading agent recreates the scenario, replays the interaction, and checks the outcome against reviewed requirements.

---

## Leaderboard

Snapshot of the [published leaderboard](https://ibench.ai/leaderboard) as of 29 Oct 2026. Pass rates are measured across all 44 tasks; each result links to its recorded run on Harbor Hub.

| Model | Harness | Pass rate (passed / total) | Harbor Hub |
| --- | --- | ---: | --- |
| GPT-6 Astra | Codex | 34.1% (15/44) | [View run](https://hub.harborframework.com/jobs/f54d076c-070d-5533-92fc-80b403e39c3a) |
| Claude Opus 5.5 | Claude Code | 27.3% (12/44) | [View run](https://hub.harborframework.com/jobs/58add739-5535-5189-9002-8c1a98a9dfe0) |
| DeepSeek Flash | DSH | 15.9% (7/44) | [View run](https://hub.harborframework.com/jobs/23ef15c8-109a-5a90-b83e-49918df1e509) |
| GLM-5.3 Flash | ZCode | 9.1% (4/44) | [View run](https://hub.harborframework.com/jobs/8e9dbe3b-2a3f-57b4-910b-b7ca7e2f6c25) |
| Qwen3.8 Max | Codex | 6.8% (3/44) | [View run](https://hub.harborframework.com/jobs/ee425524-01bf-54f9-b08d-8a55114fed3e) |
| Kimi K3 | Kimi Code | 4.5% (2/44) | [View run](https://hub.harborframework.com/jobs/4e94ddee-4be9-513d-b914-48339687b59f) |

---

## Quickstart

### 1) Clone and install

```bash
git clone https://github.com/eval-sys/ibench.git
cd ibench
uv sync --locked
cp .env.example .env
bash scripts/build-dev-images.sh
uv run ibench check .
```

Add solver and scorer credentials to `.env`. The example uses `OPENAI_API_KEY` and `DEEPSEEK_API_KEY`. Edit files in `configs/` to choose other models or endpoints. Requires Python 3.12+ and Docker for task environments.

### 2) Run a task

```bash
uv run ibench run \
  --task photo-map-panning \
  --solver-config configs/gpt-6-astra-high.json \
  --score-config configs/deepseek-flash.json \
  --output jobs/example \
  --n-concurrent 2
```

Repeat `--task` to select tasks; omit it to run all 44. Task names and IDs are listed in `tasks/release.json`. Add `--profile intent-actions` to include interaction steps alongside the default user goal (`intent`).

### 3) Resume, score later, and inspect

Resume an interrupted run:

```bash
uv run ibench resume jobs/example
```

Defer scoring with `--solver-only`, then score collected patches:

```bash
uv run ibench score jobs/example \
  --config configs/deepseek-flash.json --n-concurrent 2
```

Preview tasks and videos at `http://127.0.0.1:8090`:

```bash
uv run ibench preview --no-open
```

View results and trajectories:

```bash
uv run harbor view jobs/example/jobs
```

See `uv run ibench --help` for debugging, recording, and other commands. Use the [audit-cases skill](.agents/skills/audit-cases/SKILL.md) to review task quality.

---

## Running evaluations

| Goal | Command |
| --- | --- |
| Validate the release | `uv run ibench check .` |
| Run selected / all tasks | `uv run ibench run --output jobs/… --solver-config … --score-config …` |
| Resume a run | `uv run ibench resume jobs/…` |
| Score an existing run | `uv run ibench score jobs/… --config …` |
| Browse tasks locally | `uv run ibench preview` |
| Start an app for inspection | `uv run ibench debug '<task>' --revision base --fixture before --output jobs/…` |
| Replay before / reference-after | `uv run ibench replay '<task>' --revision … --fixture … --output jobs/…` |

Published solver and scorer configs live in `configs/` (for example `gpt-6-astra-high.json`, `deepseek-flash.json`, `claude-opus-5-5-high.json`). Instruction profiles in `tasks/release.json`: `intent` (default) and `intent-actions`.

More detail: [docs quickstart](https://ibench.ai/docs/quickstart) · [task catalog](https://ibench.ai/tasks) · [environments](https://ibench.ai/environments) · [pipeline](https://ibench.ai/pipeline).

---

## Results

- Per-run artifacts are written under the `--output` directory (Harbor jobs, patches, scores).
- Aggregate pass rate, cost, latency, and per-task outcomes are published on the [leaderboard](https://ibench.ai/leaderboard).
- Explore individual trajectories on the site when a run is published.

The 0.1 site release is a preview; treat leaderboard numbers as the current published snapshot, not a frozen paper result.

---

## Contributing

Contributions that improve tasks, configs, or the harness are welcome.

1. Install as in Quickstart, then validate with `uv run ibench check .`.
2. Use `preview`, `debug`, and `replay` while iterating on task materials ([contribute guide](https://ibench.ai/docs/contribute)).
3. Open a pull request against [eval-sys/ibench](https://github.com/eval-sys/ibench).

---

## License

Original Interaction Bench code and benchmark material use **Apache-2.0**. Third-party application source, assets, and trademarks retained or executed by tasks keep their own terms.

See [LICENSE](LICENSE), [NOTICE](NOTICE), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
