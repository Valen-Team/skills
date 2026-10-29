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

## Example and benchmark

- [Build a support router with the agent skill](https://valen-team.github.io/cookbook/skill-support-router/): what an agent built from a one-page brief, scored on unseen messages.
- [`evals/`](evals/): text, image and video tasks that measure the skill, with and without it installed.

## License

[Apache-2.0](LICENSE).
