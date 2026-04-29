"""D17: 模板可解析性 + dogfood 可运行性的基本回归测试。

这些测试不验证生成结果的"剧本质量"，只验证：
1. 所有模板里 `- 字段名： [MUST]` / `[SHOULD]` / `[MAY]` 形式的字段
   都能被 `build_full_script.extract_field` 取到（即字段格式没出错）
2. dogfood 项目生成脚本的核心写文件函数不抛异常（至少能跑通）
"""
from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


build_full_script = load_module("build_full_script", "scripts/build_full_script.py")


# ===== 模板可解析性 =====

# 顶层字段行正则（必须从行首开始，不带缩进 — extract_field 只识别顶层 list item）
TOP_LEVEL_FIELD_RE = re.compile(r"^-\s+(?P<label>[^：:]+?)[：:](?P<rest>.*)$")
MARKER_RE = re.compile(r"\[(MUST|SHOULD|MAY)[^\]]*\]")


def collect_top_level_fields_with_marker(template_path: Path) -> list[tuple[int, str]]:
    """提取模板里**顶层**且带 MUST/SHOULD/MAY 标记的字段标签（含行号）。

    - 跳过 HTML 注释段
    - 跳过表格行
    - 跳过子 bullet（带缩进的 list item — 按 build_full_script docstring 子 bullet 不算字段）
    - 跳过空字段（无 marker，等用户填的纯占位槽）
    """
    fields: list[tuple[int, str]] = []
    in_comment = False
    text = template_path.read_text(encoding="utf-8")
    for index, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if "<!--" in stripped:
            in_comment = True
        if "-->" in stripped:
            in_comment = False
            continue
        if in_comment:
            continue
        if stripped.startswith("|"):  # 表格行
            continue
        # 必须从行首开始，不能有缩进（子 bullet 跳过）
        if not raw_line.startswith("-"):
            continue
        m = TOP_LEVEL_FIELD_RE.match(raw_line)
        if not m:
            continue
        label = m.group("label").strip().replace("`", "")
        rest = m.group("rest")
        if label.endswith(".md") or label.endswith(".json"):
            continue
        # 只关心带 marker 的字段
        if not MARKER_RE.search(rest):
            continue
        fields.append((index, label))
    return fields


class TemplateParseabilityTests(unittest.TestCase):
    """每个模板里能抽到的 MUST/SHOULD/MAY 字段都必须能被 extract_field 找到。"""

    def setUp(self):
        self.templates_dir = REPO_ROOT / "assets" / "templates"
        self.assertTrue(self.templates_dir.exists(), "assets/templates/ 目录缺失")

    def test_at_least_some_templates_have_marker_fields(self):
        """至少要有几个核心策划/立项模板带 MUST/SHOULD/MAY 标记。

        不是所有模板都需要 marker（日志型、表格型、freeform 试写样场等不需要），
        但核心模板（项目简报 / 锁题摘要 / 25 骨架等）必须带 marker，否则反作弊
        红线无从落地。
        """
        must_have_marker = {
            "00-项目简报模板.md",
            "02-锁题摘要模板.md",
            "25-正式策划产物骨架模板.md",
            "05-场次执行稿-中文模板.md",
            "06-场次执行稿-海外模板.md",
        }
        for template_name in must_have_marker:
            with self.subTest(template=template_name):
                template = self.templates_dir / template_name
                self.assertTrue(template.exists(), f"{template_name} 缺失")
                fields = collect_top_level_fields_with_marker(template)
                self.assertGreater(
                    len(fields),
                    0,
                    f"{template_name} 没有任何带 MUST/SHOULD/MAY 标记的顶层字段；"
                    f"反作弊红线无法对它生效",
                )

    def test_template_field_labels_are_extractable(self):
        """模板里每个字段标签都应该能被 extract_field 取回非 None 值。

        模板里字段值通常是 `[MUST]` / `[SHOULD]` / `[MAY]` 占位符；
        这测试只验证"字段能被识别"，不验证值本身。
        """
        for template in sorted(self.templates_dir.glob("*.md")):
            with self.subTest(template=template.name):
                text = template.read_text(encoding="utf-8")
                fields = collect_top_level_fields_with_marker(template)
                for line_no, label in fields:
                    value = build_full_script.extract_field(text, label)
                    self.assertIsNotNone(
                        value,
                        f"{template.name}:L{line_no} 字段 `{label}` 不能被 extract_field 解析",
                    )


# ===== dogfood 可运行性 =====


class DogfoodRunnabilityTests(unittest.TestCase):
    """dogfood 脚本能不能在临时目录里跑完不抛异常。

    不验证"生成结果是否通过 validate_delivery_inputs"——dogfood 是模拟数据，
    不一定满足 production 门禁。这测试只验证脚本不会因为 API 漂移崩掉。
    """

    def test_dogfood_writes_two_projects_without_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            # dogfood 模块全局有 ROOT / PROJECTS_DIR / GENERATED_AT，需要 monkey-patch
            dogfood = load_module(
                "dogfood_generate_validation_projects",
                "scripts/dogfood_generate_validation_projects.py",
            )
            dogfood.ROOT = tmp_root
            dogfood.PROJECTS_DIR = tmp_root / "projects"
            dogfood.PROJECTS_DIR.mkdir()

            # 运行两个项目生成器
            dogfood.cn_project()
            dogfood.us_project()

            # 检查关键文件是否落盘
            cn_state = dogfood.PROJECTS_DIR / "dogfood-cn-ruins-court-60" / "项目状态.json"
            us_state = dogfood.PROJECTS_DIR / "dogfood-us-nda-heiress-60" / "项目状态.json"
            self.assertTrue(cn_state.exists(), "国内项目状态文件未生成")
            self.assertTrue(us_state.exists(), "出海项目状态文件未生成")

    def test_dogfood_projects_pass_anti_cheat_check(self):
        """dogfood 项目自身必须过 check_planning 的反作弊红线。

        历史 bug：dogfood 曾经把字段值写成 "具体内容。[MUST]"，把模板标记当 suffix
        留下，违反 SKILL.md 的反作弊红线。这条测试确保再也不会回潮。
        """
        check_planning = load_module("check_planning", "scripts/check_planning.py")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            dogfood = load_module(
                "dogfood_generate_validation_projects_for_anti_cheat",
                "scripts/dogfood_generate_validation_projects.py",
            )
            dogfood.ROOT = tmp_root
            dogfood.PROJECTS_DIR = tmp_root / "projects"
            dogfood.PROJECTS_DIR.mkdir()
            dogfood.cn_project()
            dogfood.us_project()

            for slug in ("dogfood-cn-ruins-court-60", "dogfood-us-nda-heiress-60"):
                with self.subTest(project=slug):
                    project_dir = dogfood.PROJECTS_DIR / slug
                    files = check_planning.collect_target_files(project_dir)
                    self.assertGreater(len(files), 0, f"{slug} 没有可扫描的策划文件")
                    all_v: list = []
                    for f in files:
                        all_v.extend(check_planning.check_file(f))
                    if all_v:
                        details = "\n".join(
                            f"  {v.file.split('/')[-1]}:L{v.line} 字段 {v.field!r} = {v.value!r} ({v.rule})"
                            for v in all_v[:8]
                        )
                        self.fail(
                            f"{slug} 命中 {len(all_v)} 处反作弊违规，前 8 条:\n{details}"
                        )


if __name__ == "__main__":
    unittest.main()
