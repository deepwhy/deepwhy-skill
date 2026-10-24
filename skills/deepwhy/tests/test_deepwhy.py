#!/usr/bin/env python3
"""Tests for the DeepWhy knowledge-chain skill, contract, and builder."""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_content import validate_content  # noqa: E402
import manim_runtime  # noqa: E402
import manim_render  # noqa: E402

def node(
    node_id: str,
    node_type: str,
    index: int,
    *,
    answer: str = "这是一个足够完整、但仍然很短的一句核心答案。",
    diagram: dict | None = None,
    lab: dict | None = None,
) -> dict:
    return {
        "id": node_id,
        "parentId": None,
        "type": node_type,
        "concept": f"概念{index}",
        "question": f"为什么第 {index} 层会这样？",
        "answer": answer,
        "analogy": "把新概念想成一个熟悉的日常场景。",
        "guide": {
            "bridge": "先接着上一层的现象。",
            "plainLanguage": "用一个简单例子说明这一层。",
            "steps": ["先观察现象。", "再解释原因。"],
            "check": {
                "prompt": "你觉得下一步会发生什么？",
                "answer": "它会继续沿同一方向变化。",
            },
        },
        "status": "complete",
        "sourceIds": ["source-1"],
        "detail": {
            "deepDive": "",
            "whyItMatters": "",
            "experimentOrProof": "",
            "frontier": "",
        },
        "diagram": diagram,
        "videoIds": [f"video-{index}-{video_index}" for video_index in range(1, 6)],
        "lab": lab,
        "branches": [],
    }


def tiny_svg() -> dict:
    return {
        "mode": "svg",
        "kind": "illustration",
        "svg": (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
            '<rect width="20" height="20" fill="#123456"/></svg>'
        ),
        "src": None,
        "alt": "测试示意图",
        "caption": "用于验证图表结构。",
        "formula": None,
        "sourceIds": ["source-1"],
        "interaction": {
            "kind": "prediction",
            "prompt": "先猜一猜：改变条件后会发生什么？",
            "options": [
                {
                    "label": "结果不变",
                    "feedback": "再观察一下当前条件。",
                },
                {
                    "label": "结果随条件改变",
                    "feedback": "正确，这正是这一层要观察的因果变化。",
                },
            ],
            "correctIndex": 1,
        },
    }


def tiny_lab(kind: str) -> dict:
    return {
        "kind": kind,
        "title": "测试交互实验室",
        "goal": "改变一个条件，观察结果怎样变化。",
        "html": (
            "<!doctype html><html><head>"
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            "</head><body><main id=\"lab-root\">"
            "<div id=\"lab-state\">初始状态</div>"
            "<div id=\"lab-feedback\">观察变化</div>"
            "<button id=\"lab-reset\" type=\"button\">重置</button>"
            "<script>window.parent.postMessage("
            "{source:'deepwhy-lab',type:'state',complete:false,"
            "summary:'初始状态',state:{}}, '*');</script>"
            "</main></body></html>"
        ),
        "height": 360,
        "fallbackText": "如果实验无法运行，直接阅读这句等价说明。",
        "completionText": "条件改变后，结果也会随之变化。",
        "reflectionPrompt": "用自己的比喻复述刚才观察到的关系。",
    }


def tiny_video(node_index: int, index: int) -> dict:
    return {
        "id": f"video-{node_index}-{index}",
        "title": f"测试外站视频 {index}",
        "author": "测试作者",
        "platform": "bilibili",
        "url": "https://www.bilibili.com/video/BV12N411a784",
        "embedUrl": (
            "https://player.bilibili.com/player.html?"
            "bvid=BV12N411a784&page=1&autoplay=0"
        ),
        "thumbnailUrl": (
            "https://i0.hdslb.com/bfs/archive/test-thumbnail.jpg"
        ),
        "durationSeconds": 120 + index,
        "publishedAt": "2026-01-01",
        "queryDate": "2026-10-24",
        "metricsStatus": "captured",
        "metrics": {"views": index, "likes": index, "comments": index},
        "selectionRationale": "用于验证每个知识节点关联五条外站视频。",
        "sourceIds": ["source-1"],
    }


