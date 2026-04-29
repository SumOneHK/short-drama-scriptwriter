"""单集场次执行稿确定性一致性校验工具。

用途：
- 对单集 `第XXX集.md` 做"机械可计数"的检查（叠加屏幕字字数 / 画内文字可读性 / 环境标签字 / 规则词频次 / 前置字段比例 / 有效行数）
- 不参与质检放行（质检放行只看模型读稿复检，详见 references/18 / 19）
- 不替代戏剧判断；只发现"模型自检容易漏掉的硬阈值越线"

使用：
    python3 check_episode.py --regulation-words "命格,暗文,命债,见证人" projects/<slug>/02-剧本/第001集.md
    python3 check_episode.py projects/<slug>/02-剧本/  # 检查整个目录所有集

退出码：
    0 = 全部通过
    1 = 至少一集发现越线问题
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, fields, replace
from pathlib import Path


# ===== 阈值常量（与 references/12-单集写作协议.md 第三章保持一致） =====

DEFAULT_SCREEN_TEXT_PER_SCENE_LIMIT = 12  # 叠加屏幕字单条字数上限
DEFAULT_SCREEN_TEXT_PER_EPISODE_LIMIT = 30  # 叠加屏幕字整集累计字数上限
DEFAULT_DIEGETIC_TEXT_PER_LINE_WARN_LIMIT = 24  # 画内信息文字单条可读性提示线
DEFAULT_DIEGETIC_TEXT_PER_EPISODE_WARN_LIMIT = 120  # 画内信息文字整集可读性提示线
DEFAULT_REGULATION_WORD_PER_SCENE_LIMIT = 1  # 规则词单场出现次数上限
DEFAULT_REGULATION_WORD_PER_EPISODE_LIMIT = 3  # 规则词整集累计上限
DEFAULT_PREFIX_RATIO_LIMIT = 1 / 3  # 前置字段行数 / 正文行数 上限

DEFAULT_MIN_BODY_LINES_60_90S = 28  # 60-90 秒规格最少正文行数
DEFAULT_MIN_BODY_LINES_90_120S = 34  # 90-120 秒规格最少正文行数
DEFAULT_MIN_BODY_LINES_45_75S = 22  # 45-75 秒规格最少正文行数
DEFAULT_MIN_BODY_LINES_FIRST_EPISODE = 34  # 首集最少正文行数


# ===== 阈值容器（项目级覆盖） =====


@dataclass(frozen=True)
class Thresholds:
    """所有阈值的项目级容器。

    项目可以在 `项目状态.json` 的 `qualityThresholds` 字段里覆盖任意子集；
    未覆盖的字段保持 references/12 第三章的默认值。
    """

    screen_text_per_scene_limit: int = DEFAULT_SCREEN_TEXT_PER_SCENE_LIMIT
    screen_text_per_episode_limit: int = DEFAULT_SCREEN_TEXT_PER_EPISODE_LIMIT
    diegetic_text_per_line_warn_limit: int = DEFAULT_DIEGETIC_TEXT_PER_LINE_WARN_LIMIT
    diegetic_text_per_episode_warn_limit: int = DEFAULT_DIEGETIC_TEXT_PER_EPISODE_WARN_LIMIT
    regulation_word_per_scene_limit: int = DEFAULT_REGULATION_WORD_PER_SCENE_LIMIT
    regulation_word_per_episode_limit: int = DEFAULT_REGULATION_WORD_PER_EPISODE_LIMIT
    prefix_ratio_limit: float = DEFAULT_PREFIX_RATIO_LIMIT
    min_body_lines_60_90s: int = DEFAULT_MIN_BODY_LINES_60_90S
    min_body_lines_90_120s: int = DEFAULT_MIN_BODY_LINES_90_120S
    min_body_lines_45_75s: int = DEFAULT_MIN_BODY_LINES_45_75S
    min_body_lines_first_episode: int = DEFAULT_MIN_BODY_LINES_FIRST_EPISODE

    @classmethod
    def from_overrides(cls, overrides: dict | None) -> "Thresholds":
        """从字典构造：未提供的键保持默认值；非法 key 直接忽略并 stderr 警告。"""
        base = cls()
        if not isinstance(overrides, dict):
            return base
        valid_keys = {f.name for f in fields(cls)}
        kwargs = {}
        for key, value in overrides.items():
            if key not in valid_keys:
                sys.stderr.write(
                    f"[WARN] qualityThresholds 出现未知字段 `{key}`，已忽略。\n"
                )
                continue
            kwargs[key] = value
        return replace(base, **kwargs)


def load_thresholds_from_project_state(project_dir: Path) -> Thresholds:
    """从 `<project>/项目状态.json` 的 `qualityThresholds` 字段加载阈值覆盖。

    文件不存在 / JSON 不合法 / 没有 qualityThresholds 字段时，返回默认值。
    """
    state_path = project_dir / "项目状态.json"
    if not state_path.exists():
        return Thresholds()
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"[WARN] {state_path} 不是合法 JSON：{exc}；阈值回退默认值。\n")
        return Thresholds()
    if not isinstance(state, dict):
        return Thresholds()
    return Thresholds.from_overrides(state.get("qualityThresholds"))

# ===== 数据结构 =====


@dataclass(frozen=True)
class Violation:
    """单条越线问题。"""

    severity: str  # "FAIL" | "WARN"
    rule: str
    detail: str
    location: str = ""


@dataclass(frozen=True)
class EpisodeReport:
    """单集校验报告。"""

    episode_path: str
    violations: tuple[Violation, ...]
    body_line_count: int
    prefix_line_count: int
    screen_text_total_chars: int
    diegetic_text_total_chars: int
    label_text_total_chars: int
    regulation_word_total_count: int

    @property
    def passed(self) -> bool:
        return not any(v.severity == "FAIL" for v in self.violations)

    @property
    def evidence_text_total_chars(self) -> int:
        """兼容旧字段名：上一版把画内文字称为证据字。"""
        return self.diegetic_text_total_chars


@dataclass(frozen=True)
class ScreenTextItem:
    """一条画面文字。

    category=overlay 参与硬阈值；diegetic 只做可读性提示；label 单独统计。
    """

    content: str
    char_count: int
    category: str  # "overlay" | "diegetic" | "label"
    tag: str = ""


# ===== 解析逻辑 =====


SCENE_HEADING_RE = re.compile(r"^### \d+-\d+ .+$")
ACTION_LINE_RE = re.compile(r"^△")
CHARACTER_LINE_RE = re.compile(r"^[一-龥A-Za-z][一-龥A-Za-z0-9· .'\-\s]{0,40}[：:]")
SCREEN_TEXT_RE = re.compile(
    r"^(?:屏幕字(?:（(?P<tag>[^）]+)）)?|Screen Text(?: \((?P<en_tag>[^)]+)\))?)[：:]\s*(?P<content>.+)$"
)
PREFIX_FIELD_RE = re.compile(r"^- (?:承接点|场景目标|场景状态差量|视觉记忆点|动作升级点|第二阻力 / 二次压迫|场内翻面|可见后果)：")

OVERLAY_SCREEN_TEXT_TAGS = frozenset(
    {
        "叠加",
        "叠加提示",
        "作者提示",
        "规则",
        "规则说明",
        "总结",
        "弹幕式总结",
        "字幕",
        "subtitle",
        "caption",
        "overlay",
        "super",
        "title",
    }
)
DIEGETIC_SCREEN_TEXT_TAGS = frozenset(
    {
        "证据",
        "画内证据",
        "画内",
        "屏内",
        "界面",
        "系统",
        "文件",
        "公告",
        "公示",
        "通知",
        "账本",
        "名单",
        "表格",
        "票据",
        "收据",
        "发票",
        "合同",
        "授权",
        "申请",
        "回执",
        "手机",
        "短信",
        "消息",
        "聊天",
        "群聊",
        "私信",
        "邮件",
        "弹窗",
        "直播",
        "热搜",
        "评论",
        "弹幕",
        "病历",
        "诊断",
        "处方",
        "检查单",
        "成绩单",
        "课表",
        "考勤",
        "档案",
        "判词",
        "转移结果",
        "phone",
        "text",
        "message",
        "chat",
        "dm",
        "email",
        "file",
        "document",
        "notice",
        "record",
        "report",
        "bill",
        "invoice",
        "receipt",
        "contract",
        "system",
        "alert",
    }
)
LABEL_SCREEN_TEXT_TAGS = frozenset(
    {
        "姓名牌",
        "人名牌",
        "名牌",
        "招牌",
        "地名",
        "门牌",
        "路牌",
        "标识",
        "标签",
        "nameplate",
        "sign",
        "signage",
        "label",
        "location",
    }
)
DIEGETIC_SCREEN_TEXT_KEYWORDS = (
    "公告",
    "公示",
    "通知",
    "明细",
    "账本",
    "名单",
    "合同",
    "授权",
    "申请",
    "回执",
    "收据",
    "发票",
    "票据",
    "登记",
    "记录",
    "档案",
    "文件",
    "群聊",
    "聊天记录",
    "短信",
    "微信",
    "业主群",
    "付款",
    "转账",
    "维修基金",
    "病历",
    "诊断",
    "处方",
    "检查单",
    "成绩单",
    "课表",
    "考勤",
    "处分",
    "热搜",
    "直播间",
    "评论",
    "弹幕",
    "判词",
    "转给",
    "access denied",
    "system alert",
    "message",
    "chat",
    "dm",
    "email",
    "file",
    "document",
    "notice",
    "record",
    "report",
    "bill",
    "invoice",
    "receipt",
    "contract",
)
LABEL_SCREEN_TEXT_KEYWORDS = (
    "姓名牌",
    "人名牌",
    "门牌",
    "路牌",
    "招牌",
)


def split_into_scenes(text: str) -> list[tuple[str, list[str]]]:
    """把单集正文按场次拆分。返回 [(scene_heading, body_lines), ...]。

    只处理 `## 场次正文` 之后的内容，跳过本集创作简卡和本集回填。
    """
    lines = text.splitlines()

    in_body_section = False
    current_scene: list[str] = []
    current_heading = ""
    scenes: list[tuple[str, list[str]]] = []

    for line in lines:
        if line.startswith("## 场次正文"):
            in_body_section = True
            continue
        if line.startswith("## 本集回填"):
            in_body_section = False
            if current_heading:
                scenes.append((current_heading, current_scene))
                current_scene = []
                current_heading = ""
            break
        if not in_body_section:
            continue
        if SCENE_HEADING_RE.match(line):
            if current_heading:
                scenes.append((current_heading, current_scene))
            current_heading = line
            current_scene = []
        elif current_heading:
            current_scene.append(line)

    if current_heading:
        scenes.append((current_heading, current_scene))

    return scenes


def count_body_lines(scene_body: list[str]) -> int:
    """计算一场内的有效正文行数：动作行 / 角色台词行 / OS / VO / 屏幕字 / SFX 算正文；
    前置字段行 / 空行 / 注释行不算。"""
    count = 0
    for line in scene_body:
        stripped = line.strip()
        if not stripped:
            continue
        if PREFIX_FIELD_RE.match(stripped):
            continue
        if stripped.startswith("人物：") or stripped.startswith("<!--"):
            continue
        if (
            stripped.startswith("△")
            or CHARACTER_LINE_RE.match(stripped)
            or stripped.startswith("OS：")
            or stripped.startswith("VO：")
            or SCREEN_TEXT_RE.match(stripped)
            or stripped.startswith("SFX：")
        ):
            count += 1
    return count


def count_prefix_lines(scene_body: list[str]) -> int:
    """计算一场内的前置字段行数。"""
    return sum(1 for line in scene_body if PREFIX_FIELD_RE.match(line.strip()))


def count_mixed_text_units(content: str) -> int:
    """中文按汉字计，英文按 word 计，用于估算竖屏可读负担。"""
    chinese_chars = sum(1 for c in content if "一" <= c <= "龥")
    english_words = len(re.findall(r"[A-Za-z]+", content))
    return chinese_chars + english_words


def classify_screen_text(content: str, tag: str = "") -> str:
    """判断画面文字类别。

    `屏幕字` 是制作标记，不是单一预算。真正需要硬卡的是作者额外叠加的
    提示/规则字；剧情世界内的手机、文件、系统界面、榜单、告示等，应按
    竖屏可读性提示处理；姓名牌、地名、门牌等低负担标签单独统计。
    """
    normalized_tag = tag.strip().lower()
    if normalized_tag:
        for overlay_tag in OVERLAY_SCREEN_TEXT_TAGS:
            if overlay_tag.lower() in normalized_tag:
                return "overlay"
        for label_tag in LABEL_SCREEN_TEXT_TAGS:
            if label_tag.lower() in normalized_tag:
                return "label"
        for diegetic_tag in DIEGETIC_SCREEN_TEXT_TAGS:
            if diegetic_tag.lower() in normalized_tag:
                return "diegetic"

    lower_content = content.lower()
    if any(keyword in lower_content for keyword in DIEGETIC_SCREEN_TEXT_KEYWORDS):
        return "diegetic"
    if any(keyword in content for keyword in LABEL_SCREEN_TEXT_KEYWORDS):
        return "label"
    return "overlay"


def is_evidence_screen_text(content: str, tag: str = "") -> bool:
    """兼容旧调用：上一版把画内信息文字称为证据文字。"""
    return classify_screen_text(content, tag) == "diegetic"


def extract_screen_text_items(scene_body: list[str]) -> list[ScreenTextItem]:
    """提取一场内所有画面文字，区分叠加字、画内信息字和环境标签。"""
    results: list[ScreenTextItem] = []
    for line in scene_body:
        stripped = line.strip()
        match = SCREEN_TEXT_RE.match(stripped)
        if match:
            tag = (match.group("tag") or match.group("en_tag") or "").strip()
            content = match.group("content").strip()
            results.append(
                ScreenTextItem(
                    content=content,
                    char_count=count_mixed_text_units(content),
                    category=classify_screen_text(content, tag),
                    tag=tag,
                )
            )
    return results


def extract_screen_text_chars(scene_body: list[str]) -> list[tuple[str, int]]:
    """兼容旧调用：只返回叠加屏幕字的 [(content, char_count), ...]。"""
    return [
        (item.content, item.char_count)
        for item in extract_screen_text_items(scene_body)
        if item.category == "overlay"
    ]


def count_regulation_words(scene_body: list[str], regulation_words: list[str]) -> dict[str, int]:
    """统计一场内规则词出现次数。"""
    text = "\n".join(scene_body)
    counts: dict[str, int] = {}
    for word in regulation_words:
        word = word.strip()
        if not word:
            continue
        counts[word] = text.count(word)
    return counts


# ===== 校验逻辑 =====


def check_episode(
    episode_path: Path,
    regulation_words: list[str],
    target_seconds: int = 75,
    is_first_episode: bool = False,
    thresholds: Thresholds | None = None,
) -> EpisodeReport:
    """校验单集场次执行稿。

    `thresholds` 不传时使用 `Thresholds()` 的默认值；项目级覆盖应该由调用方
    通过 `load_thresholds_from_project_state()` 提前装载好后传进来。
    """
    if thresholds is None:
        thresholds = Thresholds()

    text = episode_path.read_text(encoding="utf-8")
    scenes = split_into_scenes(text)
    violations: list[Violation] = []

    if not scenes:
        violations.append(
            Violation(
                severity="FAIL",
                rule="format",
                detail="未在 `## 场次正文` 段落下找到任何 `### N-N` 场次标题",
            )
        )
        return EpisodeReport(
            episode_path=str(episode_path),
            violations=tuple(violations),
            body_line_count=0,
            prefix_line_count=0,
            screen_text_total_chars=0,
            diegetic_text_total_chars=0,
            label_text_total_chars=0,
            regulation_word_total_count=0,
        )

    total_body = 0
    total_prefix = 0
    total_screen_chars = 0
    total_diegetic_chars = 0
    total_label_chars = 0
    total_regulation_count = 0

    for heading, body in scenes:
        body_lines = count_body_lines(body)
        prefix_lines = count_prefix_lines(body)
        total_body += body_lines
        total_prefix += prefix_lines

        # 1. 前置字段比例
        if body_lines > 0:
            ratio = prefix_lines / body_lines
            if ratio > thresholds.prefix_ratio_limit:
                violations.append(
                    Violation(
                        severity="FAIL",
                        rule="prefix_ratio",
                        detail=f"前置字段 {prefix_lines} 行 / 正文 {body_lines} 行 = {ratio:.2f}，超过 {thresholds.prefix_ratio_limit:.2f} 阈值",
                        location=heading,
                    )
                )

        # 2. 画面文字字数：叠加提示字硬卡；画内信息字只提示可读性风险；环境标签单独统计
        screen_texts = extract_screen_text_items(body)
        for item in screen_texts:
            if item.category == "label":
                total_label_chars += item.char_count
                continue

            if item.category == "diegetic":
                total_diegetic_chars += item.char_count
                if item.char_count > thresholds.diegetic_text_per_line_warn_limit:
                    violations.append(
                        Violation(
                            severity="WARN",
                            rule="diegetic_text_per_line",
                            detail=(
                                f"画内文字 {item.char_count} 字超过单条建议 "
                                f"{thresholds.diegetic_text_per_line_warn_limit} 字：'{item.content}'"
                            ),
                            location=heading,
                        )
                    )
                continue

            total_screen_chars += item.char_count
            if item.char_count > thresholds.screen_text_per_scene_limit:
                violations.append(
                    Violation(
                        severity="FAIL",
                        rule="screen_text_per_line",
                        detail=f"叠加屏幕字 {item.char_count} 字超过单条 {thresholds.screen_text_per_scene_limit} 字阈值：'{item.content}'",
                        location=heading,
                    )
                )

        # 3. 规则词单场频次
        if regulation_words:
            counts = count_regulation_words(body, regulation_words)
            scene_regulation_count = sum(counts.values())
            total_regulation_count += scene_regulation_count
            for word, count in counts.items():
                if count > thresholds.regulation_word_per_scene_limit:
                    violations.append(
                        Violation(
                            severity="FAIL",
                            rule="regulation_word_per_scene",
                            detail=f"规则词 '{word}' 在本场出现 {count} 次，超过单场 {thresholds.regulation_word_per_scene_limit} 次阈值",
                            location=heading,
                        )
                    )

    # 4. 叠加屏幕字整集字数
    if total_screen_chars > thresholds.screen_text_per_episode_limit:
        violations.append(
            Violation(
                severity="FAIL",
                rule="screen_text_per_episode",
                detail=f"叠加屏幕字累计 {total_screen_chars} 字超过整集 {thresholds.screen_text_per_episode_limit} 字阈值",
            )
        )

    # 4.5 画内信息字整集可读性提示
    if total_diegetic_chars > thresholds.diegetic_text_per_episode_warn_limit:
        violations.append(
            Violation(
                severity="WARN",
                rule="diegetic_text_per_episode",
                detail=(
                    f"画内文字累计 {total_diegetic_chars} 字超过整集建议 "
                    f"{thresholds.diegetic_text_per_episode_warn_limit} 字；需人工确认没有变成读材料"
                ),
            )
        )

    # 5. 规则词整集频次
    if total_regulation_count > thresholds.regulation_word_per_episode_limit:
        violations.append(
            Violation(
                severity="FAIL",
                rule="regulation_word_per_episode",
                detail=f"规则词累计 {total_regulation_count} 次超过整集 {thresholds.regulation_word_per_episode_limit} 次阈值",
            )
        )

    # 6. 有效正文行数下限
    if is_first_episode:
        min_body_lines = thresholds.min_body_lines_first_episode
        spec_label = "首集"
    elif target_seconds >= 90:
        min_body_lines = thresholds.min_body_lines_90_120s
        spec_label = "90-120 秒规格"
    elif target_seconds >= 60:
        min_body_lines = thresholds.min_body_lines_60_90s
        spec_label = "60-90 秒规格"
    else:
        min_body_lines = thresholds.min_body_lines_45_75s
        spec_label = "45-75 秒规格"

    if total_body < min_body_lines:
        violations.append(
            Violation(
                severity="WARN",
                rule="body_line_count",
                detail=f"全集有效正文 {total_body} 行 < {spec_label} 推荐下限 {min_body_lines} 行",
            )
        )

    return EpisodeReport(
        episode_path=str(episode_path),
        violations=tuple(violations),
        body_line_count=total_body,
        prefix_line_count=total_prefix,
        screen_text_total_chars=total_screen_chars,
        diegetic_text_total_chars=total_diegetic_chars,
        label_text_total_chars=total_label_chars,
        regulation_word_total_count=total_regulation_count,
    )


# ===== CLI =====


def detect_episode_number(path: Path) -> int:
    match = re.search(r"(?:第|EP|ep)(\d{3})", path.stem)
    return int(match.group(1)) if match else 0


def collect_episode_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(
        [p for p in target.rglob("*.md") if re.search(r"(?:第|EP|ep)\d{3}(?:集)?\.md$", p.name)],
        key=detect_episode_number,
    )


def format_report(report: EpisodeReport) -> str:
    lines = [
        f"\n=== {report.episode_path} ===",
        f"  正文 {report.body_line_count} 行 / 前置 {report.prefix_line_count} 行 / "
        f"叠加屏幕字 {report.screen_text_total_chars} 字 / 画内字 {report.diegetic_text_total_chars} 字 / "
        f"标签字 {report.label_text_total_chars} 字 / "
        f"规则词 {report.regulation_word_total_count} 次",
    ]
    if not report.violations:
        lines.append("  [PASS] 所有硬阈值检查通过")
        return "\n".join(lines)

    for v in report.violations:
        loc = f" @ {v.location}" if v.location else ""
        lines.append(f"  [{v.severity}] {v.rule}{loc}: {v.detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="单集场次执行稿确定性一致性校验（不参与质检放行，只做硬阈值越线检查）",
    )
    parser.add_argument(
        "target",
        help="单集 .md 文件路径，或 02-剧本/ 目录路径（递归找所有第NNN集.md）",
    )
    parser.add_argument(
        "--regulation-words",
        default="",
        help="规则词列表，逗号分隔（如 '命格,暗文,命债,见证人'）；空则跳过规则词检查",
    )
    parser.add_argument(
        "--target-seconds",
        type=int,
        default=75,
        help="目标单集时长（秒），决定有效正文下限；默认 75",
    )
    parser.add_argument(
        "--first-episode",
        action="store_true",
        help="标记为首集（按首集加长口径检查正文下限）",
    )
    parser.add_argument(
        "--project-dir",
        default="",
        help="项目根目录路径；如指定，从 <project>/项目状态.json 的 qualityThresholds 字段加载阈值覆盖",
    )
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"Target not found: {target}")

    episode_files = collect_episode_files(target)
    if not episode_files:
        raise SystemExit(f"No episode files found at: {target}")

    regulation_words = [w for w in args.regulation_words.split(",") if w.strip()]

    # 加载阈值：优先按 --project-dir，未给时尝试从 target 推断
    thresholds = Thresholds()
    if args.project_dir:
        project_dir = Path(args.project_dir).expanduser().resolve()
        thresholds = load_thresholds_from_project_state(project_dir)
    else:
        # 启发式：如果 target 是项目子路径（包含 02-剧本/ 或 第NNN集.md），向上找到项目根
        candidate = target if target.is_dir() else target.parent
        for _ in range(3):
            if (candidate / "项目状态.json").exists():
                thresholds = load_thresholds_from_project_state(candidate)
                break
            if candidate.parent == candidate:
                break
            candidate = candidate.parent

    has_failure = False
    for path in episode_files:
        is_first = args.first_episode or detect_episode_number(path) == 1
        report = check_episode(
            path,
            regulation_words=regulation_words,
            target_seconds=args.target_seconds,
            is_first_episode=is_first,
            thresholds=thresholds,
        )
        print(format_report(report))
        if not report.passed:
            has_failure = True

    print()
    if has_failure:
        print("[OVERALL] 至少一集发现 FAIL；建议先按提示修后再交独立质检")
        return 1
    print("[OVERALL] 全部 PASS（这只代表确定性硬阈值通过；戏剧判断仍由独立质检负责）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
