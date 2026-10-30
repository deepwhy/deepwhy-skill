#!/usr/bin/env python3
"""Tests for the AskWhy content contract, validator, and standalone builder."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - optional local verification dependency
    jsonschema = None


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_page import safe_json_for_script  # noqa: E402
from validate_content import validate_content  # noqa: E402


EXAMPLE_PATH = SKILL_ROOT / "examples" / "bulb-glow.json"
SCHEMA_PATH = SKILL_ROOT / "assets" / "content.schema.json"
BUILDER_PATH = SCRIPTS / "build_page.py"
VALIDATOR_PATH = SCRIPTS / "validate_content.py"


def example_content() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def assert_valid(test: unittest.TestCase, content: dict) -> None:
    report = validate_content(content)
    test.assertEqual([], report.errors)


class SchemaTests(unittest.TestCase):
    def test_schema_is_valid_json_and_internal_refs_resolve(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            "https://json-schema.org/draft/2020-12/schema",
            schema["$schema"],
        )
        refs: list[str] = []

        def walk(value: object) -> None:
            if isinstance(value, dict):
                ref = value.get("$ref")
                if isinstance(ref, str):
                    refs.append(ref)
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(schema)
        self.assertTrue(refs)
        for ref in refs:
            self.assertTrue(ref.startswith("#/$defs/"), ref)
            self.assertIn(ref.removeprefix("#/$defs/"), schema["$defs"])

    def test_example_matches_core_contract(self) -> None:
        content = example_content()
        self.assertEqual("8.0", content["schemaVersion"])
        self.assertGreaterEqual(len(content["nodes"]), 4)
        self.assertLessEqual(len(content["nodes"]), 8)
        self.assertNotIn("followUps", content)
        self.assertEqual(4, len(content["center"]["analogy"]["mappings"]))
        self.assertTrue(
            all(2 <= len(node["analogy"]["mappings"]) <= 4 for node in content["nodes"])
        )
        self.assertIsInstance(content["center"]["analogy"]["visual"], dict)
        self.assertEqual("manim", content["center"]["analogy"]["visual"]["kind"])
        self.assertEqual("image", content["center"]["overviewVisual"]["kind"])
        self.assertTrue(
            all(node["analogy"].get("visual") for node in content["nodes"])
        )

    @unittest.skipIf(jsonschema is None, "jsonschema is not installed")
    def test_schema_validates_examples_with_selected_learning_level(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for path in sorted((SKILL_ROOT / "examples").glob("*.json")):
            with self.subTest(path=path.name):
                content = json.loads(path.read_text(encoding="utf-8"))
                errors = sorted(validator.iter_errors(content), key=str)
                self.assertEqual([], [error.message for error in errors])
                self.assertIn(content["meta"]["learningLevel"], {"primary", "middle", "high"})


class ValidationTests(unittest.TestCase):
    def test_example_is_valid(self) -> None:
        assert_valid(self, example_content())

    def test_all_example_contents_are_valid(self) -> None:
        for path in sorted((SKILL_ROOT / "examples").glob("*.json")):
            with self.subTest(path=path.name):
                content = json.loads(path.read_text(encoding="utf-8"))
                assert_valid(self, content)

    def test_cli_accepts_example(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), str(EXAMPLE_PATH)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Valid AskWhy 8.0 content", result.stdout)

    def test_requires_four_to_eight_nodes(self) -> None:
        content = example_content()
        content["nodes"] = content["nodes"][:3]
        report = validate_content(content)
        self.assertTrue(any("4–8 causal-chain steps" in error for error in report.errors))
        self.assertTrue(
            any("nextQuestion" in error for error in report.errors)
        )

    def test_rejects_duplicate_node_id(self) -> None:
        content = example_content()
        content["nodes"][1]["id"] = content["nodes"][0]["id"]
        report = validate_content(content)
        self.assertTrue(any("duplicate node ID" in error for error in report.errors))

    def test_rejects_reserved_root_node_id(self) -> None:
        content = example_content()
        content["nodes"][0]["id"] = "root"
        report = validate_content(content)
        self.assertTrue(any("reserved for the center" in error for error in report.errors))

    def test_rejects_top_level_sources(self) -> None:
        content = example_content()
        content["sources"] = []
        report = validate_content(content)
        self.assertTrue(any("unexpected key" in error for error in report.errors))

    def test_rejects_source_ids(self) -> None:
        content = example_content()
        content["nodes"][0]["sourceIds"] = ["source-does-not-exist"]
        report = validate_content(content)
        self.assertTrue(any("unexpected key" in error for error in report.errors))

    def test_rejects_broken_parent_chain(self) -> None:
        content = example_content()
        content["nodes"][2]["parentId"] = "root"
        report = validate_content(content)
        self.assertTrue(any("one ordered causal chain" in error for error in report.errors))

    def test_rejects_skipped_next_question(self) -> None:
        content = example_content()
        content["nodes"][0]["nextQuestion"] = "一个没有被下一节点回答的问题？"
        report = validate_content(content)
        self.assertTrue(
            any("next node's question" in error for error in report.errors)
        )

    def test_requires_complete_detail_on_every_node(self) -> None:
        content = example_content()
        del content["nodes"][3]["knowledge"]
        del content["nodes"][4]["facts"]
        report = validate_content(content)
        self.assertTrue(any("knowledge" in error for error in report.errors))
        self.assertTrue(any("facts" in error for error in report.errors))

    def test_later_nodes_have_complete_details(self) -> None:
        content = example_content()
        self.assertTrue(content["nodes"][3]["knowledge"])
        self.assertGreaterEqual(len(content["nodes"][3]["facts"]), 2)
        assert_valid(self, content)

    def test_requires_analogy_on_center_and_every_node(self) -> None:
        content = example_content()
        del content["center"]["analogy"]
        report = validate_content(content)
        self.assertTrue(
            any("$.center: missing required key 'analogy'" == error for error in report.errors)
        )

    def test_requires_static_overview_visual_on_center(self) -> None:
        content = example_content()
        del content["center"]["overviewVisual"]
        report = validate_content(content)
        self.assertTrue(
            any(
                "$.center: missing required key 'overviewVisual'" == error
                for error in report.errors
            )
        )

        content = example_content()
        content["center"]["overviewVisual"]["kind"] = "manim"
        report = validate_content(content)
        self.assertTrue(
            any("must be a static image visual" in error for error in report.errors)
        )

        content = example_content()
        del content["nodes"][3]["analogy"]
        report = validate_content(content)
        self.assertTrue(
            any(
                "$.nodes[3]: missing required key 'analogy'" == error
                for error in report.errors
            )
        )

    def test_requires_two_to_four_analogy_mappings(self) -> None:
        content = example_content()
        content["nodes"][0]["analogy"]["mappings"] = []
        report = validate_content(content)
        self.assertTrue(
            any("must contain 2–4 familiar-to-concept mappings" in error for error in report.errors)
        )

        content = example_content()
        mapping = content["nodes"][1]["analogy"]["mappings"][0]
        content["nodes"][1]["analogy"]["mappings"] = [mapping] * 5
        report = validate_content(content)
        self.assertTrue(
            any("must contain 2–4 familiar-to-concept mappings" in error for error in report.errors)
        )

    def test_requires_analogy_mapping_and_boundary_text(self) -> None:
        content = example_content()
        del content["nodes"][0]["analogy"]["mappings"][0]["familiar"]
        content["nodes"][1]["analogy"]["scene"] = ""
        content["center"]["analogy"]["limit"] = ""
        report = validate_content(content)
        self.assertTrue(
            any(
                "$.nodes[0].analogy.mappings[0]: missing required key 'familiar'" == error
                for error in report.errors
            )
        )
        self.assertTrue(
            any("$.nodes[1].analogy.scene: must be a non-empty string" == error for error in report.errors)
        )
        self.assertTrue(
            any("$.center.analogy.limit: must be a non-empty string" == error for error in report.errors)
        )

    def test_example_has_one_selected_learning_level(self) -> None:
        content = example_content()
        self.assertEqual("middle", content["meta"]["learningLevel"])
        self.assertNotIn("learningLevels", content["meta"])
        self.assertNotIn("levelVariants", content["center"])
        self.assertNotIn("levelVariants", content["nodes"][0])

    def test_rejects_legacy_multi_level_fields(self) -> None:
        content = example_content()
        content["meta"]["learningLevels"] = []
        report = validate_content(content)
        self.assertTrue(any("unexpected key" in error for error in report.errors))

    def test_rejects_invalid_learning_level(self) -> None:
        content = example_content()
        content["meta"]["learningLevel"] = "university"
        report = validate_content(content)
        self.assertTrue(any("primary, middle, or high" in error for error in report.errors))

    def test_rejects_search_result_as_video(self) -> None:
        content = example_content()
        content["nodes"][0]["videoLinks"] = [
            {
                "id": "video-search-result",
                "title": "不该出现的搜索页",
                "url": "https://www.youtube.com/results?search_query=gravity",
                "embedUrl": "https://www.youtube-nocookie.com/embed/verified-id",
                "platform": "youtube",
            }
        ]
        report = validate_content(content)
        self.assertTrue(any("not a search result" in error for error in report.errors))

    def test_rejects_placeholder_text(self) -> None:
        content = example_content()
        content["nodes"][0]["summary"] = "TODO: replace this text"
        report = validate_content(content)
        self.assertTrue(any("unfinished placeholder" in error for error in report.errors))

    def test_optional_experiment_and_video_links_can_be_omitted(self) -> None:
        content = example_content()
        del content["nodes"][0]["experiment"]
        del content["nodes"][0]["videoLinks"]
        assert_valid(self, content)

    def test_rejects_legacy_follow_ups(self) -> None:
        content = example_content()
        content["followUps"] = []
        report = validate_content(content)
        self.assertTrue(any("unexpected key" in error for error in report.errors))

    def test_rejects_unknown_keys(self) -> None:
        content = example_content()
        content["nodes"][0]["unexpected"] = True
        report = validate_content(content)
        self.assertTrue(any("unexpected key" in error for error in report.errors))

    def test_rejects_remote_visual_asset(self) -> None:
        content = example_content()
        content["nodes"][0]["visual"]["src"] = "https://example.com/diagram.svg"
        report = validate_content(content)
        self.assertTrue(
            any("must be a local path" in error for error in report.errors)
        )

    def test_rejects_remote_analogy_visual_asset(self) -> None:
        content = example_content()
        content["nodes"][0]["analogy"]["visual"]["src"] = (
            "https://example.com/analogy.svg"
        )
        report = validate_content(content)
        self.assertTrue(
            any("must be a local path" in error for error in report.errors)
        )

    def test_accepts_real_video(self) -> None:
        content = example_content()
        content["nodes"][0]["videoLinks"] = [
            {
                "id": "nasa-gravity-video",
                "title": "A verified external video title",
                "url": "https://www.youtube.com/watch?v=verified-id",
                "embedUrl": "https://www.youtube-nocookie.com/embed/verified-id",
                "platform": "youtube",
                "author": "NASA",
                "thumbnailUrl": "https://i.ytimg.com/vi/verified-id/hqdefault.jpg",
                "durationSeconds": 240,
                "publishedAt": "2026-01-02",
                "queryDate": "2026-10-26",
                "relevanceScore": 91.5,
                "selectionRationale": "标题与节点问题匹配，且提供实验演示。",
            }
        ]
        assert_valid(self, content)

    def test_rejects_invalid_video_score(self) -> None:
        content = example_content()
        content["nodes"][0]["videoLinks"] = [
            {
                "id": "video-score",
                "title": "Video",
                "url": "https://www.bilibili.com/video/BV1test",
                "embedUrl": "https://player.bilibili.com/player.html?bvid=BV1test&page=1",
                "platform": "bilibili",
                "relevanceScore": 101,
            }
        ]
        report = validate_content(content)
        self.assertTrue(
            any("relevanceScore" in error for error in report.errors)
        )

    def test_rejects_mismatched_embed_video(self) -> None:
        content = example_content()
        content["nodes"][0]["videoLinks"] = [
            {
                "id": "video-mismatch",
                "title": "Video",
                "url": "https://www.bilibili.com/video/BV1good",
                "embedUrl": "https://player.bilibili.com/player.html?bvid=BV1other",
                "platform": "bilibili",
            }
        ]
        report = validate_content(content)
        self.assertTrue(any("BVID must match" in error for error in report.errors))


class BuilderTests(unittest.TestCase):
    def test_safe_json_prevents_script_breakout(self) -> None:
        serialized = safe_json_for_script({"text": "</script><script>bad()</script>"})
        self.assertNotIn("</script>", serialized.lower())
        self.assertIn("<\\/script>", serialized)

    def test_builder_creates_one_standalone_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "apple.html"
            data_out = Path(temp_dir) / "apple.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILDER_PATH),
                    str(EXAMPLE_PATH),
                    "--output",
                    str(output),
                    "--data-out",
                    str(data_out),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertEqual(1, len(list(Path(temp_dir).glob("*.html"))))
            self.assertIn("<title>电灯为什么会发光 · AskWhy</title>", html)
            self.assertIn('id="askwhy-data"', html)
            self.assertNotIn("__ASKWHY_", html)
            self.assertNotRegex(html, r"<script[^>]+\bsrc=")
            self.assertNotRegex(html, r"<link[^>]+\brel=[\"']stylesheet")
            self.assertNotIn("fonts.googleapis.com", html)
            self.assertIn('data-layout="chain"', html)
            self.assertIn("data:image/svg+xml;base64,", html)
            self.assertIn("data:video/webm;base64,", html)
            self.assertIn("data:image/webp;base64,", html)
            self.assertIn("Embedded visuals: 16", result.stdout)
            self.assertNotIn("OpenStax", html)
            self.assertNotIn("sourceIds", html)
            self.assertNotIn(">SRC<", html)
            self.assertTrue(data_out.is_file())

    def test_builder_aborts_invalid_content(self) -> None:
        content = example_content()
        content["nodes"] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "invalid.json"
            output = Path(temp_dir) / "invalid.html"
            input_path.write_text(json.dumps(content), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILDER_PATH),
                    str(input_path),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertFalse(output.exists())
            self.assertIn("Build aborted", result.stderr)

    def test_example_data_is_embedded_without_mutating_source(self) -> None:
        original = example_content()
        content = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "apple.html"
            subprocess.run(
                [
                    sys.executable,
                    str(BUILDER_PATH),
                    str(EXAMPLE_PATH),
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            html = output.read_text(encoding="utf-8")
            match = re.search(
                r'<script type="application/json" id="askwhy-data">(.*?)</script>',
                html,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            embedded = json.loads(match.group(1))
            self.assertEqual(7, len(embedded["nodes"]))
            self.assertEqual(original, content)


if __name__ == "__main__":
    unittest.main()
