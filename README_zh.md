<p align="center">
  <img src="https://raw.githubusercontent.com/Valen-Team/Valen/main/assets/branding/valen-mark-white.png" alt="Valen" width="96">
</p>
<h1 align="center">Valen Agent Skills</h1>
<p align="center">让你的编程 agent 学会用 <a href="https://github.com/Valen-Team/Valen">Valen</a> 构建应用：对文本、图像和视频给出类型化的决策和概率。</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong><br>
  <a href="skills/valen/SKILL.md">阅读 SKILL.md</a> · <a href="https://valen-team.github.io/zh-Hans/docs/valen/agent-skill/">文档</a> · <a href="https://valen-team.github.io/llms.txt">llms.txt</a>
</p>

## 安装

### Claude Code 插件

```bash
claude plugin marketplace add Valen-Team/skills
claude plugin install valen@valen-team
```

### Codex

```bash
codex plugin marketplace add Valen-Team/skills
codex plugin add valen@valen-team
```

也可以把 [`skills/valen/`](skills/valen/) 复制到 `~/.codex/skills/valen/`（所有项目可用），或项目里的 `.agents/skills/valen/`。通过插件安装时 Codex 中显示为 `valen:valen`，复制安装时显示为 `valen`；在需求里提到 Valen，或直接点名这个 skill 即可。

### 其他 agent（通过 skills.sh）

```bash
npx skills add Valen-Team/skills --skill valen
```

按提示选择你的 agent。默认安装到当前项目；加 `-g` 安装到全局。

### 手动安装

把 [`skills/valen/`](skills/valen/) 复制到 agent 的 skills 目录，例如项目里的 `.claude/skills/valen/`。

## 使用

直接对 agent 说，例如：

> 用 Valen 检查商品图里有没有水印、logo 和模糊，拿不准的商品转人工审核。

> 把 `router.py` 里的关键词规则换成 Valen 问题，哪个队列都不匹配的消息走 `none` 分支。

在 Claude Code 中可以用 `/valen:valen` 显式调用；在 Codex 中输入 `$valen` 或直接点名这个 skill。

| Skill | 用途 |
|---|---|
| [valen](skills/valen/SKILL.md) | 设计 Valen 集成：决策逻辑、state 与图像组织、问题和候选项写法、请求组合、阈值、运行时选择，以及指向在线文档的入口 |

## 示例与评测

- [用 agent skill 做客服分流](https://valen-team.github.io/zh-Hans/cookbook/skill-support-router/)：agent 根据一页需求做出的应用，以及在没见过的消息上的得分。
- [`evals/`](evals/)：文本、图像、视频三个任务，对比装与不装 skill 的效果。

## 许可证

[Apache-2.0](LICENSE)。
