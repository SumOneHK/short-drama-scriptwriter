# short-drama-scriptwriter

面向 AI 竖屏剧 / AI 漫剧的编剧工作流 skill，覆盖从立项选题、策划设计、分集场次执行稿到 Markdown 交付包的完整流程。同一份 skill 同时支持 **Claude Code（Anthropic Skills 规范）** 与 **OpenAI Codex CLI（Codex skills 规范）**，安装路径不同，触发方式不同，内容完全共用。

它不是一个通用短剧写作模板，而是一套带状态门禁、质量检查、交付口径和制作增强整理的工作流。适用场景包括抖音国内项目和 TikTok 出海项目；目标市场需单独锁定，如美国英语首版、泛欧美、东南亚、拉美或指定国家地区。**不适用于真人拍摄短剧、分镜、视频提示词、配音脚本或音效表生成。**

## 支持的运行环境

| 运行环境 | 安装路径 | 触发方式 |
| --- | --- | --- |
| Claude Code（用户级） | `~/.claude/skills/short-drama-scriptwriter/` | 自然语言提及关键词，模型按 frontmatter 的 `description` 自动加载 |
| Claude Code（项目级） | `<project>/.claude/skills/short-drama-scriptwriter/` | 同上，仅当前项目可见 |
| OpenAI Codex CLI | `~/.codex/skills/short-drama-scriptwriter/` 或 `$CODEX_HOME/skills/short-drama-scriptwriter/` | 在提问里写 `$short-drama-scriptwriter ...` 显式触发 |

> 仓库的 `SKILL.md` frontmatter (`name` / `description`) 同时被两套生态识别；`agents/openai.yaml` 仅 Codex 使用，Claude 侧会忽略。两侧加载的内容、模板、脚本完全一致。

## 功能特性

- 完整流程：立项与选题 → 剧本圣经设计 → 分集剧本创作 → 交付整理。
- 平台与市场分离：国内平台默认为抖音，出海平台默认为 TikTok；目标市场按国内、美国英语首版、泛欧美或指定地区单独判断。
- Markdown 交付：所有正式产物、工作稿、质检记录和交付包均按 Markdown / JSON 文件组织。
- 状态门禁：通过 `项目状态.json` 和 `质检检查点.md` 管控阶段推进，避免跳过大纲、质检或全剧复核。
- 结构化素材：内置项目简报、锁题摘要、项目设定、世界观、人物、分集大纲、剧本圣经、交付清单等 27 份模板。
- 制作增强包：支持 `production-enhanced` 模式，补齐制作理解稿、参数表、海外制作版分场表、信息流投放素材切片说明等文件。
- 辅助脚本：提供交付汇总脚本和单集硬阈值检查脚本，处理机械可计数的校验与整理工作。

## 目录结构

```text
.
├── SKILL.md                         # skill 主入口（Claude / Codex 共用）
├── agents/
│   └── openai.yaml                  # Codex 展示信息（仅 Codex 使用）
├── assets/
│   └── templates/                   # 各阶段产物模板（27 份）
├── LICENSE                          # MIT 开源许可证
├── references/                      # 流程、市场、剧本、质检、交付规则（25 份）
├── scripts/
│   ├── build_full_script.py         # 交付汇总脚本
│   ├── check_episode.py             # 单集硬阈值检查脚本
│   └── dogfood_generate_validation_projects.py
└── tests/                           # unittest 测试
```

## 安装

任选一种环境即可；同一台机器同时为 Claude Code 和 Codex 安装时，建议**只 clone 一次到第三方位置，再用软链接接到两边**，避免双份维护。

### Claude Code

用户级安装（推荐，所有项目都能用）：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/SumOneHK/short-drama-scriptwriter.git \
  ~/.claude/skills/short-drama-scriptwriter
```

项目级安装（仅当前项目可见，便于团队随仓库分发）：

```bash
mkdir -p .claude/skills
git clone https://github.com/SumOneHK/short-drama-scriptwriter.git \
  .claude/skills/short-drama-scriptwriter
```

安装后无需特殊触发命令，Claude 会按 SKILL.md 的 `description` 自动决定是否启用。提示示例见下文「使用方式」。

### OpenAI Codex CLI

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/SumOneHK/short-drama-scriptwriter.git \
  ~/.codex/skills/short-drama-scriptwriter
```

如果你设置了自定义 `CODEX_HOME`：

```bash
mkdir -p "$CODEX_HOME/skills"
git clone https://github.com/SumOneHK/short-drama-scriptwriter.git \
  "$CODEX_HOME/skills/short-drama-scriptwriter"
```

Codex 中显式触发：

```text
使用 $short-drama-scriptwriter 为抖音国内或 TikTok 出海 AI 竖屏剧 / AI 漫剧推进立项、策划、分集场次执行稿、复盘和 Markdown 交付。
```

