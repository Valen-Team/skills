# Valen skill evals

A fixed benchmark for the [Valen skill](../skills/valen/SKILL.md): coding agents build real integrations from a business brief, and a grader scores them on hidden labeled cases. It measures whether the skill helps an agent design good Valen questions, and keeps every skill edit honest.

## Tasks

| Task | Modality | Brief | Hidden test | Dev examples given to the agent |
| --- | --- | --- | ---: | ---: |
| [`delivery-support`](tasks/delivery-support/task.md) | Text (English, Chinese) | Route food-delivery support messages to 6 queues with `safety` and `compensation` flags | 60 | 10 |
| [`upload-intake`](tasks/upload-intake/task.md) | Image | Sort notes-app image uploads by kind, readable text and usability | 90 | 13 |
| [`clip-tagging`](tasks/clip-tagging/task.md) | Video | Tag stock-footage clips by setting, activity and number of people | 45 | 8 |

Each task folder holds `task.md` (the brief), `labeling.md` (the business's labeling rules), `dev.json` and the hidden `test.json`. Text messages are written for this benchmark. Images and videos come from [Valen-Team/VisualDecisionBench](https://huggingface.co/datasets/Valen-Team/VisualDecisionBench) and keep their upstream terms; the labels here are new business labels assigned by the Valen team, independent of the agents under test.

## Protocol

Every run starts an agent in a fresh folder containing only `task.md`, `labeling.md`, `dev.json` and the dev media. The `skill` arm also has the skill installed at `.claude/skills/valen/`; the `no-skill` arm does not. The agent:

1. writes a first complete version and freezes it in `v1/` before running it on any labeled example;
2. improves it on `dev.json` and its own cases, leaving the final version in `solution.py`;
3. writes `NOTES.md`.

The grader then runs `v1/solution.py` and `solution.py` on the hidden test set.

**Score**: balanced accuracy (mean per-class recall) per output field, averaged over the fields. A constant answer scores at chance (39% on `delivery-support`).
**Primary metric**: first-version score averaged over the three tasks. The skill's job is to make the first design right; the final version also reflects how well the agent iterates.

## Run

```bash
python -m pip install huggingface_hub
python evals/fetch_media.py
python evals/run.py --arms skill no-skill --runs 3
```

`--agent codex` runs the same protocol with `codex exec` (workspace-write sandbox with network access) and installs the skill at `.agents/skills/valen/`:

```bash
python evals/run.py --agent codex --arms skill no-skill --runs 1
```

With the default `--agent claude`, `run.py` uses the `claude` CLI in print mode with `--permission-mode auto` by default; pass `--permission-mode bypassPermissions` for unattended runs, where agents run commands without asking; keep it on a machine you are comfortable with. Each agent is capped by `--budget-usd` (default 15) and `--timeout` (default 90 minutes). Results land in `evals/results/<timestamp>/<task>/<arm>-<n>/` with the agent's workspace, transcript summary and `grade.json`; `summary.md` aggregates them:

```bash
python evals/summarize.py evals/results/<timestamp>
```

Grade a single workspace by hand with `python evals/grade.py WORKSPACE TASK`.

## Changing the skill

1. Run the current skill to get a baseline (3 runs per task at least).
2. Sort feedback from agents: product or docs defects go to the API and website; a principle seen in two or more tasks goes to `SKILL.md`; a lesson from one task goes to the cookbook or the question-design page.
3. Keep an edit only when the primary metric improves by more than the spread between runs; otherwise revert it.
4. Do not tune on `test.json`. If an edit is motivated by a hidden test case, add new cases to the next benchmark version instead.

## Results

First-version score on the hidden test sets, 2026-10-29, Claude Code and Codex agents on the free API:

| Task | Claude, skill (2 runs) | Claude, no skill | Codex, skill | Codex, no skill |
| --- | --- | --- | --- | --- |
| `delivery-support` (text) | 97.2%, 89.4% | 89.2% | 86.8% | 97.6% |
| `upload-intake` (image) | 92.3%, 92.4% | 58.8% | 91.4% | 92.2% |
| `clip-tagging` (video) | 95.9%, 88.7% | 92.7% | 95.6% | 0.0% |
| **Primary metric** | **92.7%** | **80.2%** | **91.2%** | **63.3%** |

With the skill, every first version scored at least 86.8%. Without it, each agent produced one first version that failed outright: Claude marked every image unusable after thresholding a vague question at 0.5, and Codex sent eight frames per request to an endpoint that accepts one, so every video request returned HTTP 400. On the other tasks the arms were close. Final versions scored 86.5–98.1% in all arms. Runs on the same task differ by up to 8 points, so add runs before reading small differences.

The best text run is published as the [support-router recipe](https://valen-team.github.io/cookbook/skill-support-router/).
