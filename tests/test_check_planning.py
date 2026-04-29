import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_planning.py"
SPEC = importlib.util.spec_from_file_location("check_planning", SCRIPT_PATH)
check_planning = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = check_planning
SPEC.loader.exec_module(check_planning)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CheckPlanningTests(unittest.TestCase):
    def test_clean_file_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目设定.md"
            write(
                f,
                "\n".join(
                    [
                        "# 项目设定",
                        "- 一句话题眼：北漂直播主播被恶意切流后报复反杀",
                        "- 发行平台：抖音",
                        "- 目标市场：国内",
                    ]
                ),
            )
            violations = check_planning.check_file(f)
            self.assertEqual(violations, [])

    def test_forbidden_exact_value_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目设定.md"
            write(f, "- 一句话题眼：待定\n- 发行平台：暂略\n- 目标市场：后补\n")
            violations = check_planning.check_file(f)
            self.assertEqual(len(violations), 3)
            self.assertEqual({v.rule for v in violations}, {"forbidden_exact"})

    def test_forbidden_case_insensitive_english(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目设定.md"
            write(f, "- 商业化模式：TBD\n- 参考作品：N/A\n- 题材敏感点：todo\n")
            violations = check_planning.check_file(f)
            self.assertEqual(len(violations), 3)

    def test_template_marker_left_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目设定.md"
            write(f, "- 一句话题眼： [MUST]\n- 发行平台： [SHOULD]\n")
            violations = check_planning.check_file(f)
            # 一行可能同时命中 forbidden_substring 和 template_marker_left；至少要有 marker_left
            rules = {v.rule for v in violations}
            self.assertIn("template_marker_left", rules)

    def test_empty_value_does_not_fail_alone(self):
        # 空值不单独由本脚本判定违禁；交独立复检判 MUST 字段是否实质有内容
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目设定.md"
            write(f, "- 一句话题眼：\n- 发行平台：\n")
            violations = check_planning.check_file(f)
            self.assertEqual(violations, [])

    def test_legitimate_未定_in_table_or_option_passes(self):
        # 模板里 "发行模式：平台端原生 / APP / 平台定制 / 未定" 是合法选项
        # 我们的违禁列表不包含"未定"，所以这种情况不会被误报
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目简报.md"
            write(f, "- 发行模式：未定\n")
            violations = check_planning.check_file(f)
            self.assertEqual(violations, [])

    def test_table_row_skipped(self):
        # 表格里出现"待定"不会被误报为字段值（表格行用 | 起始）
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "故事大纲.md"
            write(
                f,
                "\n".join(
                    [
                        "| 阶段 | 阶段目标 |",
                        "| --- | --- |",
                        "| 开篇 | 待定 |",  # 这里"待定"出现在表格,不该被报
                    ]
                ),
            )
            violations = check_planning.check_file(f)
            self.assertEqual(violations, [])

    def test_html_comment_block_skipped(self):
        # HTML 注释块里有"[MUST]"是模板自己的说明,不该被报
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目设定.md"
            write(
                f,
                "\n".join(
                    [
                        "<!-- 字段分级（行末标 [MUST]）：见每个字段行末标注 -->",
                        "- 一句话题眼：实际填好的内容",
                    ]
                ),
            )
            violations = check_planning.check_file(f)
            self.assertEqual(violations, [])

    def test_collect_files_in_project_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            write(project / "00-立项" / "项目简报.md", "- 项目名：演示\n")
            write(project / "01-策划" / "项目设定.md", "- 一句话题眼：演示\n")
            write(project / "01-策划" / "世界观设定.md", "- 主关系一句话：演示\n")
            write(project / "其它" / "无关.md", "- 字段：演示\n")  # 不在扫描目录,跳过

            files = check_planning.collect_target_files(project)
            names = {f.name for f in files}

            self.assertEqual(names, {"项目简报.md", "项目设定.md", "世界观设定.md"})

    def test_single_file_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目设定.md"
            write(f, "- 一句话题眼：演示\n")
            files = check_planning.collect_target_files(f)
            self.assertEqual(files, [f])

    def test_single_non_md_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "项目状态.json"
            write(f, "{}")
            files = check_planning.collect_target_files(f)
            self.assertEqual(files, [])

    def test_main_returns_0_for_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            write(project / "00-立项" / "项目简报.md", "- 项目名：演示\n")
            rc = check_planning.main([str(project)])
            self.assertEqual(rc, 0)

    def test_main_returns_1_for_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            write(project / "00-立项" / "项目简报.md", "- 项目名：待定\n")
            rc = check_planning.main([str(project)])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
