#!/usr/bin/env python3
"""机械交付汇总脚本（不参与质检放行）。

模板字段书写约定（`extract_field` 解析的前提）：
- 字段必须写成单层 Markdown list item：`- 字段名：值`
- 值可以悬挂缩进续行（下一行以空格或 Tab 开头），但禁止写成 `- 子 bullet`
- 出现 `- ` 开头或 `#` 开头的行会被视为当前字段结束
- 如果模板作者把字段值写成子 bullet，`extract_field` 将只读到空值

历史命名兼容：
- `项目设定.md` 是当前主名；老项目使用过 `项目圣经.md / season-bible.md`，这里保留回退查找
- `剧本圣经.md` 是当前主名；老项目使用过 `剧本策划总册.md`，仅在去重交付清单时识别
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# 当前主流程优先读取中文新文件名；旧文件名只作为历史项目兼容回退。
PREFERRED_FILES = {
    "planning": ["项目设定.md", "项目圣经.md", "season-bible.md"],
    "brief": ["项目简报.md", "project-brief.md"],
    "lock_summary": ["锁题摘要.md", "project-lock-summary.md"],
    "full_script": "完整剧本总稿.md",
    "planning_bible": "剧本圣经.md",
    "manifest": "交付清单.md",
    "production_brief": "制作理解稿.md",
    "production_params": "制作交付参数表.md",
    "douyin_clip_brief": "信息流投放素材切片说明.md",
    "overseas_scene_table": "海外制作版分场表.md",
}
PREFERRED_DIRS = {
    "planning": ["01-策划", "01-planning"],
    "intake": ["00-立项", "00-brief"],
    "scripts": ["02-剧本", "03-剧本", "04-批次", "04-batches"],
    "delivery": ["03-交付", "04-交付", "05-交付", "05-delivery"],
}

CANONICAL_MARKETS = {"抖音国内", "TikTok 欧美"}
MARKET_ALIASES = {
    "抖音国内": "抖音国内",
    "抖音": "抖音国内",
    "国内": "抖音国内",
    "中国国内": "抖音国内",
    "TikTok 欧美": "TikTok 欧美",
    "TikTok欧美": "TikTok 欧美",
    "TikTok 欧美市场": "TikTok 欧美",
    "TikTok美国": "TikTok 欧美",
    "TikTok 美国": "TikTok 欧美",
    "TikTok 美国市场": "TikTok 欧美",
    "TikTok US": "TikTok 欧美",
    "TikTok USA": "TikTok 欧美",
}
CHINESE_SECTION_NUMBERS = [
    "一",
    "二",
    "三",
    "四",
    "五",
    "六",
    "七",
    "八",
    "九",
    "十",
    "十一",
    "十二",
    "十三",
    "十四",
    "十五",
]
REQUIRED_PLANNING_FILES = [
    ("项目设定", "项目设定.md"),
    ("故事梗概", "故事梗概.md"),
    ("故事大纲", "故事大纲.md"),
    ("故事节拍表", "故事节拍表.md"),
    ("世界观设定", "世界观设定.md"),
    ("人物小传", "人物小传.md"),
    ("分集大纲", "分集大纲.md"),
]
COMPLETED_FULL_SCRIPT_PHASES = {"全剧复核已通过", "交付已通过"}
FORMAL_DELIVERY_STEPS = {"交付整合", "交付质检"}


class DeliveryInputError(Exception):
    """Raised when a formal delivery export would hide incomplete upstream work."""


def extract_field(text: str, label: str) -> str | None:
    target = re.sub(r"\s+", " ", label.replace("`", "").strip())
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        body = line[2:]
        delimiter = "：" if "：" in body else ":" if ":" in body else None
        if delimiter is None:
            continue
        field_label, value = body.split(delimiter, 1)
        normalized_label = re.sub(r"\s+", " ", field_label.replace("`", "").strip())
        if normalized_label != target:
            continue
        value_lines: list[str] = []
        inline_value = value.replace("`", "").strip()
        if inline_value:
            value_lines.append(inline_value)

        for following in lines[index + 1 :]:
            stripped_following = following.strip()
            if not stripped_following:
                if value_lines:
                    value_lines.append("")
                continue
            if stripped_following.startswith("- "):
                break
            if re.match(r"^#{1,6}\s", stripped_following):
                break
            if not following.startswith((" ", "\t")):
                break
            value_lines.append(stripped_following.replace("`", "").strip())

        normalized_value = "\n".join(line for line in value_lines).strip()
        return normalized_value or None
    return None


def normalize_market(value: str | None) -> str:
    if not value:
        return ""
    normalized = re.sub(r"\s+", " ", value.replace("`", "").strip())
    return MARKET_ALIASES.get(normalized, normalized if normalized in CANONICAL_MARKETS else "")


def extract_episode_count(value: str | None) -> str:
    if not value:
        return ""
    match = re.search(r"(\d+)", value)
    return match.group(1) if match else ""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_leading_title(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and re.match(r"^#\s+", lines[0].strip()):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def demote_markdown_headings(text: str, levels: int = 1) -> str:
    """Demote embedded Markdown headings so source docs nest under bible sections."""
    prefix = "#" * levels
    demoted_lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})(\s+.*)$", line)
        if match:
            hashes, rest = match.groups()
            demoted_lines.append(f"{hashes}{prefix}{rest}" if len(hashes) + levels <= 6 else line)
        else:
            demoted_lines.append(line)
    return "\n".join(demoted_lines).strip()


def prepare_embedded_source_text(text: str) -> str:
    return demote_markdown_headings(strip_leading_title(text))


def extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def extract_section_body(text: str, heading: str, level: int = 2) -> str | None:
    lines = text.splitlines()
    pattern = re.compile(rf"^#{{{level}}}\s+{re.escape(heading)}\s*$")
    in_section = False
    collected: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not in_section:
            if pattern.match(stripped):
                in_section = True
            continue

        if re.match(rf"^#{{1,{level}}}\s+", stripped):
            break
        collected.append(line)

    if not collected:
        return None
    body = "\n".join(collected).strip()
    return body or None


def detect_episode_number(path: Path) -> int:
    match = re.search(r"(?:ep|第)(\d{3})(?:集)?\.md$", path.name, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid episode filename: {path.name}")
    return int(match.group(1))


def resolve_existing_file(base_dir: Path, candidates: list[str]) -> Path | None:
    for name in candidates:
        candidate = base_dir / name
        if candidate.exists():
            return candidate
    return None


def resolve_existing_dir(project_dir: Path, candidates: list[str]) -> Path:
    for name in candidates:
        candidate = project_dir / name
        if candidate.exists():
            return candidate
    return project_dir / candidates[0]


def resolve_first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def project_delivery_mode(project_dir: Path) -> str:
    state_path = project_dir / "项目状态.json"
    if not state_path.exists():
        return "standard"
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError:
        return "standard"
    if not isinstance(state, dict):
        return "standard"
    value = state.get("deliveryMode")
    return value if value in {"planning-only", "standard", "production-enhanced"} else "standard"


def load_project_state(project_dir: Path) -> dict:
    state_path = project_dir / "项目状态.json"
    if not state_path.exists():
        raise DeliveryInputError("缺少 `项目状态.json`；不能生成正式交付包。")
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError as exc:
        raise DeliveryInputError(f"`项目状态.json` 不是合法 JSON：{exc}") from exc
    if not isinstance(state, dict):
        raise DeliveryInputError("`项目状态.json` 顶层必须是对象。")
    return state


def collect_episode_files(project_dir: Path) -> list[Path]:
    script_root = resolve_existing_dir(project_dir, PREFERRED_DIRS["scripts"])
    direct_files = sorted(
        [path for path in script_root.glob("*.md") if re.search(r"(?:ep|第)\d{3}(?:集)?\.md$", path.name, re.IGNORECASE)],
        key=detect_episode_number,
    )
    if direct_files:
        return direct_files

    nested_files = sorted(
        [path for path in script_root.glob("*/*.md") if re.search(r"(?:ep|第)\d{3}(?:集)?\.md$", path.name, re.IGNORECASE)],
        key=detect_episode_number,
    )
    return nested_files


def project_metadata(project_dir: Path) -> dict[str, str]:
    planning_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["planning"])
    intake_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["intake"])
    planning_file = resolve_existing_file(planning_dir, PREFERRED_FILES["planning"])
    brief_file = resolve_existing_file(intake_dir, PREFERRED_FILES["brief"])
    lock_summary = resolve_existing_file(intake_dir, PREFERRED_FILES["lock_summary"])

    data = {
        "project_name": project_dir.name,
        "market": "",
        "format": "场次执行稿",
        "shape": "AI漫剧",
        "target_episodes": "",
    }

    if brief_file and brief_file.exists():
        text = read_text(brief_file)
        data["project_name"] = extract_field(text, "项目名") or data["project_name"]
        data["market"] = normalize_market(extract_field(text, "目标市场")) or data["market"]
        target = extract_episode_count(extract_field(text, "总集数"))
        if target:
            data["target_episodes"] = target

    if lock_summary and lock_summary.exists():
        text = read_text(lock_summary)
        data["market"] = normalize_market(extract_field(text, "目标市场")) or data["market"]
        target = extract_episode_count(extract_field(text, "总集数"))
        if target:
            data["target_episodes"] = target

    # 项目设定.md 不再当成元数据真相源；市场和总集数以 项目简报.md / 锁题摘要.md 为准。
    # 这里只是兼容历史项目里 项目设定.md 含 "推荐规格" 字段的情况，未来可彻底删除。
    if planning_file and planning_file.exists() and not data["target_episodes"]:
        text = read_text(planning_file)
        spec = extract_field(text, "推荐规格")
        if spec:
            match = re.search(r"(\d+)\s*集", spec)
            if match:
                data["target_episodes"] = match.group(1)

    return data


def required_planning_sources(project_dir: Path) -> list[tuple[str, Path]]:
    planning_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["planning"])
    sources = [(label, planning_dir / filename) for label, filename in REQUIRED_PLANNING_FILES]
    metadata = project_metadata(project_dir)
    target = int(metadata["target_episodes"]) if metadata["target_episodes"] else None
    if target is not None and target >= 30:
        sources.append(("阶段大纲", planning_dir / "阶段大纲.md"))
    return sources


def detect_enhanced_recommendation_reasons(project_dir: Path) -> list[str]:
    """检测项目是否应当推荐 production-enhanced 模式。

    返回触发原因列表；空列表表示不强烈推荐。判断依据：
    - 海外项目（市场为 TikTok 欧美）
    - 长线项目（总集数 >= 30）
    - 资产重项目（已存在 场景参考卡.md / 道具设定卡.md）
    """
    reasons: list[str] = []
    metadata = project_metadata(project_dir)

    if metadata.get("market") == "TikTok 欧美":
        reasons.append("项目市场为 TikTok 欧美，需要 海外制作版分场表 等增强包文件")

    target_text = metadata.get("target_episodes") or ""
    if target_text:
        try:
            if int(target_text) >= 30:
                reasons.append("总集数 >= 30，长线项目应使用增强包整理资产")
        except ValueError:
            pass

    planning_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["planning"])
    asset_files = ["场景参考卡.md", "道具设定卡.md"]
    if any((planning_dir / name).exists() for name in asset_files):
        reasons.append("策划目录已存在 场景参考卡 / 道具设定卡 工作版，资产重项目默认应进入增强包")

    return reasons


def warn_enhanced_recommendation(project_dir: Path) -> None:
    """如果项目命中 production-enhanced 推荐条件但当前 deliveryMode 为 standard，打印警告。

    不阻塞流程；只是打印 stderr 提示，避免资产重 / 海外项目意外漏包。
    """
    try:
        state = load_project_state(project_dir)
    except DeliveryInputError:
        return

    delivery_mode = state.get("deliveryMode")
    if delivery_mode != "standard":
        return

    reasons = detect_enhanced_recommendation_reasons(project_dir)
    if not reasons:
        return

    sys.stderr.write(
        "\n[WARN] 当前 deliveryMode = standard，但项目命中以下增强包推荐条件：\n"
    )
    for reason in reasons:
        sys.stderr.write(f"  - {reason}\n")
    sys.stderr.write(
        "建议改为 production-enhanced；若坚持 standard，必须在 90-内部工作稿/质检检查点.md 记录风险接受理由。\n"
        "见 references/05-交付细则.md 与 references/14-制作交付整理.md。\n\n"
    )


def required_enhanced_delivery_files(project_dir: Path, delivery_dir: Path) -> list[tuple[str, Path]]:
    """Return production-enhanced deliverables that must already exist for formal export.

    `build_full_script.py` only does deterministic standard bundle assembly. Enhanced
    files require editorial/production judgment, so formal enhanced export should fail
    if the model has not prepared those files first.
    """
    metadata = project_metadata(project_dir)
    required = [
        ("制作理解稿", delivery_dir / PREFERRED_FILES["production_brief"]),
        ("制作交付参数表", delivery_dir / PREFERRED_FILES["production_params"]),
    ]
    if metadata.get("market") == "抖音国内":
        required.append(("信息流投放素材切片说明", delivery_dir / PREFERRED_FILES["douyin_clip_brief"]))
    if metadata.get("market") == "TikTok 欧美":
        required.append(("海外制作版分场表", delivery_dir / PREFERRED_FILES["overseas_scene_table"]))

    planning_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["planning"])
    for filename, label in (("场景参考卡.md", "场景参考卡"), ("道具设定卡.md", "道具设定卡")):
        if (planning_dir / filename).exists():
            required.append((label, delivery_dir / filename))

    return required


def validate_delivery_inputs(project_dir: Path, episode_files: list[Path]) -> None:
    errors: list[str] = []

    try:
        state = load_project_state(project_dir)
    except DeliveryInputError as exc:
        state = {}
        errors.append(str(exc))

    if state:
        current_step = state.get("currentStep")
        if current_step not in FORMAL_DELIVERY_STEPS:
            errors.append("`currentStep` 必须为 `交付整合` 或 `交付质检`，不能在非交付节点生成正式交付包。")

        delivery_mode = state.get("deliveryMode")
        if delivery_mode not in {"standard", "production-enhanced"}:
            errors.append("`deliveryMode` 必须为 `standard` 或 `production-enhanced`；不能从 `planning-only` 或未知模式生成正式交付包。")

        last_completed = state.get("lastCompletedPhase")
        script_progress = state.get("scriptProgress")
        if last_completed not in COMPLETED_FULL_SCRIPT_PHASES:
            errors.append("缺少 `T15 全剧复核` 通过状态：`lastCompletedPhase` 必须为 `全剧复核已通过` 或 `交付已通过`。")
        if not isinstance(script_progress, dict) or script_progress.get("fullScriptReviewDone") is not True:
            errors.append("缺少 `T15 全剧复核` 通过状态：`scriptProgress.fullScriptReviewDone` 必须为 `true`。")

        change_control = state.get("changeControl")
        if isinstance(change_control, dict) and change_control.get("pendingRollback") is True:
            errors.append("`changeControl.pendingRollback = true`，存在未闭环的上游改动回退，不能生成正式交付包。")

        qc_status = state.get("qcStatus")
        if not isinstance(qc_status, dict):
            errors.append("`项目状态.json.qcStatus` 缺失或不是对象。")
        else:
            for gate in ("kickoff", "planningFoundation", "planningStructure"):
                if qc_status.get(gate) != "已通过":
                    errors.append(f"`qcStatus.{gate}` 不是 `已通过`；不能汇总正式交付包。")
            if qc_status.get("outline") != "已通过":
                errors.append("`qcStatus.outline` 不是 `已通过`；不能汇总正式剧本。")
            script_batches = qc_status.get("scriptBatches")
            if not isinstance(script_batches, list) or not script_batches:
                errors.append("`qcStatus.scriptBatches` 缺少已通过批次记录。")
            else:
                failed_batches = [
                    str(batch.get("range") or batch.get("batch") or index + 1)
                    for index, batch in enumerate(script_batches)
                    if not isinstance(batch, dict) or batch.get("status") != "已通过"
                ]
                if failed_batches:
                    errors.append("存在未通过的剧本批次：" + "，".join(failed_batches))

        if delivery_mode == "production-enhanced":
            delivery_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["delivery"])
            missing_enhanced = [
                f"`{path.relative_to(project_dir)}`（{label}）"
                for label, path in required_enhanced_delivery_files(project_dir, delivery_dir)
                if not path.exists()
            ]
            if missing_enhanced:
                errors.append("production-enhanced 模式缺少增强包文件：" + "，".join(missing_enhanced))

    intake_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["intake"])
    if not (intake_dir / "锁题摘要.md").exists() and not (intake_dir / "项目简报.md").exists():
        errors.append("缺少 `00-立项/锁题摘要.md` 或 `00-立项/项目简报.md`。")

    for label, path in required_planning_sources(project_dir):
        if not path.exists():
            errors.append(f"缺少正式策划源文件 `{path.relative_to(project_dir)}`（{label}）。")

    metadata = project_metadata(project_dir)
    if metadata["target_episodes"]:
        target = int(metadata["target_episodes"])
        episode_numbers = [detect_episode_number(path) for path in episode_files]
        expected = list(range(1, target + 1))
        if episode_numbers != expected:
            missing = [number for number in expected if number not in set(episode_numbers)]
            extras = [number for number in episode_numbers if number > target]
            details: list[str] = []
            if missing:
                details.append("缺失 " + "，".join(f"第{number:03d}集" for number in missing[:8]))
            if extras:
                details.append("超出目标 " + "，".join(f"第{number:03d}集" for number in extras[:8]))
            errors.append("剧本集数与目标总集数不一致：" + "；".join(details or ["范围不连续"]))

    if errors:
        raise DeliveryInputError("\n".join(f"- {error}" for error in errors))


def build_full_script(project_dir: Path, episode_files: list[Path]) -> str:
    metadata = project_metadata(project_dir)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    first_ep = detect_episode_number(episode_files[0])
    last_ep = detect_episode_number(episode_files[-1])
    market_display = metadata["market"] or "未在项目文件中写明"

    header = [
        f"# {metadata['project_name']}",
        "",
        "## 交付信息",
        f"- 项目目录：`{project_dir}`",
        f"- 市场：{market_display}",
        f"- 形态：{metadata['shape']}",
        f"- 正文格式：{metadata['format']}",
        f"- 汇总范围：第{first_ep:03d}集-第{last_ep:03d}集",
        f"- 汇总集数：{len(episode_files)}",
        f"- 生成时间：{generated_at}",
        "",
        "---",
        "",
    ]

    sections: list[str] = []
    for path in episode_files:
        raw_text = read_text(path)
        title = extract_title(raw_text, path.stem)
        scene_body = extract_section_body(raw_text, "场次正文", level=2)
        if scene_body is None:
            sections.append(raw_text.strip())
        else:
            sections.extend(
                [
                    f"# {title}",
                    "",
                    "## 场次正文",
                    "",
                    scene_body.strip(),
                ]
            )
        sections.append("")
        sections.append("---")
        sections.append("")

    return "\n".join(header + sections).rstrip() + "\n"


def build_planning_bible(project_dir: Path, delivery_dir: Path) -> str:
    metadata = project_metadata(project_dir)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    planning_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["planning"])
    intake_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["intake"])
    market_display = metadata["market"] or "未在项目文件中写明"
    include_enhanced = project_delivery_mode(project_dir) == "production-enhanced"

    header = [
        f"# {metadata['project_name']} - 剧本圣经",
        "",
        "## 交付信息",
        f"- 项目目录：`{project_dir}`",
        f"- 市场：{market_display}",
        f"- 汇总时间：{generated_at}",
        "- 说明：本文件在交付阶段汇总已通过质检的分项策划，用于统一交接项目定位、结构推进、世界、角色和关键资产，不替代 `完整剧本总稿.md`。",
        "",
    ]

    source_specs: list[tuple[str, str, list[Path], bool]] = [
        ("卖点与项目定位", "锁题摘要.md", [intake_dir / "锁题摘要.md", intake_dir / "项目简报.md"], True),
        ("项目设定", "项目设定.md", [planning_dir / "项目设定.md"], True),
        ("故事梗概", "故事梗概.md", [planning_dir / "故事梗概.md"], True),
        ("故事大纲", "故事大纲.md", [planning_dir / "故事大纲.md"], True),
        ("故事节拍表", "故事节拍表.md", [planning_dir / "故事节拍表.md"], True),
        ("阶段大纲", "阶段大纲.md", [planning_dir / "阶段大纲.md"], (planning_dir / "阶段大纲.md").exists()),
        ("世界观设定", "世界观设定.md", [planning_dir / "世界观设定.md"], True),
        ("人物小传", "人物小传.md", [planning_dir / "人物小传.md"], True),
        (
            "制作理解稿",
            PREFERRED_FILES["production_brief"],
            [delivery_dir / PREFERRED_FILES["production_brief"]],
            include_enhanced and (delivery_dir / PREFERRED_FILES["production_brief"]).exists(),
        ),
        (
            "制作交付参数表",
            PREFERRED_FILES["production_params"],
            [delivery_dir / PREFERRED_FILES["production_params"]],
            include_enhanced and (delivery_dir / PREFERRED_FILES["production_params"]).exists(),
        ),
        (
            "信息流投放素材切片说明",
            PREFERRED_FILES["douyin_clip_brief"],
            [delivery_dir / PREFERRED_FILES["douyin_clip_brief"]],
            include_enhanced and market_display == "抖音国内" and (delivery_dir / PREFERRED_FILES["douyin_clip_brief"]).exists(),
        ),
        ("场景参考卡", "场景参考卡.md", [delivery_dir / "场景参考卡.md"], (delivery_dir / "场景参考卡.md").exists()),
        ("道具设定卡", "道具设定卡.md", [delivery_dir / "道具设定卡.md"], (delivery_dir / "道具设定卡.md").exists()),
    ]

    sections: list[str] = []
    included_specs = [(title, filename, candidates) for title, filename, candidates, include in source_specs if include]
    for index, (title, filename, candidates) in enumerate(included_specs):
        number = CHINESE_SECTION_NUMBERS[index] if index < len(CHINESE_SECTION_NUMBERS) else str(index + 1)
        heading = f"{number}、{title}"
        source_path = resolve_first_existing(candidates)
        sections.extend([f"## {heading}", ""])
        if source_path is None:
            sections.extend([f"> 当前项目未单独整理 `{filename}`。", ""])
        else:
            sections.extend([prepare_embedded_source_text(read_text(source_path)), ""])
        sections.extend(["---", ""])

    return "\n".join(header + sections).rstrip() + "\n"


def build_manifest(project_dir: Path, delivery_dir: Path, episode_files: list[Path]) -> str:
    metadata = project_metadata(project_dir)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    delivery_mode = project_delivery_mode(project_dir)
    first_ep = detect_episode_number(episode_files[0])
    last_ep = detect_episode_number(episode_files[-1])
    episode_numbers = [detect_episode_number(path) for path in episode_files]
    target_episodes = int(metadata["target_episodes"]) if metadata["target_episodes"] else None
    market_display = metadata["market"] or "未在项目文件中写明"
    target_display = str(target_episodes) if target_episodes is not None else "未在项目文件中写明"
    expected_start = 1 if target_episodes is not None else first_ep
    expected_end = target_episodes if target_episodes is not None else last_ep
    missing_numbers = [number for number in range(expected_start, expected_end + 1) if number not in set(episode_numbers)]
    if target_episodes is None:
        full_status = "按当前已完成集数汇总"
    else:
        full_status = "是" if episode_numbers == list(range(1, target_episodes + 1)) else "否"
    existing_files = sorted({path.name for path in delivery_dir.glob("*.md")} | {PREFERRED_FILES["manifest"]})
    if PREFERRED_FILES["planning_bible"] in existing_files:
        existing_files = [name for name in existing_files if name != "剧本策划总册.md"]
    version_display = (
        "production-enhanced 制作增强正式交付版"
        if delivery_mode == "production-enhanced"
        else "standard 标准正式交付版"
    )
    if missing_numbers:
        missing_display = ", ".join(f"第{number:03d}集" for number in missing_numbers[:8])
        if len(missing_numbers) > 8:
            missing_display += " ..."
    else:
        missing_display = "无"

    return "\n".join(
        [
            "# 剧本交付清单",
            "",
            "## 一、项目基本信息",
            "",
            f"- 项目名：{metadata['project_name']}",
            f"- 市场：{market_display}",
            f"- 形态：{metadata['shape']}",
            f"- 当前交付版本：{version_display}",
            f"- 交付日期：{generated_at}",
            f"- 目标总集数：{target_display}",
            "",
            "## 二、本次交付包含",
            "",
            *[f"- `{name}`" for name in existing_files],
            "",
            "## 三、剧本范围",
            "",
            f"- 已交付集数：{len(episode_files)}",
            f"- 是否全季总稿：{full_status}",
            f"- 当前交付到：第{last_ep:03d}集",
            f"- 当前汇总范围：第{first_ep:03d}集-第{last_ep:03d}集",
            f"- 当前应补缺失集：{missing_display}",
            "",
            "## 四、版本说明",
            "",
            f"- 本版基于已完成单集稿自动汇总：第{first_ep:03d}集-第{last_ep:03d}集",
            "- 说明：本清单由汇总脚本按当前 deliveryMode 生成；制作备注以交付包内对应文件为准。",
            "",
        ]
    )


def collect_source_files_for_check(project_dir: Path, episode_files: list[Path]) -> list[Path]:
    """收集所有可能影响交付包的源文件，用于 --check-mode 的 mtime 比较。"""
    source_files: list[Path] = list(episode_files)

    intake_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["intake"])
    for name in ("锁题摘要.md", "项目简报.md"):
        candidate = intake_dir / name
        if candidate.exists():
            source_files.append(candidate)

    planning_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["planning"])
    for label, path in required_planning_sources(project_dir):
        if path.exists():
            source_files.append(path)
    for name in ("场景参考卡.md", "道具设定卡.md"):
        candidate = planning_dir / name
        if candidate.exists():
            source_files.append(candidate)

    state_path = project_dir / "项目状态.json"
    if state_path.exists():
        source_files.append(state_path)

    delivery_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["delivery"])
    if project_delivery_mode(project_dir) == "production-enhanced":
        for _label, path in required_enhanced_delivery_files(project_dir, delivery_dir):
            if path.exists():
                source_files.append(path)

    return source_files


def run_check_mode(project_dir: Path, episode_files: list[Path]) -> int:
    """检查交付包是否落后于源文件 mtime，返回 0 表示同步、1 表示需要重生成。"""
    delivery_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["delivery"])
    generated_deliverables = [
        delivery_dir / PREFERRED_FILES["full_script"],
        delivery_dir / PREFERRED_FILES["planning_bible"],
        delivery_dir / PREFERRED_FILES["manifest"],
    ]
    required_files = list(generated_deliverables)
    if project_delivery_mode(project_dir) == "production-enhanced":
        required_files.extend(path for _label, path in required_enhanced_delivery_files(project_dir, delivery_dir))

    missing = [path for path in required_files if not path.exists()]
    if missing:
        sys.stderr.write("[check-mode] 交付包尚未生成，缺少：\n")
        for path in missing:
            sys.stderr.write(f"  - {path.relative_to(project_dir)}\n")
        sys.stderr.write("请运行 build_full_script.py（不带 --check-mode）生成交付包。\n")
        return 1

    oldest_delivery_mtime = min(path.stat().st_mtime for path in generated_deliverables)
    source_files = collect_source_files_for_check(project_dir, episode_files)
    newer_sources = [
        path for path in source_files
        if path.stat().st_mtime > oldest_delivery_mtime
    ]

    if not newer_sources:
        print("[check-mode] 交付包与源文件同步，无需重生成。")
        return 0

    sys.stderr.write("[check-mode] 检测到源文件已更新，交付包需要重新生成：\n")
    for path in sorted(newer_sources):
        sys.stderr.write(f"  - {path.relative_to(project_dir)}\n")
    sys.stderr.write("请运行 build_full_script.py（不带 --check-mode）刷新交付包。\n")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build delivery bundle files from planning and episode sources.")
    parser.add_argument("--draft", action="store_true", help="Skip formal gate/source validation and generate a draft bundle.")
    parser.add_argument(
        "--check-mode",
        action="store_true",
        help="Compare delivery bundle mtime against source files; report stale bundle without regenerating.",
    )
    parser.add_argument("project_dir", help="Path to project root, e.g. projects/my-project")
    args = parser.parse_args(argv)

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        raise SystemExit(f"Project directory not found: {project_dir}")

    episode_files = collect_episode_files(project_dir)
    if not episode_files:
        raise SystemExit(f"No episode files found under: {resolve_existing_dir(project_dir, PREFERRED_DIRS['scripts'])}")

    if args.check_mode:
        return run_check_mode(project_dir, episode_files)

    if not args.draft:
        try:
            validate_delivery_inputs(project_dir, episode_files)
        except DeliveryInputError as exc:
            raise SystemExit(f"Delivery input validation failed:\n{exc}") from exc

    warn_enhanced_recommendation(project_dir)

    delivery_dir = resolve_existing_dir(project_dir, PREFERRED_DIRS["delivery"])
    delivery_dir.mkdir(parents=True, exist_ok=True)

    full_script_path = delivery_dir / PREFERRED_FILES["full_script"]
    planning_bible_path = delivery_dir / PREFERRED_FILES["planning_bible"]
    manifest_path = delivery_dir / PREFERRED_FILES["manifest"]

    full_script_path.write_text(build_full_script(project_dir, episode_files), encoding="utf-8")
    planning_bible_path.write_text(build_planning_bible(project_dir, delivery_dir), encoding="utf-8")
    manifest_path.write_text(build_manifest(project_dir, delivery_dir, episode_files), encoding="utf-8")

    print(f"Wrote {full_script_path}")
    print(f"Wrote {planning_bible_path}")
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
