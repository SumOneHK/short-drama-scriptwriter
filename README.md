# short-drama-scriptwriter

面向 AI 漫剧的 Codex 编剧工作流 skill，覆盖从立项选题、策划设计、分集场次执行稿到 Markdown 交付包的完整流程。

它不是一个通用短剧写作模板，而是一套带状态门禁、质量检查、交付约束和制作增强整理的工作流。适用场景包括抖音国内和 TikTok 欧美市场的 AI 漫剧项目，不适用于真人拍摄短剧、分镜、视频提示词、配音脚本或音效表生成。

## 功能特性

- 完整流程：立项与选题 -> 剧本圣经设计 -> 分集剧本创作 -> 交付整理。
- 双市场支持：抖音国内、TikTok 欧美；海外项目策划层使用中文，英文只用于对白、屏幕字和必要制作字段。
- Markdown 交付：所有正式产物、工作稿、质检记录和交付包均按 Markdown / JSON 文件组织。
- 状态门禁：通过 `项目状态.json` 和 `质检检查点.md` 管控阶段推进，避免跳过大纲、质检或全剧复核。
- 结构化素材：内置项目简报、锁题摘要、项目设定、世界观、人物、分集大纲、剧本圣经、交付清单等模板。
- 制作增强包：支持 `production-enhanced` 模式，补齐制作理解稿、参数表、海外制作版分场表、信息流投放素材切片说明等文件。
- 辅助脚本：提供交付汇总脚本和单集硬阈值检查脚本，处理机械可计数的校验与整理工作。

## 目录结构

```text
.
├── SKILL.md                         # skill 主说明与流程入口
├── agents/
│   └── openai.yaml                  # Codex/agent 展示信息
├── assets/
│   └── templates/                   # 各阶段产物模板
├── LICENSE                          # MIT 开源许可证
├── references/                      # 流程、市场、剧本、质检、交付规则
├── scripts/
│   ├── build_full_script.py         # 交付汇总脚本
│   ├── check_episode.py             # 单集硬阈值检查脚本
│   └── dogfood_generate_validation_projects.py
└── tests/                           # unittest 测试
```

## 安装

### 安装到 Codex skills 目录

将仓库克隆到你的 Codex skills 目录，并保持目录名为 `short-drama-scriptwriter`。把 `<repo-url>` 替换为你发布后的 GitHub 仓库地址：

```bash
mkdir -p ~/.codex/skills
git clone <repo-url> ~/.codex/skills/short-drama-scriptwriter
```

如果你使用的是自定义 `CODEX_HOME`：

```bash
mkdir -p "$CODEX_HOME/skills"
git clone <repo-url> "$CODEX_HOME/skills/short-drama-scriptwriter"
```

安装后，在 Codex 中可用类似方式触发：

```text
使用 $short-drama-scriptwriter 为抖音国内或 TikTok 欧美 AI 漫剧推进立项、策划、分集场次执行稿、复盘和 Markdown 交付。
```

## 使用方式

新项目建议按流程推进：

1. 立项与选题：先做市场判断、题材候选、方向确认；方向未确认前不创建项目目录。
2. 剧本圣经设计：完成项目设定、世界观、人物、场景道具、梗概、大纲、节拍和分集大纲。
3. 分集剧本创作：按批次生成 `第XXX集.md` 场次执行稿，并做批次质检。
4. 交付整理：在全剧复核通过后生成完整剧本总稿、剧本圣经和交付清单。

常见提示示例：

```text
使用 $short-drama-scriptwriter，帮我为抖音国内 AI 漫剧做立项选题，目标是 60-90 秒单集、30 集左右。
```

```text
使用 $short-drama-scriptwriter，基于当前项目状态继续写第 001-003 集场次执行稿，并按批次做硬阈值检查。
```

```text
使用 $short-drama-scriptwriter，当前项目已完成全剧复核，请进入标准交付整合。
```

## 辅助脚本

脚本只做机械整理和可计数检查，不替代模型读稿质检，也不能单独作为阶段放行依据。

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

- 只服务 AI 漫剧，不服务真人拍摄短剧。
- 最终剧本正文采用 `场次执行稿`，不按批次目录交付最终正文。
- 不生成分镜、视频提示词、配音脚本或音效表。
- 质检放行必须基于实际稿件的独立复检；脚本输出只作为硬阈值证据。
- `references/` 和 `assets/templates/` 是流程规则与产物结构的单一真相源，使用时应按阶段加载，不建议一次性全部读入上下文。

## 贡献

欢迎提交 issue 或 pull request。建议贡献前先确认：

- 新规则是否应该进入 `SKILL.md`、`references/` 还是 `assets/templates/`。
- 新模板字段是否明确标注 MUST / SHOULD / MAY。
- 新脚本逻辑是否仍然只处理机械可验证问题，不越权替代剧本质检。
- 新增或修改脚本时同步补充 `tests/`。

## License

本项目采用 MIT License，详见 [LICENSE](LICENSE)。
