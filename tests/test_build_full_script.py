import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_full_script.py"
SPEC = importlib.util.spec_from_file_location("build_full_script", SCRIPT_PATH)
build_full_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_full_script)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_project(
    root: Path,
    *,
    target_episodes: int = 2,
    batch_status: str = "已通过",
    delivery_mode: str = "standard",
    market: str = "抖音国内",
    full_script_review_done: bool = True,
    last_completed_phase: str = "全剧复核已通过",
    current_step: str = "交付整合",
    pending_rollback: bool = False,
) -> Path:
    project = root / "demo-project"
    write(
        project / "项目状态.json",
        json.dumps(
            {
                "currentStep": current_step,
                "projectPhase": "交付",
                "lastCompletedPhase": last_completed_phase,
                "deliveryMode": delivery_mode,
                "scriptProgress": {
                    "completedRanges": ["001-002"],
                    "currentRange": "",
                    "nextRange": "",
                    "fullScriptReviewDone": full_script_review_done,
                },
                "changeControl": {
                    "pendingRollback": pending_rollback,
                    "sourceStep": "",
                    "sourceFiles": [],
                    "affectedGates": [],
                    "reason": "",
                    "triggeredAt": "",
                    "resolvedAt": "",
                },
                "qcStatus": {
                    "kickoff": "已通过",
                    "planningFoundation": "已通过",
                    "planningStructure": "已通过",
                    "outline": "已通过",
                    "scriptBatches": [{"range": "001-002", "status": batch_status}],
                    "delivery": "未检查",
                },
            },
            ensure_ascii=False,
        ),
    )
    write(project / "00-立项" / "项目简报.md", f"# 项目简报\n\n- 项目名：演示项目\n- 目标市场：{market}\n- 总集数：{target_episodes}\n")
    write(project / "00-立项" / "锁题摘要.md", f"# 锁题摘要\n\n- 目标市场：{market}\n- 总集数：{target_episodes}\n")
    for filename in [
        "项目设定.md",
        "故事梗概.md",
        "故事大纲.md",
        "故事节拍表.md",
        "世界观设定.md",
        "人物小传.md",
        "分集大纲.md",
    ]:
        write(project / "01-策划" / filename, f"# {filename[:-3]}\n\n正式内容。\n")
    for number in range(1, target_episodes + 1):
        write(
            project / "02-剧本" / f"第{number:03d}集.md",
            f"# 第{number:03d}集\n\n## 本集创作简卡\n\n- 开场承接：略\n\n## 场次正文\n\n### {number}-1 日内 地点\n\n人物：角色A\n\n△ 角色A做出选择。\n\n角色A：台词。\n\n## 本集回填\n\n- 下一集必须承接：略\n",
        )
    return project