### 同时给两边用（软链接方式）

```bash
# 1. clone 到任意位置
git clone https://github.com/SumOneHK/short-drama-scriptwriter.git \
  ~/dev/short-drama-scriptwriter

# 2. 分别软链到两个生态
mkdir -p ~/.claude/skills ~/.codex/skills
ln -s ~/dev/short-drama-scriptwriter ~/.claude/skills/short-drama-scriptwriter
ln -s ~/dev/short-drama-scriptwriter ~/.codex/skills/short-drama-scriptwriter
```

这样 `git pull` 一次即可同时更新两边。

### 升级

无论哪种环境，进入安装目录执行：

```bash
cd ~/.claude/skills/short-drama-scriptwriter   # 或 ~/.codex/skills/...
git pull
```

## 使用方式

新项目按四阶段推进：

1. **立项与选题**：先做市场判断、题材候选、方向确认；方向未确认前不创建项目目录。
2. **剧本圣经设计**：完成项目设定、世界观、人物、场景道具、梗概、大纲、节拍和分集大纲。
3. **分集剧本创作**：按批次生成 `第XXX集.md` 场次执行稿，并做批次质检。
4. **交付整理**：在全剧复核通过后生成完整剧本总稿、剧本圣经和交付清单。

### Claude Code 提示示例

直接用自然语言，不需要 `$` 前缀：

```text
帮我为抖音国内 AI 漫剧做立项选题，目标 60-90 秒单集、30 集左右。
```

```text
基于当前项目状态继续写第 001-003 集场次执行稿，并按批次做硬阈值检查。
```

```text
当前项目已完成全剧复核，请进入标准交付整合。
```

### Codex 提示示例

显式带 `$` 前缀触发：

```text
$short-drama-scriptwriter 帮我为抖音国内 AI 漫剧做立项选题，目标 60-90 秒单集、30 集左右。
```

```text
$short-drama-scriptwriter 基于当前项目状态继续写第 001-003 集场次执行稿，并按批次做硬阈值检查。
```

```text
$short-drama-scriptwriter 当前项目已完成全剧复核，请进入标准交付整合。
```

## 辅助脚本

脚本只做机械整理和可计数检查，**不替代模型读稿质检，也不能单独作为阶段放行依据**。

两侧运行环境调用方式相同；脚本不依赖 Claude / Codex 的具体运行时。

### 交付汇总

从项目目录中的正式策划源文件和分集剧本生成交付文件：

```bash
python3 scripts/build_full_script.py projects/<project-slug>
```

默认会校验 `项目状态.json`、已通过批次、必需策划源文件和交付模式。草稿模式可跳过正式门禁：

```bash
python3 scripts/build_full_script.py --draft projects/<project-slug>
```

只检查交付包是否落后于源文件，不重新生成：

```bash
python3 scripts/build_full_script.py --check-mode projects/<project-slug>
```

### 单集硬阈值检查

检查叠加屏幕字、画内文字可读性、环境标签字、规则词频次、前置字段比例和有效正文行数：

```bash
python3 scripts/check_episode.py \
  --regulation-words "命格,暗文,命债,见证人" \
  projects/<project-slug>/02-剧本/第001集.md
```

也可以检查整个剧本目录：

```bash
python3 scripts/check_episode.py projects/<project-slug>/02-剧本/
```

## 测试

本项目没有外部 Python 依赖，测试基于标准库 `unittest`：

```bash
python3 -m unittest discover -s tests
```

## 设计边界

- 只服务 AI 竖屏剧 / AI 漫剧；不以真人拍摄短剧的场景和预算逻辑作为题材限制。
- 最终剧本正文采用 `场次执行稿`，不按批次目录交付最终正文。
- 不生成分镜、视频提示词、配音脚本或音效表。
- 质检放行必须基于实际稿件的独立复检；脚本输出只作为硬阈值证据。
- `references/` 和 `assets/templates/` 是流程规则与产物结构的单一真相源，使用时应按阶段加载，不建议一次性全部读入上下文。
- 同一份内容供两套生态共用：所有运行时差异都收敛在 `agents/openai.yaml`（仅 Codex）和 `SKILL.md` 顶部 frontmatter（两边共用），核心规则、模板、脚本不区分运行环境。

## 贡献

欢迎提交 issue 或 pull request。建议贡献前先确认：

- 新规则是否应该进入 `SKILL.md`、`references/` 还是 `assets/templates/`。
- 新模板字段是否明确标注 MUST / SHOULD / MAY。
- 新脚本逻辑是否仍然只处理机械可验证问题，不越权替代剧本质检。
- 新增或修改脚本时同步补充 `tests/`。
- 改动 `SKILL.md` 的 frontmatter 时，确认 Claude Code 和 Codex 两边都仍能正常加载。

## License

本项目采用 MIT License，详见 [LICENSE](LICENSE)。
