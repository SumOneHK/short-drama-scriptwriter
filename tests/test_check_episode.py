import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_episode.py"
SPEC = importlib.util.spec_from_file_location("check_episode", SCRIPT_PATH)
check_episode = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = check_episode
SPEC.loader.exec_module(check_episode)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CheckEpisodeTests(unittest.TestCase):
    def test_english_dialogue_with_ascii_colon_counts_as_body_line(self):
        scene_body = [
            "人物：English Name（中文身份） / English Name B",
            "△ English Name grabs the phone.",
            "English Name: You don't get to do that.（别越界。）",
            "Screen Text: ACCESS DENIED",
            "SFX：Door slam.",
        ]

        self.assertEqual(check_episode.count_body_lines(scene_body), 4)

    def test_system_screen_text_ascii_colon_counts_words_as_diegetic(self):
        scene_body = ["Screen Text: ACCESS DENIED"]

        items = check_episode.extract_screen_text_items(scene_body)

        self.assertEqual(items[0].category, "diegetic")
        self.assertEqual(items[0].char_count, 2)

    def test_explicit_overlay_text_counts_against_overlay_quota(self):
        scene_body = ["屏幕字（叠加）：三天后"]

        items = check_episode.extract_screen_text_items(scene_body)

        self.assertEqual(items[0].category, "overlay")
        self.assertEqual(check_episode.extract_screen_text_chars(scene_body), [("三天后", 3)])

    def test_tagged_group_chat_is_diegetic_text_not_overlay_quota(self):
        scene_body = ["屏幕字（群聊）：梁一诺：我截了"]

        items = check_episode.extract_screen_text_items(scene_body)

        self.assertEqual(items[0].category, "diegetic")
        self.assertEqual(check_episode.extract_screen_text_chars(scene_body), [])

    def test_obvious_document_title_is_diegetic_text(self):
        scene_body = ["屏幕字：维修基金支出明细"]

        items = check_episode.extract_screen_text_items(scene_body)

        self.assertEqual(items[0].category, "diegetic")

    def test_tagged_screen_text_counts_as_body_line(self):
        scene_body = ["人物：林栀 / 陈崇", "屏幕字（文件）：维修基金支出明细"]

        self.assertEqual(check_episode.count_body_lines(scene_body), 1)

    def test_medical_and_school_text_are_diegetic_across_genres(self):
        scene_body = ["屏幕字（病历）：诊断记录", "屏幕字：高三二班考勤记录"]

        items = check_episode.extract_screen_text_items(scene_body)

        self.assertEqual([item.category for item in items], ["diegetic", "diegetic"])

    def test_system_prompt_tag_is_diegetic_not_overlay(self):
        scene_body = ["屏幕字（系统提示）：余额不足"]

        items = check_episode.extract_screen_text_items(scene_body)

        self.assertEqual(items[0].category, "diegetic")

    def test_location_label_is_separate_from_diegetic_budget(self):
        scene_body = ["屏幕字（地名）：住院部三楼"]

        items = check_episode.extract_screen_text_items(scene_body)

        self.assertEqual(items[0].category, "label")

    def test_long_diegetic_text_warns_but_does_not_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            episode_path = Path(tmp) / "第003集.md"
            write(
                episode_path,
                "\n".join(
                    [
                        "## 场次正文",
                        "### 3-1 日内 物业办公室",
                        "人物：林栀 / 陈崇",
                        "△ 林栀把文件推到桌边。",
                        "屏幕字（文件）：维修基金支出明细电梯大修费用合计十八万六千四百元由三号楼业主共同承担",
                        "林栀：这张给我复印。",
                        "## 本集回填",
                    ]
                ),
            )

            report = check_episode.check_episode(episode_path, regulation_words=[], target_seconds=75)

        self.assertTrue(report.passed)
        self.assertEqual(report.screen_text_total_chars, 0)
        self.assertGreater(report.diegetic_text_total_chars, 0)
        self.assertIn("diegetic_text_per_line", [v.rule for v in report.violations])

    def test_collect_episode_files_accepts_uppercase_ep_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "EP001.md", "# EP001\n")

            episode_files = check_episode.collect_episode_files(root)

            self.assertEqual([path.name for path in episode_files], ["EP001.md"])


if __name__ == "__main__":
    unittest.main()