class BuildFullScriptTests(unittest.TestCase):
    def test_formal_export_requires_required_planning_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp))
            (project / "01-策划" / "人物小传.md").unlink()

            with self.assertRaises(build_full_script.DeliveryInputError) as context:
                build_full_script.validate_delivery_inputs(project, build_full_script.collect_episode_files(project))

            self.assertIn("人物小传", str(context.exception))

    def test_formal_export_requires_approved_script_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), batch_status="需修改")

            with self.assertRaises(build_full_script.DeliveryInputError) as context:
                build_full_script.validate_delivery_inputs(project, build_full_script.collect_episode_files(project))

            self.assertIn("未通过的剧本批次", str(context.exception))

    def test_formal_export_requires_full_script_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(
                Path(tmp),
                full_script_review_done=False,
                last_completed_phase="剧本批次已全部通过",
            )

            with self.assertRaises(build_full_script.DeliveryInputError) as context:
                build_full_script.validate_delivery_inputs(project, build_full_script.collect_episode_files(project))

            self.assertIn("T15 全剧复核", str(context.exception))

    def test_formal_export_blocks_pending_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), pending_rollback=True)

            with self.assertRaises(build_full_script.DeliveryInputError) as context:
                build_full_script.validate_delivery_inputs(project, build_full_script.collect_episode_files(project))

            self.assertIn("pendingRollback", str(context.exception))

    def test_production_enhanced_requires_enhanced_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), delivery_mode="production-enhanced", market="TikTok 欧美")

            with self.assertRaises(build_full_script.DeliveryInputError) as context:
                build_full_script.validate_delivery_inputs(project, build_full_script.collect_episode_files(project))

            message = str(context.exception)
            self.assertIn("production-enhanced", message)
            self.assertIn("制作理解稿", message)
            self.assertIn("海外制作版分场表", message)

    def test_douyin_production_enhanced_requires_clip_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), delivery_mode="production-enhanced", market="抖音国内")
            for name in ["制作理解稿.md", "制作交付参数表.md"]:
                write(project / "03-交付" / name, f"# {name[:-3]}\n\n正式内容。\n")

            with self.assertRaises(build_full_script.DeliveryInputError) as context:
                build_full_script.validate_delivery_inputs(project, build_full_script.collect_episode_files(project))

            self.assertIn("信息流投放素材切片说明", str(context.exception))

    def test_production_enhanced_passes_when_required_enhanced_files_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), delivery_mode="production-enhanced", market="TikTok 欧美")
            for name in ["制作理解稿.md", "制作交付参数表.md", "海外制作版分场表.md"]:
                write(project / "03-交付" / name, f"# {name[:-3]}\n\n正式内容。\n")

            build_full_script.validate_delivery_inputs(project, build_full_script.collect_episode_files(project))

    def test_planning_bible_includes_enhanced_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), delivery_mode="production-enhanced", market="抖音国内")
            for name in ["制作理解稿.md", "制作交付参数表.md", "信息流投放素材切片说明.md"]:
                write(project / "03-交付" / name, f"# {name[:-3]}\n\n{name} 正式内容。\n")

            output = build_full_script.build_planning_bible(project, project / "03-交付")

            self.assertIn("制作理解稿.md 正式内容", output)
            self.assertIn("制作交付参数表.md 正式内容", output)
            self.assertIn("信息流投放素材切片说明.md 正式内容", output)

    def test_planning_bible_demotes_embedded_headings(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp), delivery_mode="production-enhanced", market="抖音国内")
            write(project / "03-交付" / "制作理解稿.md", "# 制作理解稿\n\n## 一、项目概览\n\n正式内容。\n")
            write(project / "03-交付" / "制作交付参数表.md", "# 制作交付参数表\n\n## 一、版本来源\n\n正式内容。\n")
            write(project / "03-交付" / "信息流投放素材切片说明.md", "# 信息流投放素材切片说明\n\n## 一、版本信息\n\n正式内容。\n")

            output = build_full_script.build_planning_bible(project, project / "03-交付")

            self.assertIn("制作理解稿", output)
            self.assertIn("### 一、项目概览", output)
            self.assertNotIn("\n## 一、项目概览", output)

    def test_collect_episode_files_accepts_uppercase_ep_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo-project"
            write(project / "02-剧本" / "EP001.md", "# EP001\n")

            episode_files = build_full_script.collect_episode_files(project)

            self.assertEqual([path.name for path in episode_files], ["EP001.md"])

    def test_full_script_only_includes_scene_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp))
            episode_files = build_full_script.collect_episode_files(project)

            output = build_full_script.build_full_script(project, episode_files)

            self.assertIn("## 场次正文", output)
            self.assertIn("角色A做出选择", output)
            self.assertNotIn("## 本集创作简卡", output)
            self.assertNotIn("## 本集回填", output)

    def test_main_writes_standard_delivery_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = create_project(Path(tmp))

            result = build_full_script.main([str(project)])

            self.assertEqual(result, 0)
            self.assertTrue((project / "03-交付" / "完整剧本总稿.md").exists())
            self.assertTrue((project / "03-交付" / "剧本圣经.md").exists())
            self.assertTrue((project / "03-交付" / "交付清单.md").exists())


if __name__ == "__main__":
    unittest.main()