def make_content() -> dict:
    return {
        "schemaVersion": "2.0",
        "meta": {
            "topic": "测试主题",
            "question": "测试问题是什么？",
            "slug": "test-topic",
            "hook": "从一个人人熟悉的观察开始。",
            "asOf": "2026-10-23",
            "language": "zh-CN",
            "audience": {
                "description": "测试学习者",
                "priorKnowledge": "知道基本术语",
                "explanationLevel": "child",
                "assumptions": [],
            },
            "premiseCheck": {
                "status": "confirmed",
                "original": "测试问题是什么？",
                "note": "问题前提成立。",
            },
            "scope": {"included": ["核心机制"], "excluded": ["无关内容"]},
            "evidenceGaps": [],
        },
        "presentation": {
            "preset": "deepwhy",
            "source": "auto",
            "rationale": "测试技术主题。",
            "archetype": "phenomenon_exploration",
            "centralInsight": "从一个现象进入机制。",
            "focalRepresentation": "用一张机制图建立主视觉。",
            "hierarchy": ["开场主视觉", "主链节点", "节点详情"],
            "sectionRhythm": ["开场", "主链", "验证"],
        },
        "sources": [
            {
                "id": "source-1",
                "title": "官方说明",
                "publisher": "测试机构",
                "url": "https://example.com/source",
                "kind": "official",
                "publishedAt": "2026-01-01",
                "accessedAt": "2026-10-23",
                "notes": "用于测试。",
            }
        ],
        "chain": {
            "title": "测试知识链",
            "openingScenario": "先观察一个熟悉现象。",
            "openingQuestion": "这个现象为什么出现？",
            "openingVisual": tiny_svg(),
            "nodes": [
                node("n1", "phenomenon", 1),
                node("n2", "mechanism", 2, lab=tiny_lab("simulation")),
                node(
                    "n3",
                    "principle",
                    3,
                    diagram=tiny_svg(),
                    lab=tiny_lab("diagram"),
                ),
                node("n4", "boundary", 4),
            ],
            "takeaway": "测试链用一个简短结论收束。",
        },
        "videos": {
            "platformsSearched": ["youtube", "bilibili"],
            "items": [
                tiny_video(node_index, video_index)
                for node_index in range(1, 5)
                for video_index in range(1, 6)
            ],
            "gap": "测试环境没有可核验视频。",
        },
        "background": {
            "summary": "测试背景摘要。",
            "people": [],
            "institutions": [],
            "applications": [],
            "timeline": [],
            "frontier": [],
            "gap": None,
        },
        "assessment": {
            "instructions": "每个节点完成 5 道单选题。",
            "items": [
                {
                    "id": f"q-{node_id}-{index}",
                    "nodeId": node_id,
                    "type": "concept",
                    "prompt": f"第 {node_id} 节点的第 {index} 道单选题？",
                    "format": "choice",
                    "options": ["甲", "乙", "丙"],
                    "correctIndex": 0,
                    "modelAnswer": "甲。",
                    "rubric": ["选择与当前节点一致的答案"],
                    "explanation": "甲与当前节点的因果链一致。",
                    "sourceIds": ["source-1"],
                }
                for node_id in ("n1", "n2", "n3", "n4")
                for index in range(1, 6)
            ],
        },
        "nextQuestions": [
            {
                "question": "下一步可以追问什么？",
                "why": "它延伸了当前机制。",
                "sourceIds": ["source-1"],
            }
        ],
    }


class DeepWhyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.content = make_content()

    def assert_valid(self, content: dict) -> None:
        report = validate_content(content)
        self.assertTrue(report.ok, "\n".join(report.errors))

    def test_skill_frontmatter_and_references(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: deepwhy\n"))
        self.assertLess(len(text.splitlines()), 500)
        for relative in re.findall(r"\]\((references/[^)]+|assets/[^)]+)\)", text):
            self.assertTrue((SKILL_ROOT / relative).exists(), relative)

    def test_example_is_knowledge_chain_not_module_article(self) -> None:
        example = json.loads(
            (SKILL_ROOT / "examples" / "apple-gravity.json").read_text(
                encoding="utf-8"
            )
        )
        self.assert_valid(example)
        self.assertNotIn("modules", example)
        self.assertGreaterEqual(len(example["chain"]["nodes"]), 4)
        self.assertLessEqual(len(example["chain"]["nodes"]), 6)
        self.assertTrue(any(node.get("diagram") for node in example["chain"]["nodes"]))
        self.assertTrue(any(node.get("manim") for node in example["chain"]["nodes"]))
        self.assertTrue(
            all(item["format"] == "choice" for item in example["assessment"]["items"])
        )
        self.assertEqual(len(example["assessment"]["items"]), 30)
        for main_node in example["chain"]["nodes"]:
            self.assertEqual(
                sum(
                    item["nodeId"] == main_node["id"]
                    for item in example["assessment"]["items"]
                ),
                5,
            )
        self.assertEqual(len(example["videos"]["items"]), 30)
        self.assertEqual(
            len({video["id"] for video in example["videos"]["items"]}),
            30,
        )
        self.assertTrue(
            all(len(main_node["videoIds"]) == 5 for main_node in example["chain"]["nodes"])
        )
        self.assertTrue(
            all(video["embedUrl"].startswith("https://player.bilibili.com/")
                for video in example["videos"]["items"])
        )

        html_path = SKILL_ROOT / "examples" / "apple-gravity.html"
        html = html_path.read_text(encoding="utf-8")
        self.assertIn('id="chain-start"', html)
        self.assertIn('id="background-dialog"', html)
        self.assertIn('data-style="deepwhy"', html)
        self.assertNotIn('id="chapter-links"', html)
        match = re.search(
            r'<script id="deepwhy-data" type="application/json">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        embedded = json.loads(match.group(1))
        self.assertEqual(embedded["schemaVersion"], "2.0")
        self.assertEqual(embedded["meta"]["topic"], example["meta"]["topic"])

    def test_mathematical_chain(self) -> None:
        content = copy.deepcopy(self.content)
        content["meta"].update(
            {
                "topic": "无穷级数的有限和",
                "question": "为什么无限多项相加有时会得到有限值？",
                "slug": "infinite-series",
            }
        )
        content["chain"]["nodes"][0]["answer"] = "无限和是否有限，要通过部分和序列的极限来判断。"
        content["chain"]["nodes"][1]["type"] = "mechanism"
        content["chain"]["nodes"][2]["type"] = "principle"
        self.assert_valid(content)

    def test_apple_visual_validation_example(self) -> None:
        example = json.loads(
            (SKILL_ROOT / "assets" / "apple-gravity.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assert_valid(example)
        self.assertEqual(example["presentation"]["archetype"], "phenomenon_exploration")
        self.assertEqual(example["meta"]["audience"]["explanationLevel"], "child")
        self.assertEqual(len(example["videos"]["items"]), 30)
        self.assertTrue(example["chain"]["openingVisual"]["svg"])
        self.assertIn(
            "<animateTransform",
            example["chain"]["openingVisual"]["svg"],
            "the motion opening example should demonstrate inline SVG animation",
        )
        self.assertTrue(
            all(
                node["guide"]["bridge"]
                and node["guide"]["plainLanguage"]
                and len(node["guide"]["steps"]) >= 2
                and node["guide"]["check"]["prompt"]
                for node in example["chain"]["nodes"]
            )
        )
        kinds = {
            node["diagram"]["kind"]
            for node in example["chain"]["nodes"]
            if node.get("diagram")
        }
        self.assertTrue({"force", "equation", "comparison", "evidence"} <= kinds)
        html = (SKILL_ROOT / "examples" / "apple-gravity.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('data-style="deepwhy"', html)
        self.assertIn("苹果为什么会落地？", html)

    def test_computer_science_frontier_dossier(self) -> None:
        content = copy.deepcopy(self.content)
        content["background"]["frontier"] = [
            {
                "title": "一项特定基准研究",
                "publishedAt": "2026-01-02",
                "status": "research",
                "route": "检索增强",
                "finding": "论文在受限基准上报告了变化。",
                "unresolved": "部署效果仍需验证。",
                "sourceIds": ["source-1"],
            }
        ]
        self.assert_valid(content)

    def test_history_timeline_dossier(self) -> None:
        content = copy.deepcopy(self.content)
        content["background"]["timeline"] = [
            {
                "date": "1912",
                "sortDate": "1912-01-01",
                "eventType": "proposal",
                "title": "理论被提出",
                "description": "一个竞争性解释进入争论。",
                "impact": "后续证据开始重新组织问题。",
                "sourceIds": ["source-1"],
            }
        ]
        self.assert_valid(content)

    def test_insufficient_frontier_remains_empty(self) -> None:
        content = copy.deepcopy(self.content)
        content["background"]["frontier"] = []
        content["background"]["gap"] = "没有找到可核验的最新资料。"
        self.assert_valid(content)

    def test_missing_video_metrics(self) -> None:
        content = copy.deepcopy(self.content)
        content["videos"]["items"][0].update(
            {
                "publishedAt": None,
                "metricsStatus": "unavailable",
                "metrics": {"views": None, "likes": None, "comments": None},
            }
        )
        content["videos"]["gap"] = "B 站未找到可核验视频。"
        self.assert_valid(content)

    def test_each_node_requires_exactly_five_external_videos(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][0]["videoIds"] = content["chain"]["nodes"][0][
            "videoIds"
        ][:4]
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("exactly 5 external videos" in error for error in report.errors))

    def test_external_video_requires_thumbnail_url(self) -> None:
        content = copy.deepcopy(self.content)
        del content["videos"]["items"][0]["thumbnailUrl"]
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("thumbnailUrl" in error for error in report.errors))

    def test_nodes_must_use_different_videos(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][1]["videoIds"][0] = content["chain"]["nodes"][0][
            "videoIds"
        ][0]
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("use different videos" in error for error in report.errors))

    def test_wrong_premise(self) -> None:
        content = copy.deepcopy(self.content)
        content["meta"]["premiseCheck"] = {
            "status": "corrected",
            "original": "为什么 GPS 卫星追踪手机？",
            "note": "GPS 卫星广播单向信号，并不接收手机位置。",
        }
        self.assert_valid(content)

    def test_design_brief_and_opening_visual_are_required(self) -> None:
        content = copy.deepcopy(self.content)
        del content["presentation"]["centralInsight"]
        del content["chain"]["openingVisual"]
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("centralInsight" in error for error in report.errors))
        self.assertTrue(any("openingVisual" in error for error in report.errors))

    def test_guided_progression_is_required(self) -> None:
        content = copy.deepcopy(self.content)
        del content["chain"]["nodes"][1]["guide"]
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any(".guide" in error for error in report.errors))

    def test_mechanism_requires_teaching_metaphor(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][1]["analogy"] = ""
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("teaching metaphor" in error for error in report.errors)
        )

    def test_mechanism_requires_hands_on_lab(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][1]["lab"] = None
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("hands-on lab" in error for error in report.errors))

    def test_adjacent_labs_need_different_modalities(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][2]["lab"] = tiny_lab("simulation")
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("adjacent lab nodes" in error for error in report.errors)
        )

    def test_all_six_lab_kinds_validate(self) -> None:
        kinds = [
            "simulation",
            "diagram",
            "code",
            "game",
            "spatial3d",
            "procedural",
        ]
        for index, kind in enumerate(kinds):
            with self.subTest(kind=kind):
                content = copy.deepcopy(self.content)
                content["chain"]["nodes"][1]["lab"] = tiny_lab(kind)
                content["chain"]["nodes"][2]["lab"] = tiny_lab(
                    kinds[(index + 1) % len(kinds)]
                )
                self.assert_valid(content)

    def test_lab_requires_sandbox_contract_markers(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][1]["lab"]["html"] = (
            "<!doctype html><html><head></head><body>plain</body></html>"
        )
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("required lab contract marker" in error for error in report.errors)
        )

    def test_manim_contract_and_transcript(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][0]["manim"] = {
            "sceneSource": "media/scene.py",
            "sceneClass": "AppleScene",
            "videoSrc": "media/apple.webm",
            "posterSrc": "media/apple.webp",
            "durationSeconds": 8.4,
            "alt": "苹果落到地面的动画",
            "caption": "苹果朝地球移动。",
            "transcript": [
                {"start": 0, "end": 3, "text": "苹果离开树枝。"},
                {"start": 3, "end": 8, "text": "苹果朝地球加速。"},
            ],
            "fallbackSvg": (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
                '<circle cx="10" cy="10" r="4"/></svg>'
            ),
        }
        self.assert_valid(content)

        content["chain"]["nodes"][0]["manim"]["transcript"][1]["start"] = 2
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("ordered" in error for error in report.errors))

    def test_manim_rejects_remote_media_and_missing_fallback(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][0]["manim"] = {
            "sceneSource": "media/scene.py",
            "sceneClass": "AppleScene",
            "videoSrc": "https://example.com/apple.webm",
            "posterSrc": "media/apple.webp",
            "durationSeconds": 8,
            "alt": "苹果下落",
            "caption": "苹果下落。",
            "transcript": [{"start": 0, "end": 8, "text": "苹果下落。"}],
            "fallbackSvg": "not an svg",
        }
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("local path" in error for error in report.errors))
        self.assertTrue(any("inline SVG" in error for error in report.errors))

    def test_each_node_requires_exactly_five_single_choice_questions(self) -> None:
        content = copy.deepcopy(self.content)
        content["assessment"]["items"] = [
            item
            for item in content["assessment"]["items"]
            if item["id"] != "q-n2-5"
        ]
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("exactly 5" in error for error in report.errors))

        content = copy.deepcopy(self.content)
        content["assessment"]["items"][0]["format"] = "text"
        content["assessment"]["items"][0]["correctIndex"] = None
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("single-choice" in error for error in report.errors))

    def test_builder_inlines_manim_media(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][0]["manim"] = {
            "sceneSource": "media/scene.py",
            "sceneClass": "AppleScene",
            "videoSrc": "media/apple.webm",
            "posterSrc": "media/apple.webp",
            "durationSeconds": 1.1,
            "alt": "苹果下落",
            "caption": "苹果朝地球移动。",
            "transcript": [{"start": 0, "end": 1.1, "text": "苹果下落。"}],
            "fallbackSvg": (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
                '<circle cx="10" cy="10" r="4"/></svg>'
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            media = root / "media"
            media.mkdir()
            (media / "scene.py").write_text("from manim import Scene\n", encoding="utf-8")
            (media / "apple.webm").write_bytes(b"webm-test-bytes")
            (media / "apple.webp").write_bytes(b"webp-test-bytes")
            source = root / "content.json"
            output = root / "page.html"
            source.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "build_page.py"),
                    str(source),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertIn("data:video/webm;base64,", html)
            self.assertIn("data:image/webp;base64,", html)
            self.assertNotIn("media/apple.webm", html)
            self.assertIn("Inlined Manim scenes: 1", result.stdout)

    def test_chain_requires_a_learner_interaction(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["openingVisual"]["interaction"] = None
        content["chain"]["nodes"][2]["diagram"]["interaction"] = None
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(
            any("learner interaction" in error for error in report.errors)
        )

    def test_long_main_answer_is_rejected(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][1]["answer"] = "这是一个故意写得非常长的主链答案，" * 4
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("text wall" in error for error in report.errors))

    def test_descending_node_depth_is_rejected(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][1]["type"] = "theory"
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("move backward" in error for error in report.errors))

    def test_dangling_source_is_rejected(self) -> None:
        content = copy.deepcopy(self.content)
        content["chain"]["nodes"][0]["sourceIds"] = ["missing-source"]
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("dangling source" in error for error in report.errors))

    def test_video_platform_gap_is_required(self) -> None:
        content = copy.deepcopy(self.content)
        content["videos"]["gap"] = None
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("video platforms" in error for error in report.errors))

    def test_invalid_embed_url_is_rejected(self) -> None:
        content = copy.deepcopy(self.content)
        content["videos"]["items"][0]["embedUrl"] = (
            "https://example.com/player.html?bvid=BV12N411a784"
        )
        content["videos"]["gap"] = "YouTube 无结果。"
        report = validate_content(content)
        self.assertFalse(report.ok)
        self.assertTrue(any("player.bilibili.com" in error for error in report.errors))

    def test_build_env_style_and_special_topic(self) -> None:
        content = copy.deepcopy(self.content)
        topic = 'Why does 0.999… = 1 & "why" matter?'
        content["meta"]["topic"] = topic
        content["meta"]["question"] = topic
        content["meta"]["slug"] = "url-encoding"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "content.json"
            output = root / "page.html"
            data_out = root / "resolved.json"
            source.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "build_page.py"),
                    str(source),
                    "--output",
                    str(output),
                    "--data-out",
                    str(data_out),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "DEEPWHY_PAGE_STYLE": "chronicle",
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            resolved = json.loads(data_out.read_text(encoding="utf-8"))
            self.assertIn('data-style="chronicle"', html)
            self.assertNotIn("deepwhy.example", html)
            self.assertNotIn('id="deepwhy-completion"', html)
            self.assertNotIn('id="deepwhy-background"', html)
            self.assertEqual(resolved["presentation"]["preset"], "chronicle")
            self.assertEqual(resolved["presentation"]["source"], "user")
            embedded_match = re.search(
                r'<script id="deepwhy-data" type="application/json">(.*?)</script>',
                html,
                re.DOTALL,
            )
            self.assertIsNotNone(embedded_match)
            embedded = json.loads(embedded_match.group(1))
            self.assertEqual(embedded["meta"]["topic"], topic)

    def test_invalid_style_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "content.json"
            source.write_text(json.dumps(self.content, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "build_page.py"),
                    str(source),
                    "--style",
                    "not-a-style",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid choice", result.stderr)

    def test_all_style_presets_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "content.json"
            source.write_text(json.dumps(self.content, ensure_ascii=False), encoding="utf-8")
            for style in ("deepwhy", "atlas", "chronicle", "fieldnotes"):
                output = root / f"{style}.html"
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPTS / "build_page.py"),
                        str(source),
                        "--style",
                        style,
                        "--output",
                        str(output),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(
                    f'data-style="{style}"',
                    output.read_text(encoding="utf-8"),
                )

    def test_schema_is_v2_json(self) -> None:
        schema = json.loads(
            (SKILL_ROOT / "assets" / "content.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(schema["properties"]["schemaVersion"]["const"], "2.0")
        self.assertIn("chain", schema["required"])
        self.assertNotIn("modules", schema["properties"])
        self.assertNotIn("deepwhy", schema["required"])
        self.assertIn("manim", schema["$defs"]["chainNode"]["properties"])


class ManimRuntimeTests(unittest.TestCase):
    def test_install_without_confirmation_is_refused(self) -> None:
        with mock.patch.object(manim_runtime.subprocess, "run") as run:
            with self.assertRaises(PermissionError):
                manim_runtime.install(False)
            run.assert_not_called()

    def test_macos_install_plan_lists_full_dependencies(self) -> None:
        with mock.patch.object(
            manim_runtime.shutil,
            "which",
            side_effect=lambda name: "/opt/homebrew/bin/brew" if name == "brew" else None,
        ):
            commands, notes = manim_runtime._system_commands(
                "Darwin", {"ffmpeg", "ffprobe", "cairo_pango", "latex"}
            )
        self.assertEqual(notes, [])
        flattened = [" ".join(command["argv"]) for command in commands]
        self.assertTrue(any("brew install ffmpeg cairo pango" in item for item in flattened))
        self.assertTrue(any("mactex-no-gui" in item for item in flattened))

    def test_linux_install_plan_uses_apt(self) -> None:
        with mock.patch.object(
            manim_runtime.shutil,
            "which",
            side_effect=lambda name: "/usr/bin/apt-get" if name == "apt-get" else None,
        ):
            commands, notes = manim_runtime._system_commands(
                "Linux", {"ffmpeg", "cairo_pango", "latex"}
            )
        self.assertEqual(notes, [])
        self.assertEqual(commands[0]["argv"][:3], ["sudo", "apt-get", "update"])
        install = " ".join(commands[1]["argv"])
        self.assertIn("libcairo2-dev", install)
        self.assertIn("texlive-latex-extra", install)

    def test_windows_install_plan_uses_winget(self) -> None:
        with mock.patch.object(
            manim_runtime.shutil,
            "which",
            side_effect=lambda name: "winget.exe" if name == "winget" else None,
        ):
            commands, notes = manim_runtime._system_commands(
                "Windows", {"ffmpeg", "latex"}
            )
        self.assertTrue(any("Gyan.FFmpeg" in command["argv"] for command in commands))
        self.assertTrue(any("MiKTeX.MiKTeX" in command["argv"] for command in commands))
        self.assertTrue(any("smoke test" in note for note in notes))

    def test_transcript_overlap_is_rejected_before_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "transcript.json"
            transcript.write_text(
                json.dumps(
                    [
                        {"start": 0, "end": 3, "text": "第一段"},
                        {"start": 2, "end": 4, "text": "第二段"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "overlaps"):
                manim_render._load_transcript(transcript)


if __name__ == "__main__":
    unittest.main(verbosity=2)
