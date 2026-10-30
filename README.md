<p align="center">
  <img src="https://raw.githubusercontent.com/Valen-Team/Valen/main/assets/branding/valen-mark-white.png" alt="Valen" width="96">
</p>
<h1 align="center">Valen Agent Skills</h1>
<p align="center">Teach your coding agent to build with <a href="https://github.com/Valen-Team/Valen">Valen</a>: typed decisions and probabilities over text, images and video.</p>

<p align="center">
  <strong>English</strong> · <a href="README_zh.md">简体中文</a><br>
  <a href="skills/valen/SKILL.md">Read SKILL.md</a> · <a href="https://valen-team.github.io/docs/valen/agent-skill/">Documentation</a> · <a href="https://valen-team.github.io/llms.txt">llms.txt</a>
</p>

## Install

### Claude Code plugin

```bash
claude plugin marketplace add Valen-Team/skills
claude plugin install valen@valen-team
```

### Codex

```bash
codex plugin marketplace add Valen-Team/skills
codex plugin add valen@valen-team
```

Or copy [`skills/valen/`](skills/valen/) into `~/.codex/skills/valen/` (all projects) or `.agents/skills/valen/` in a project. Codex lists it as `valen:valen` when installed as a plugin and `valen` when copied; mention Valen in your request, or name the skill.

### Other agents via skills.sh

```bash
npx skills add Valen-Team/skills --skill valen
```

Select your agent when prompted. Installation is project-local by default; add `-g` to install globally.

### Manual

Copy [`skills/valen/`](skills/valen/) into your agent's skills directory, for example `.claude/skills/valen/` in a project.

## Use

Ask your agent, for example:

> Use Valen to screen product photos for watermarks, logos and blur, and send uncertain listings to human review.

> Replace the keyword rules in `router.py` with Valen questions, with a `none` route for messages that fit no queue.

In Claude Code, invoke the skill explicitly with `/valen:valen`; in Codex, ask for `$valen` or name the skill.

| Skill | Purpose |
|---|---|
| [valen](skills/valen/SKILL.md) | Design Valen integrations: decision logic, state and image design, question and candidate wording, request composition, thresholds, runtime choice, and pointers to the live docs |

## Results

We gave coding agents a one-page brief (route support messages, sort image uploads, tag video clips), let them build, then ran each agent's first version, unchanged, against Valen and five LLMs.

- **Valen comes within a few points of frontier LLMs, free and 2–3× faster.** First versions built with the skill average 92.6 on Valen 4B, against 94–96 on GPT, Gemini and Claude Sonnet.
- **The skill keeps the first version from breaking.** Without it, 2 of 6 first versions failed on Valen: one sent eight video frames per request to an endpoint that takes one, and scored 0; another thresholded a vague question and marked most images unusable, scoring below 61 on the smaller sizes. With the skill, all 9 held up. LLMs accept eight images and absorb vague questions, so the same mistakes cost them little.

| Model answering the integration's questions | First version with the skill | Worst first version, with skill | Worst, without skill | Cost per 1,000 items, list price | Median time per item |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Valen 4B** | **92.6** | **84.1** | 0.0 | **$0** | **2.7 s** |
| **Valen 2B** | **91.6** | **86.8** | 0.0 | **$0** | **2.7 s** |
| **Valen 0.8B** | **89.0** | **78.2** | 0.0 | **$0** | **2.6 s** |
| Claude Sonnet 5.5 | 96.1 | 92.2 | 89.5 | $1.93* | 6.8 s |
| GPT-6 Luna | 95.5 | 90.1 | 89.9 | $0.24 | 6.0 s |
| GPT-5.6 Terra | 94.1 | 85.4 | 84.7 | $12.22 | 7.4 s |
| Gemini 3.8 Flash | 94.0 | 86.8 | 89.7 | $2.17 | 6.3 s |
| Claude Haiku 4.5 | 84.9 | 79.0 | 78.5 | $1.74* | 6.7 s |

Balanced accuracy on 195 unseen items (60 messages, 90 images, 45 videos), from 9 first versions with the skill and 6 without, written by Claude Code and Codex. Every row runs the same agent-written code; only the model answering its questions changes. [How we measured](evals/README.md#every-model-behind-the-same-code).

<sub>* Counts the tokens our gateway billed, which leave out Claude's image inputs; Anthropic's direct pricing adds them.</sub>

## Example and benchmark

- [Build a support router with the agent skill](https://valen-team.github.io/cookbook/skill-support-router/): what an agent built from a one-page brief, scored on unseen messages.
- [`evals/`](evals/): text, image and video tasks that measure the skill, with and without it installed.

## License

[Apache-2.0](LICENSE).
