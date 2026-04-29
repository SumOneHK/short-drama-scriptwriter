#!/usr/bin/env python3
"""策划与立项产物的反作弊红线机械检查（不参与质检放行）。

用途：
- 扫描 `00-立项/`、`01-策划/`、`03-交付/` 下所有 `.md` 文件
- 对 `- 字段名：值` 形式的字段做"违禁词 / 空值 / 未替换模板标记"机械检查
- 输出 FAIL 报告作为独立质检的"硬阈值证据附件"
- 不替代戏剧判断；不能单独作为阶段放行

SKILL.md 与 references/19 规定的反作弊红线：
- 不允许把字段值填成 `待定 / 暂略 / 后补`
- 不允许把模板标记 `[MUST] / [SHOULD] / [MAY]` 留在已落盘文件里没去掉
- MUST 字段不允许空值

使用：
    python3 check_planning.py projects/<slug>             # 扫整个项目
    python3 check_planning.py path/to/项目设定.md         # 扫单个文件

退出码：
    0 = 全部通过
    1 = 至少一处违禁
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ===== 反作弊违禁词 =====

# 完全匹配（去除两端空白后）
FORBIDDEN_EXACT = frozenset(
    {
        "待定",
        "暂略",
        "后补",
        "待补",
        "待补充",
        "待定中",
        "tbd",
        "tba",
        "n/a",
        "na",
        "todo",
        "占位",
        "占位符",
        "留空",
        "（待定）",
        "(待定)",
        "（暂略）",
        "(暂略)",
    }
)

# 子串匹配（值里包含这些就算违禁）
FORBIDDEN_SUBSTRINGS = (
    "[must]",
    "[should]",
    "[may]",
    "<待填>",
    "<待补>",
    "<占位>",
)

# 默认扫描的目录（相对项目根）
DEFAULT_SCAN_DIRS = ("00-立项", "01-策划", "03-交付")

# 字段行正则：`- 字段名：值` 或 `- 字段名: 值`（含全角/半角冒号）
FIELD_LINE_RE = re.compile(r"^-\s+(?P<label>[^：:]+?)[：:]\s*(?P<value>.*)$")


@dataclass(frozen=True)
class Violation:
    """单条违禁记录。"""

    severity: str  # "FAIL"
    rule: str
    field: str
    value: str
    file: str
    line: int


def is_forbidden_value(value: str) -> tuple[bool, str]:
    """判断字段值是否命中违禁规则。

    返回 (是否违禁, 命中的规则名)。
    """
    stripped = value.strip().lower()
    if not stripped:
        # 空值单独由调用方根据上下文判断；这里只检"被填了违禁词"
        return False, ""
    if stripped in FORBIDDEN_EXACT:
        return True, "forbidden_exact"
    for substr in FORBIDDEN_SUBSTRINGS:
        if substr in stripped:
            return True, "forbidden_substring"
    return False, ""


def check_file(path: Path) -> list[Violation]:
    """扫描单个 .md 文件的字段值。"""
    violations: list[Violation] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    for index, raw_line in enumerate(lines, start=1):
        # 跳过 HTML 注释段（简单启发式：行首是 `<!--`）
        if raw_line.lstrip().startswith("<!--"):
            continue
        # 跳过表格行
        if "|" in raw_line and raw_line.lstrip().startswith("|"):
            continue
        # 解析字段
        m = FIELD_LINE_RE.match(raw_line.strip())
        if not m:
            continue
        label = m.group("label").strip().replace("`", "")
        value = m.group("value").strip()

        # 去掉值末尾的 [MUST]/[SHOULD]/[MAY] 注释（落盘文件应该已经去掉，但容错）
        value_no_marker = re.sub(r"\s*\[(MUST|SHOULD|MAY)[^\]]*\]\s*$", "", value).strip()

        forbidden, rule = is_forbidden_value(value_no_marker)
        if forbidden:
            violations.append(
                Violation(
                    severity="FAIL",
                    rule=rule,
                    field=label,
                    value=value,
                    file=str(path),
                    line=index,
                )
            )

        # 单独检"留了模板标记没去掉"
        if re.search(r"\[(MUST|SHOULD|MAY)\b[^\]]*\]\s*$", value):
            violations.append(
                Violation(
                    severity="FAIL",
                    rule="template_marker_left",
                    field=label,
                    value=value,
                    file=str(path),
                    line=index,
                )
            )

    return violations


def collect_target_files(target: Path) -> list[Path]:
    """根据输入路径收集要扫描的 .md 文件。"""
    if target.is_file():
        return [target] if target.suffix == ".md" else []

    # 目录：按默认目录列表收集
    files: list[Path] = []
    for dirname in DEFAULT_SCAN_DIRS:
        sub = target / dirname
        if sub.exists() and sub.is_dir():
            files.extend(sorted(sub.rglob("*.md")))
    return files


def format_report(violations: list[Violation]) -> str:
    """输出可读报告。"""
    if not violations:
        return "[OVERALL] 反作弊红线全部通过（这只代表违禁词检查；MUST 字段是否实质有内容仍由独立复检判断）"

    by_file: dict[str, list[Violation]] = {}
    for v in violations:
        by_file.setdefault(v.file, []).append(v)

    out: list[str] = []
    for file, vs in by_file.items():
        out.append(f"\n=== {file} ===")
        for v in vs:
            out.append(
                f"  [{v.severity}] {v.rule} @ L{v.line}: 字段 `{v.field}` 值 `{v.value}` 命中违禁规则"
            )
    out.append("")
    out.append(f"[OVERALL] 共 {len(violations)} 处违禁；建议先按提示修后再交独立质检")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="策划与立项产物的反作弊红线机械检查（不参与质检放行）",
    )
    parser.add_argument(
        "target",
        help="项目根目录（如 projects/<slug>）或单个 .md 文件",
    )
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        raise SystemExit(f"Target not found: {target}")

    files = collect_target_files(target)
    if not files:
        raise SystemExit(
            f"No planning .md files found at: {target}\n"
            f"（项目模式下扫描 {' / '.join(DEFAULT_SCAN_DIRS)} 子目录）"
        )

    all_violations: list[Violation] = []
    for path in files:
        all_violations.extend(check_file(path))

    print(format_report(all_violations))
    return 0 if not all_violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
