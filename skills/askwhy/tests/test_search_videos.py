#!/usr/bin/env python3
"""Unit tests for AskWhy network-aware video discovery and ranking."""

from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import search_videos  # noqa: E402


def bilibili_payload() -> dict:
    return {
        "code": 0,
        "message": "OK",
        "data": {
            "result": [
                {
                    "type": "video",
                    "bvid": "BV1Physics01",
                    "title": "为什么苹果会落地？重力与自由落体物理解释",
                    "author": "科学课堂",
                    "description": "用实验解释重力如何使物体下落。",
                    "tag": "物理,重力,自由落体,科普",
                    "pic": "//i0.hdslb.com/test.jpg",
                    "play": 120000,
                    "like": 9000,
                    "review": 500,
                    "pubdate": 1704067200,
                    "duration": "7:31",
                },
                {
                    "type": "video",
                    "bvid": "BV1Song00001",
                    "title": "重力歌曲 MV",
                    "author": "音乐频道",
                    "description": "一首关于重力的歌。",
                    "tag": "音乐,歌曲",
                    "pic": "",
                    "play": 5000000,
                    "like": 100000,
                    "review": 3000,
                    "pubdate": 1704067200,
                    "duration": "3:05",
                },
            ]
        },
    }


def youtube_page() -> str:
    initial = {
        "contents": {
            "twoColumnSearchResultsRenderer": {
                "primaryContents": {
                    "sectionListRenderer": {
                        "contents": [
                            {
                                "itemSectionRenderer": {
                                    "contents": [
                                        {
                                            "videoRenderer": {
                                                "videoId": "abcDEF12345",
                                                "title": {
                                                    "runs": [
                                                        {
                                                            "text": "Why an apple falls: gravity explained"
                                                        }
                                                    ]
                                                },
                                                "ownerText": {
                                                    "runs": [{"text": "Science Lab"}]
                                                },
                                                "lengthText": {"simpleText": "6:42"},
                                                "publishedTimeText": {
                                                    "simpleText": "2 years ago"
                                                },
                                                "viewCountText": {
                                                    "simpleText": "1,250,000 views"
                                                },
                                                "thumbnail": {
                                                    "thumbnails": [
                                                        {
                                                            "url": "https://i.ytimg.com/vi/abcDEF12345/hqdefault.jpg"
                                                        }
                                                    ]
                                                },
                                                "detailedMetadataSnippets": [
                                                    {
                                                        "snippetText": {
                                                            "runs": [
                                                                {
                                                                    "text": "A physics experiment about gravity."
                                                                }
                                                            ]
                                                        }
                                                    }
                                                ],
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
    return (
        "<html><script>var ytInitialData = "
        + json.dumps(initial)
        + ";</script></html>"
    )


class NetworkTests(unittest.TestCase):
    def test_detect_network_prefers_global_when_youtube_reachable(self) -> None:
        def fake_probe(url: str, timeout: float) -> dict:
            return {
                "reachable": True,
                "httpStatus": 200,
                "latencyMs": 20,
                "failureKind": None,
            }

        with mock.patch.object(search_videos, "probe_url", side_effect=fake_probe):
            result = search_videos.detect_network(timeout=1)
        self.assertEqual("global", result["mode"])
        self.assertEqual(["bilibili", "youtube"], result["platformsToSearch"])

    def test_detect_network_returns_bilibili_only_mode(self) -> None:
        def fake_probe(url: str, timeout: float) -> dict:
            reachable = "bilibili" in url
            return {
                "reachable": reachable,
                "httpStatus": 200 if reachable else None,
                "latencyMs": 20,
                "failureKind": None if reachable else "timeout",
            }

        with mock.patch.object(search_videos, "probe_url", side_effect=fake_probe):
            result = search_videos.detect_network(timeout=1)
        self.assertEqual("cn", result["mode"])
        self.assertEqual(["bilibili"], result["platformsToSearch"])


class PlatformParserTests(unittest.TestCase):
    def test_bilibili_search_returns_canonical_video(self) -> None:
        body = json.dumps(bilibili_payload()).encode()
        with mock.patch.object(
            search_videos,
            "fetch_url",
            return_value=(200, body),
        ) as fetch:
            candidates = search_videos.search_bilibili(
                "为什么苹果会落地 重力 物理",
                2,
            )
        fetch.assert_called_once()
        self.assertEqual(2, len(candidates))
        self.assertEqual("BV1Physics01", candidates[0]["platformId"])
        self.assertEqual(
            "https://www.bilibili.com/video/BV1Physics01",
            candidates[0]["url"],
        )
        self.assertIn("player.bilibili.com", candidates[0]["embedUrl"])
        self.assertEqual(451, candidates[0]["durationSeconds"])
        self.assertGreater(
            candidates[0]["relevanceScore"],
            candidates[1]["relevanceScore"],
        )

    def test_youtube_parser_extracts_video_renderer(self) -> None:
        with mock.patch.object(
            search_videos,
            "fetch_url",
            return_value=(200, youtube_page().encode()),
        ):
            candidates = search_videos.search_youtube("why apple falls gravity", 2)
        self.assertEqual(1, len(candidates))
        candidate = candidates[0]
        self.assertEqual("abcDEF12345", candidate["platformId"])
        self.assertEqual("Science Lab", candidate["author"])
        self.assertEqual(402, candidate["durationSeconds"])
        self.assertEqual(1_250_000, candidate["metrics"]["views"])
        self.assertEqual(
            "https://www.youtube-nocookie.com/embed/abcDEF12345",
            candidate["embedUrl"],
        )


class RankingTests(unittest.TestCase):
    def test_relevant_explanation_outranks_high_view_song(self) -> None:
        query = "为什么苹果会落地 重力 物理 科普"
        relevant = {
            "title": "为什么苹果会落地？用实验理解重力",
            "tags": "物理,重力,实验,科普",
            "description": "解释自由落体与重力。",
            "author": "科学课堂",
            "durationSeconds": 480,
            "metrics": {"views": 10_000},
        }
        song = {
            "title": "重力歌曲 MV",
            "tags": "音乐,歌曲",
            "description": "一首关于重力的歌。",
            "author": "音乐频道",
            "durationSeconds": 180,
            "metrics": {"views": 10_000_000},
        }
        relevant_score, _ = search_videos.score_candidate(query, relevant)
        song_score, song_reasons = search_videos.score_candidate(query, song)
        self.assertGreater(relevant_score, song_score)
        self.assertTrue(
            any("降权关键词" in reason for reason in song_reasons),
            song_reasons,
        )

    def test_select_candidates_drops_irrelevant_music(self) -> None:
        candidates = [
            {
                "platform": "bilibili",
                "platformId": "relevant",
                "relevanceScore": 60,
                "rankingReasons": ["标题匹配"],
                "metrics": {"views": 100},
                "durationSeconds": 300,
            },
            {
                "platform": "bilibili",
                "platformId": "music",
                "relevanceScore": 90,
                "rankingReasons": ["降权关键词：歌曲、音乐"],
                "metrics": {"views": 5000000},
                "durationSeconds": 200,
            },
        ]
        selected = search_videos.select_candidates(candidates, 5, set())
        self.assertEqual(["relevant"], [item["platformId"] for item in selected])


class ReportTests(unittest.TestCase):
    def test_report_is_ready_to_review_and_merge(self) -> None:
        content = json.loads(
            (SKILL_ROOT / "examples" / "bulb-glow.json").read_text(encoding="utf-8")
        )
        content["nodes"] = content["nodes"][:4]
        network = {
            "mode": "cn",
            "checkedAt": "2026-10-26T00:00:00Z",
            "timeoutSeconds": 4,
            "platformsToSearch": ["bilibili"],
            "platforms": {
                "bilibili": {"reachable": True},
                "youtube": {"reachable": False},
            },
        }

        def fake_search(platform: str, query: str, timeout: float) -> list[dict]:
            self.assertEqual("bilibili", platform)
            return [
                {
                    "platform": "bilibili",
                    "platformId": f"BV{query[:4]}",
                    "title": query + " 物理解释",
                    "author": "科学课堂",
                    "url": f"https://www.bilibili.com/video/BV{query[:4]}",
                    "embedUrl": f"https://player.bilibili.com/player.html?bvid=BV{query[:4]}",
                    "thumbnailUrl": None,
                    "description": "解释这个问题的物理原理。",
                    "tags": "物理,科普",
                    "durationSeconds": 360,
                    "publishedAt": "2026-01-01",
                    "metrics": {"views": 1000},
                    "relevanceScore": 80,
                    "rankingReasons": ["标题匹配", "教育性关键词：物理"],
                }
            ]

        with mock.patch.object(
            search_videos,
            "search_platform",
            side_effect=fake_search,
        ), mock.patch.object(
            search_videos,
            "PLATFORM_MIN_INTERVAL",
            {"bilibili": 0, "youtube": 0},
        ):
            report = search_videos.research_content(
                content,
                platforms=["bilibili"],
                network=network,
                limit=2,
                timeout=1,
            )
        self.assertEqual(4, len(report["nodes"]))
        first = report["nodes"][0]["candidates"][0]
        self.assertEqual(1, first["rank"])
        self.assertIn("suggestedVideoLink", first)
        self.assertIn(
            "player.bilibili.com",
            first["suggestedVideoLink"]["embedUrl"],
        )
        self.assertNotIn("sourceIds", first["suggestedVideoLink"])
        self.assertNotIn("source", first)

    def test_parallel_search_is_bounded_and_preserves_node_order(self) -> None:
        content = json.loads(
            (SKILL_ROOT / "examples" / "bulb-glow.json").read_text(encoding="utf-8")
        )
        content["nodes"] = content["nodes"][:4]
        network = {
            "mode": "cn",
            "checkedAt": "2026-10-26T00:00:00Z",
            "timeoutSeconds": 4,
            "platformsToSearch": ["bilibili"],
            "platforms": {
                "bilibili": {"reachable": True},
                "youtube": {"reachable": False},
            },
        }
        lock = threading.Lock()
        active = 0
        max_active = 0

        def fake_search(platform: str, query: str, timeout: float) -> list[dict]:
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                time.sleep(0.03)
                marker = f"{abs(hash((platform, query))) % 10**8:08d}"
                return [
                    {
                        "platform": platform,
                        "platformId": f"BV{marker}{rank}",
                        "title": f"{query} 物理解释 {rank}",
                        "author": "科学课堂",
                        "url": f"https://www.bilibili.com/video/BV{marker}{rank}",
                        "embedUrl": (
                            "https://player.bilibili.com/player.html"
                            f"?bvid=BV{marker}{rank}&page=1"
                        ),
                        "thumbnailUrl": None,
                        "description": "解释这个问题的物理原理。",
                        "tags": "物理,科普",
                        "durationSeconds": 360,
                        "publishedAt": "2026-01-01",
                        "metrics": {"views": 1000},
                        "relevanceScore": 90 - rank,
                        "rankingReasons": ["标题匹配", "教育性关键词：物理"],
                    }
                    for rank in (0, 1)
                ]
            finally:
                with lock:
                    active -= 1

        with mock.patch.object(
            search_videos,
            "search_platform",
            side_effect=fake_search,
        ):
            report = search_videos.research_content(
                content,
                platforms=["bilibili"],
                network=network,
                limit=2,
                timeout=1,
            )

        self.assertEqual(
            [node["id"] for node in content["nodes"]],
            [node["nodeId"] for node in report["nodes"]],
        )
        self.assertEqual(1, max_active)
        self.assertEqual([], report["errors"])

    def test_parallel_selection_matches_sequential_reference(self) -> None:
        content = json.loads(
            (SKILL_ROOT / "examples" / "bulb-glow.json").read_text(encoding="utf-8")
        )
        content["nodes"] = content["nodes"][:4]
        network = {
            "mode": "global",
            "checkedAt": "2026-10-26T00:00:00Z",
            "timeoutSeconds": 4,
            "platformsToSearch": ["bilibili", "youtube"],
            "platforms": {
                "bilibili": {"reachable": True},
                "youtube": {"reachable": True},
            },
        }
        platforms = ["bilibili", "youtube"]

        def fake_search(platform: str, query: str, timeout: float) -> list[dict]:
            marker = hashlib.sha1(f"{platform}\0{query}".encode()).hexdigest()[:8]
            return [
                {
                    "platform": platform,
                    "platformId": marker,
                    "title": query + " 物理解释",
                    "author": "科学课堂",
                    "url": f"https://example.com/{marker}",
                    "embedUrl": f"https://example.com/embed/{marker}",
                    "thumbnailUrl": None,
                    "description": "解释这个问题的物理原理。",
                    "tags": "物理,科普",
                    "durationSeconds": 360,
                    "publishedAt": "2026-01-01",
                    "metrics": {"views": 1000},
                    "relevanceScore": 80,
                    "rankingReasons": ["标题匹配", "教育性关键词：物理"],
                }
            ]

        excluded: set[str] = set()
        expected: dict[str, list[str]] = {}
        for node in content["nodes"]:
            raw: list[dict] = []
            for query in dict.fromkeys(
                (
                    search_videos.make_query(content, node, fallback=False),
                    search_videos.make_query(content, node, fallback=True),
                )
            ):
                for platform in platforms:
                    raw.extend(fake_search(platform, query, 1))
                preview = search_videos.select_candidates(raw, 2, excluded)
                if len(preview) >= min(3, 2):
                    break
            selected = search_videos.select_candidates(raw, 2, excluded)
            expected[node["id"]] = [item["platformId"] for item in selected]
            excluded.update(item["platformId"] for item in selected)

        with mock.patch.object(
            search_videos,
            "search_platform",
            side_effect=fake_search,
        ), mock.patch.object(
            search_videos,
            "PLATFORM_MIN_INTERVAL",
            {"bilibili": 0, "youtube": 0},
        ):
            report = search_videos.research_content(
                content,
                platforms=platforms,
                network=network,
                limit=2,
                timeout=1,
            )

        actual = {
            node["nodeId"]: [item["platformId"] for item in node["candidates"]]
            for node in report["nodes"]
        }
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
