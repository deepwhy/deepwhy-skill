#!/usr/bin/env python3
"""Tests for AskWhy node visual assets and Manim helpers."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import render_manim  # noqa: E402


class VisualContractTests(unittest.TestCase):
    def test_example_contains_static_and_manim_visuals(self) -> None:
        content = json.loads(
            (SKILL_ROOT / "examples" / "bulb-glow.json").read_text(encoding="utf-8")
        )
        kinds = [node.get("visual", {}).get("kind") for node in content["nodes"]]
        self.assertEqual(3, kinds.count("image"))
        self.assertEqual(4, kinds.count("manim"))

    def test_manim_scene_compiles(self) -> None:
        for name in (
            "electron-heat.py",
            "electron-drift.py",
            "voltage-field.py",
            "battery-voltage.py",
            "water-circuit-analogy.py",
        ):
            scene = SKILL_ROOT / "examples" / "media" / "bulb-glow" / name
            with self.subTest(scene=name):
                subprocess.run(
                    [sys.executable, "-m", "py_compile", str(scene)],
                    check=True,
                    capture_output=True,
                    text=True,
                )


class TranscriptTests(unittest.TestCase):
    def test_accepts_ordered_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transcript.json"
            path.write_text(
                json.dumps(
                    [
                        {"start": 0, "end": 2, "text": "第一步"},
                        {"start": 2, "end": 4, "text": "第二步"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            cues = render_manim._load_transcript(path)
        self.assertEqual(2, len(cues))

    def test_rejects_overlapping_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "transcript.json"
            path.write_text(
                json.dumps(
                    [
                        {"start": 0, "end": 3, "text": "第一步"},
                        {"start": 2, "end": 4, "text": "第二步"},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "overlaps"):
                render_manim._load_transcript(path)


class ManimCacheTests(unittest.TestCase):
    def test_cache_hit_reuses_video_without_starting_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene = root / "cache-scene.py"
            scene.write_text("class CacheScene: pass\n", encoding="utf-8")
            output = root / "output"
            output.mkdir()
            slug = "cache-scene"
            video = output / f"{slug}.webm"
            poster = output / f"{slug}.webp"
            video.write_bytes(b"video")
            poster.write_bytes(b"poster")
            cache_key = render_manim._cache_key(scene, "CacheScene", "medium")
            render_manim._cache_meta_path(output, slug).write_text(
                json.dumps(
                    {
                        "cacheVersion": 1,
                        "cacheKey": cache_key,
                        "sceneClass": "CacheScene",
                        "quality": "medium",
                        "durationSeconds": 4.2,
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(
                render_manim,
                "_executable",
                side_effect=AssertionError("renderer should not start"),
            ):
                result = render_manim.render(
                    scene,
                    "CacheScene",
                    output_dir=output,
                    alt="缓存动画",
                    caption="源码未变化时直接复用。",
                    transcript_path=None,
                    fallback_svg=None,
                    quality="medium",
                    max_duration=10,
                    max_video_bytes=1024,
                    force=False,
                )

        self.assertTrue(result["cached"])
        self.assertEqual(4.2, result["visual"]["durationSeconds"])
        self.assertEqual(str(video.resolve()), result["visual"]["videoSrc"])

    def test_scene_change_invalidates_cache_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scene = Path(tmp) / "cache-scene.py"
            scene.write_text("class CacheScene: pass\n", encoding="utf-8")
            first = render_manim._cache_key(scene, "CacheScene", "medium")
            scene.write_text("class CacheScene: changed = True\n", encoding="utf-8")
            second = render_manim._cache_key(scene, "CacheScene", "medium")
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
