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

## Every model behind the same code

The agents' first versions call Valen's hosted API. To ask whether a design holds up with another model, [`models.py`](models.py) runs each saved `v1/solution.py` unchanged and intercepts its Valen calls: Valen backends receive the original request with only `model` replaced; LLM backends answer the same questions through JevalKit's LLM baselines, with the response translated back to the API's format. Each cell averages the saved first versions for that task: three with the skill (Claude Code ×2, Codex ×1) and two without (Claude Code, Codex), 2026-10-30.

| Backend | Delivery, no skill | Delivery, skill | Upload, no skill | Upload, skill | Clips, no skill | Clips, skill | **No skill** | **Skill** | USD / item |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| valen-4b | 95.4 | 97.3 | 88.0 | 90.2 | 46.6 | 90.4 | **76.7** | **92.6** | 0 |
| valen-2b | 88.6 | 89.4 | 74.9 | 92.0 | 46.4 | 93.4 | **70.0** | **91.6** | 0 |
| valen-0.8b | 86.9 | 86.5 | 74.5 | 88.4 | 46.3 | 92.1 | **69.3** | **89.0** | 0 |
| claude-sonnet-5-5 | 98.1 | 97.8 | 90.5 | 93.3 | 96.9 | 97.3 | **95.2** | **96.1** | 0.00193 |
| gpt-6-luna | 98.8 | 98.7 | 90.5 | 92.7 | 95.5 | 95.2 | **94.9** | **95.5** | 0.00024 |
| gpt-5.6-terra | 98.6 | 98.5 | 85.4 | 89.9 | 96.4 | 94.0 | **93.4** | **94.1** | 0.01222 |
| gemini-3.8-flash | 98.3 | 97.4 | 90.0 | 89.9 | 95.5 | 94.8 | **94.6** | **94.0** | 0.00217 |
| claude-haiku-4-5 | 91.0 | 89.4 | 85.2 | 82.7 | 82.5 | 82.5 | **86.2** | **84.9** | 0.00174 |

- **The skill removes failures rather than raising the typical score.** Medians with and without it are close on every backend. On Valen, 2 of 6 first versions without the skill failed: Codex's video design sends eight frames per request, which the hosted API rejects, so it scores 0 on every size (GPT-6 Luna accepts all eight and scores 95.7); Claude's upload design thresholds a vague usability question and scores 60.3 and 58.7 on Valen 2B and 0.8B. With the skill, the worst of 9 first versions scores 84.1 on Valen 4B. LLM backends do not enforce the hosted API's one-image limit.
- **Final versions close the gap.** After iterating on dev data, designs without the skill reach 93.6 (4B) and 93.4 (2B); the skill's contribution is a first version that already works.
- **LLM conditions.** LLMs answer through an OpenAI-compatible gateway with JSON-schema output; Claude, served through its Messages API, returned schema-shaped JSON inside a Markdown fence, which is unwrapped. Answers that are not valid JSON count as errors (Claude Haiku: 9 of 1,156 calls). Costs use list prices on the tokens the gateway reported and billed; for Claude these leave out image inputs, which Anthropic's direct pricing adds. Times are median seconds per item from this machine, Valen on the free hosted API.

```bash
pip install "jevalkit @ git+https://github.com/Valen-Team/JevalKit"
python evals/models.py --runs evals/results/baseline-2 evals/results/codex-baseline-2 evals/results/smoke-1 \
  --backends valen-4b valen-2b valen-0.8b
GATEWAY_API_KEY=... python evals/models.py --runs ... --backends gpt-6-luna claude-sonnet-5-5 \
  --gateway https://gateway.example/v1
python evals/summarize_models.py --calls calls.csv
```

`--calls` writes every model call (start time, provider request ID, tokens, estimated cost) for reconciling against provider billing.
