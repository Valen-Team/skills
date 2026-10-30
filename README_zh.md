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

## 效果

我们给 coding agent 一页需求（客服消息分流、图片上传分类、视频片段打标），让它自己动手搭，再把每个 agent 写的第一版原样接到 Valen 和 5 个大模型上跑。

- **Valen 与前沿大模型只差几分，成本为零，快 2–3 倍。** 装了 skill 的第一版在 Valen 4B 上平均 92.6 分，GPT、Gemini、Claude Sonnet 在 94–96 分。
- **skill 让第一版不翻车。** 不装 skill 时，6 份第一版里有 2 份在 Valen 上失败：一份每次请求发 8 帧视频，而接口只收 1 张图，得 0 分；另一份对一个含糊的问题直接卡阈值，把大部分图片判成不可用，在小尺寸上不到 61 分。装了 skill 的 9 份全部站得住。大模型能吃下 8 张图、也能消化含糊的问题，所以同样的错误对它们影响不大。

| 回答问题的模型 | 装 skill 的第一版 | 装 skill 的最差一份 | 不装 skill 的最差一份 | 每 1,000 条成本（标价） | 每条耗时中位数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Valen 4B** | **92.6** | **84.1** | 0.0 | **$0** | **2.7 秒** |
| **Valen 2B** | **91.6** | **86.8** | 0.0 | **$0** | **2.7 秒** |
| **Valen 0.8B** | **89.0** | **78.2** | 0.0 | **$0** | **2.6 秒** |
| Claude Sonnet 5.5 | 96.1 | 92.2 | 89.5 | $1.93* | 6.8 秒 |
| GPT-6 Luna | 95.5 | 90.1 | 89.9 | $0.24 | 6.0 秒 |
| GPT-5.6 Terra | 94.1 | 85.4 | 84.7 | $12.22 | 7.4 秒 |
| Gemini 3.8 Flash | 94.0 | 86.8 | 89.7 | $2.17 | 6.3 秒 |
| Claude Haiku 4.5 | 84.9 | 79.0 | 78.5 | $1.74* | 6.7 秒 |

分数为 195 条未见样本（60 条消息、90 张图片、45 段视频）上的平衡准确率，来自 Claude Code 和 Codex 写的 9 份装 skill、6 份不装 skill 的第一版。每一行跑的是同一份 agent 写的代码，只换回答问题的模型。[评测方法](evals/README.md#every-model-behind-the-same-code)。

<sub>* 按网关实际计费的 token 计算，其中不含 Claude 的图片输入；按 Anthropic 官方价格还要加上这部分。</sub>

## 示例与评测

- [用 agent skill 做客服分流](https://valen-team.github.io/zh-Hans/cookbook/skill-support-router/)：agent 根据一页需求做出的应用，以及在没见过的消息上的得分。
- [`evals/`](evals/)：文本、图像、视频三个任务，对比装与不装 skill 的效果。

## 许可证

[Apache-2.0](LICENSE)。
