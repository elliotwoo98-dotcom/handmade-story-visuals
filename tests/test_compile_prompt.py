from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import compile_prompt  # noqa: E402


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = compile_prompt.load_catalog()

    def test_catalog_has_ten_unique_original_styles(self) -> None:
        styles = self.catalog["styles"]
        self.assertEqual(len(styles), 10)
        self.assertEqual(len({style["id"] for style in styles}), 10)
        self.assertEqual(len({style["slug"] for style in styles}), 10)

    def test_resolves_id_slug_name_and_alias(self) -> None:
        expected = "black-gold-parable"
        for selector in ("S07", expected, "黑金寓言剪影", "金线剪影"):
            with self.subTest(selector=selector):
                style = compile_prompt.resolve_style(self.catalog, selector)
                self.assertEqual(style["slug"], expected)

    def test_unknown_style_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown style"):
            compile_prompt.resolve_style(self.catalog, "not-a-real-style")


class CompilationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = compile_prompt.load_catalog()

    def test_auto_recommendation_is_deterministic_and_explainable(self) -> None:
        package = compile_prompt.compile_package(
            self.catalog,
            subject="星空下，一位行者听完寓言后明白了选择与因果",
            intent="表达传统智慧和命运转折",
        )
        selected = package["selected_style"]
        self.assertEqual(selected["slug"], "black-gold-parable")
        self.assertEqual(selected["selection_mode"], "automatic")
        self.assertIn("寓言", selected["matched_keywords"])
        self.assertIn("因果", selected["matched_keywords"])

    def test_concrete_subject_signal_outweighs_generic_intent_words(self) -> None:
        package = compile_prompt.compile_package(
            self.catalog,
            subject="雨夜的公交站，女孩把唯一的伞递给淋雨老人",
            intent="突出微小善意带来的温暖",
        )
        selected = package["selected_style"]
        self.assertEqual(selected["slug"], "street-corner-gouache")
        self.assertIn("公交站", selected["matched_keywords"])
        self.assertIn("雨夜使用街灯、站灯与湿地反光", package["prompt"])
        self.assertNotIn("生活化的晨光或傍晚斜光", package["prompt"])

    def test_no_keyword_uses_declared_fallback(self) -> None:
        package = compile_prompt.compile_package(
            self.catalog,
            subject="甲物体位于乙物体旁边",
        )
        self.assertEqual(package["selected_style"]["slug"], "postcard-storybook")
        self.assertEqual(package["selected_style"]["selection_mode"], "fallback")

    def test_exact_visible_text_is_preserved_in_input_and_prompt(self) -> None:
        locked = ["别急，慢慢来。", "第 2 站：春天"]
        package = compile_prompt.compile_package(
            self.catalog,
            subject="女孩在站台等车",
            style_query="street-corner-gouache",
            visible_text=locked,
        )
        self.assertEqual(package["inputs"]["visible_text"], locked)
        for value in locked:
            self.assertIn(json.dumps(value, ensure_ascii=False), package["prompt"])
        self.assertIn("不得翻译、润色、缩写", package["prompt"])
        self.assertIn("错字", package["negative_prompt"])

    def test_text_free_prompt_blocks_all_visible_text(self) -> None:
        package = compile_prompt.compile_package(
            self.catalog,
            subject="孩子在窗边给小树浇水",
            style_query="windowlight-wax",
        )
        self.assertEqual(package["inputs"]["visible_text"], [])
        self.assertIn("不出现任何文字、字母、数字", package["prompt"])
        self.assertIn("任何可见文字", package["negative_prompt"])

    def test_continuity_locks_are_emitted_without_rewriting(self) -> None:
        character = "阿禾：左耳有一颗小痣、绿色围巾、旧木手杖"
        context = "固定雨后青石巷，青绿与朱红平衡，镜头保持平视"
        package = compile_prompt.compile_package(
            self.catalog,
            subject="阿禾推开旧书店的门",
            style_query="S02",
            aspect="3:4",
            character_locks=[character],
            series_context=context,
        )
        self.assertEqual(package["inputs"]["character_locks"], [character])
        self.assertEqual(package["inputs"]["series_context"], context)
        self.assertIn(json.dumps(character, ensure_ascii=False), package["prompt"])
        self.assertIn(context, package["prompt"])
        self.assertIn("3:4", package["prompt"])

    def test_output_matches_documented_top_level_contract(self) -> None:
        package = compile_prompt.compile_package(
            self.catalog,
            subject="一张桌上放着一封未拆的信",
            style_query="graphite-moment",
        )
        self.assertEqual(
            set(package),
            {
                "schema_version",
                "selected_style",
                "inputs",
                "prompt",
                "negative_prompt",
                "quality_checks",
            },
        )
        self.assertEqual(package["schema_version"], "1.0")
        self.assertGreaterEqual(len(package["quality_checks"]), 3)


class CliTests(unittest.TestCase):
    def test_json_cli_output_is_parseable(self) -> None:
        command = [
            sys.executable,
            str(SKILL_ROOT / "scripts" / "compile_prompt.py"),
            "--subject",
            "森林里的小鹿找到回家的路",
            "--style",
            "auto",
            "--format",
            "json",
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["selected_style"]["slug"], "layered-paper-theatre")

    def test_list_styles_cli_returns_all_styles(self) -> None:
        command = [
            sys.executable,
            str(SKILL_ROOT / "scripts" / "compile_prompt.py"),
            "--list-styles",
            "--format",
            "json",
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 10)


if __name__ == "__main__":
    unittest.main()
