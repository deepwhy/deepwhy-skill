#!/usr/bin/env python3
"""Validate AskWhy causal-chain content before building a standalone page."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


SCHEMA_VERSION = "8.0"
NODE_TYPES = {
    "phenomenon",
    "mechanism",
    "principle",
    "evidence",
    "foundation",
    "boundary",
}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|FIXME|lorem ipsum|place your .* here)\b", re.IGNORECASE
)
SEARCH_HOSTS = {
    "baidu.com",
    "bing.com",
    "duckduckgo.com",
    "google.com",
    "search.bilibili.com",
    "youtube.com",
    "youtu.be",
}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_text(report: Report, path: str, value: Any) -> None:
    if not _text(value):
        report.error(path, "must be a non-empty string")


def _require_keys(
    report: Report, path: str, value: dict[str, Any], keys: tuple[str, ...]
) -> None:
    for key in keys:
        if key not in value:
            report.error(path, f"missing required key '{key}'")


def _check_keys(
    report: Report,
    path: str,
    value: dict[str, Any],
    allowed: set[str],
) -> None:
    for key in sorted(set(value) - allowed):
        report.error(f"{path}.{key}", "unexpected key")


def _check_date(report: Report, path: str, value: Any, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str):
        report.error(path, "must be a YYYY-MM-DD string" + (" or null" if nullable else ""))
        return
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        report.error(path, "must be a valid YYYY-MM-DD date")


def _is_search_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = parsed.path.lower()
    query = parse_qs(parsed.query)
    if any(host == candidate or host.endswith(f".{candidate}") for candidate in SEARCH_HOSTS):
        if host in {"google.com", "bing.com", "baidu.com", "duckduckgo.com"}:
            return True
        if host == "search.bilibili.com":
            return True
        if path in {"", "/", "/results", "/search"} or "search_query" in query:
            return True
    if any(marker in path for marker in ("/results", "/search")):
        return True
    return any(key in query for key in ("q", "query", "search_query", "keyword"))


def _check_url(report: Report, path: str, value: Any) -> None:
    if not _text(value):
        report.error(path, "must be a non-empty absolute URL")
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        report.error(path, "must be an absolute http(s) URL")
        return
    if _is_search_url(value):
        report.error(path, "must link to a specific resource, not a search result")
    if parsed.username or parsed.password:
        report.error(path, "must not contain credentials")
def _check_id(report: Report, path: str, value: Any) -> None:
    if not _text(value):
        report.error(path, "must be a non-empty lowercase hyphen-case ID")
    elif not ID_PATTERN.fullmatch(value):
        report.error(path, "must use lowercase hyphen-case")


def _check_tags(report: Report, path: str, value: Any) -> None:
    if not isinstance(value, list) or not 1 <= len(value) <= 3:
        report.error(path, "must contain 1–3 tags")
        return
    if len(set(value)) != len(value):
        report.error(path, "must not contain duplicate tags")
    for index, tag in enumerate(value):
        _require_text(report, f"{path}[{index}]", tag)


def _check_experiment(report: Report, path: str, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        report.error(path, "must be an object or null")
        return
    _check_keys(report, path, value, {"title", "steps"})
    _require_keys(report, path, value, ("title", "steps"))
    _require_text(report, f"{path}.title", value.get("title"))
    steps = value.get("steps")
    if not isinstance(steps, list) or not 2 <= len(steps) <= 5:
        report.error(f"{path}.steps", "must contain 2–5 steps")
        return
    for index, step in enumerate(steps):
        _require_text(report, f"{path}.steps[{index}]", step)


def _check_analogy(report: Report, path: str, value: Any) -> None:
    if not isinstance(value, dict):
        report.error(path, "must be an object")
        return
    _check_keys(report, path, value, {"title", "scene", "mappings", "limit", "visual"})
    _require_keys(report, path, value, ("title", "scene", "mappings", "limit"))
    for key in ("title", "scene", "limit"):
        _require_text(report, f"{path}.{key}", value.get(key))
    mappings = value.get("mappings")
    if not isinstance(mappings, list) or not 2 <= len(mappings) <= 4:
        report.error(f"{path}.mappings", "must contain 2–4 familiar-to-concept mappings")
        return
    for index, mapping in enumerate(mappings):
        mapping_path = f"{path}.mappings[{index}]"
        if not isinstance(mapping, dict):
            report.error(mapping_path, "must be an object")
            continue
        _check_keys(report, mapping_path, mapping, {"familiar", "concept"})
        _require_keys(report, mapping_path, mapping, ("familiar", "concept"))
        _require_text(report, f"{mapping_path}.familiar", mapping.get("familiar"))
        _require_text(report, f"{mapping_path}.concept", mapping.get("concept"))
    if value.get("visual") is not None:
        _check_visual(report, f"{path}.visual", value.get("visual"))


def _check_asset_source(
    report: Report,
    path: str,
    value: Any,
    *,
    suffixes: tuple[str, ...],
    data_pattern: str,
) -> None:
    if not _text(value):
        report.error(path, "must be a local asset path or inline data URI")
        return
    if value.startswith("data:"):
        if not re.fullmatch(data_pattern, value):
            report.error(path, "must use the expected image/video data URI type")
        return
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        report.error(path, "must be a local path, not a remote URL")
    if not value.lower().endswith(suffixes):
        report.error(path, f"must point to one of: {', '.join(suffixes)}")


def _check_visual(
    report: Report,
    path: str,
    value: Any,
) -> None:
    if not isinstance(value, dict):
        report.error(path, "must be an object")
        return
    kind = value.get("kind")
    if kind == "image":
        _check_keys(report, path, value, {"kind", "src", "alt", "caption"})
        _require_keys(report, path, value, ("kind", "src", "alt", "caption"))
        _check_asset_source(
            report,
            f"{path}.src",
            value.get("src"),
            suffixes=(".svg", ".png", ".jpg", ".jpeg", ".webp"),
            data_pattern=(
                r"data:image/(?:svg\+xml|png|jpeg|webp);base64,[A-Za-z0-9+/=\s]+"
            ),
        )
    elif kind == "manim":
        _check_keys(
            report,
            path,
            value,
            {
                "kind",
                "sceneSource",
                "sceneClass",
                "videoSrc",
                "posterSrc",
                "durationSeconds",
                "alt",
                "caption",
                "transcript",
                "fallbackSvg",
            },
        )
        _require_keys(
            report,
            path,
            value,
            (
                "kind",
                "sceneSource",
                "sceneClass",
                "videoSrc",
                "posterSrc",
                "durationSeconds",
                "alt",
                "caption",
                "transcript",
                "fallbackSvg",
            ),
        )
        _check_asset_source(
            report,
            f"{path}.videoSrc",
            value.get("videoSrc"),
            suffixes=(".webm",),
            data_pattern=r"data:video/webm;base64,[A-Za-z0-9+/=\s]+",
        )
        _check_asset_source(
            report,
            f"{path}.posterSrc",
            value.get("posterSrc"),
            suffixes=(".webp", ".png", ".jpg", ".jpeg"),
            data_pattern=r"data:image/(?:webp|png|jpeg);base64,[A-Za-z0-9+/=\s]+",
        )
        scene_source = value.get("sceneSource")
        if not _text(scene_source) or not scene_source.lower().endswith(".py"):
            report.error(f"{path}.sceneSource", "must point to a .py Manim scene")
        scene_class = value.get("sceneClass")
        if not isinstance(scene_class, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            scene_class,
        ):
            report.error(f"{path}.sceneClass", "must be a valid Python class name")
        duration = value.get("durationSeconds")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not 1 <= duration <= 30
        ):
            report.error(f"{path}.durationSeconds", "must be from 1 to 30 seconds")
        fallback_svg = value.get("fallbackSvg")
        if not _text(fallback_svg) or "<svg" not in fallback_svg.lower():
            report.error(f"{path}.fallbackSvg", "must contain an inline SVG")
        transcript = value.get("transcript")
        if not isinstance(transcript, list):
            report.error(f"{path}.transcript", "must be an array")
        else:
            previous_end = 0.0
            for index, cue in enumerate(transcript):
                cue_path = f"{path}.transcript[{index}]"
                if not isinstance(cue, dict):
                    report.error(cue_path, "must be an object")
                    continue
                _check_keys(report, cue_path, cue, {"start", "end", "text"})
                _require_keys(report, cue_path, cue, ("start", "end", "text"))
                start = cue.get("start")
                end = cue.get("end")
                if (
                    not isinstance(start, (int, float))
                    or isinstance(start, bool)
                    or not isinstance(end, (int, float))
                    or isinstance(end, bool)
                    or start < 0
                    or end <= start
                ):
                    report.error(cue_path, "needs numeric start/end with end > start")
                elif start < previous_end:
                    report.error(cue_path, "must not overlap the previous cue")
                else:
                    previous_end = float(end)
                _require_text(report, f"{cue_path}.text", cue.get("text"))
    else:
        report.error(f"{path}.kind", "must be 'image' or 'manim'")
        return

    for key in ("alt", "caption"):
        _require_text(report, f"{path}.{key}", value.get(key))
def _check_video(
    report: Report,
    path: str,
    value: Any,
) -> None:
    if not isinstance(value, dict):
        report.error(path, "must be an object")
        return
    _check_keys(
        report,
        path,
        value,
        {
            "id",
            "title",
            "url",
            "embedUrl",
            "platform",
            "author",
            "thumbnailUrl",
            "durationSeconds",
            "publishedAt",
            "queryDate",
            "relevanceScore",
            "selectionRationale",
        },
    )
    _require_keys(
        report,
        path,
        value,
        ("id", "title", "url", "embedUrl", "platform"),
    )
    _check_id(report, f"{path}.id", value.get("id"))
    _require_text(report, f"{path}.title", value.get("title"))
    _check_url(report, f"{path}.url", value.get("url"))
    _check_url(report, f"{path}.embedUrl", value.get("embedUrl"))
    platform = value.get("platform")
    if platform not in {"bilibili", "youtube"}:
        report.error(f"{path}.platform", "must be 'bilibili' or 'youtube'")
    page_url = urlparse(value.get("url", ""))
    embed_url = urlparse(value.get("embedUrl", ""))
    if platform == "bilibili":
        page_match = re.search(r"/video/(BV[0-9A-Za-z]+)", page_url.path)
        embed_bvid = parse_qs(embed_url.query).get("bvid", [None])[0]
        if embed_url.netloc != "player.bilibili.com":
            report.error(
                f"{path}.embedUrl",
                "Bilibili embed must use player.bilibili.com",
            )
        if not page_match or embed_bvid != page_match.group(1):
            report.error(
                f"{path}.embedUrl",
                "Bilibili embed BVID must match the page URL",
            )
    elif platform == "youtube":
        page_video_id = parse_qs(page_url.query).get("v", [None])[0]
        embed_match = re.fullmatch(r"/embed/([\w-]+)", embed_url.path)
        if embed_url.netloc not in {"www.youtube-nocookie.com", "www.youtube.com"}:
            report.error(
                f"{path}.embedUrl",
                "YouTube embed must use youtube.com or youtube-nocookie.com",
            )
        if not embed_match or embed_match.group(1) != page_video_id:
            report.error(
                f"{path}.embedUrl",
                "YouTube embed video ID must match the page URL",
            )
    if "author" in value and value["author"] is not None:
        _require_text(report, f"{path}.author", value["author"])
    if "thumbnailUrl" in value and value["thumbnailUrl"] is not None:
        _check_url(report, f"{path}.thumbnailUrl", value["thumbnailUrl"])
    if "durationSeconds" in value and value["durationSeconds"] is not None:
        duration = value["durationSeconds"]
        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or not 0 <= duration <= 7200
        ):
            report.error(
                f"{path}.durationSeconds",
                "must be an integer from 0 to 7200 or null",
            )
    if "publishedAt" in value:
        _check_date(
            report,
            f"{path}.publishedAt",
            value["publishedAt"],
            nullable=True,
        )
    if "queryDate" in value:
        _check_date(report, f"{path}.queryDate", value["queryDate"])
    if "relevanceScore" in value:
        score = value["relevanceScore"]
        if (
            not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not 0 <= score <= 100
        ):
            report.error(
                f"{path}.relevanceScore",
                "must be a number from 0 to 100",
            )
    if "selectionRationale" in value:
        _require_text(
            report,
            f"{path}.selectionRationale",
            value["selectionRationale"],
        )


def _check_placeholder(report: Report, path: str, value: Any) -> None:
    if isinstance(value, str) and PLACEHOLDER_PATTERN.search(value):
        report.error(path, "contains unfinished placeholder text")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_placeholder(report, f"{path}[{index}]", child)
    elif isinstance(value, dict):
        for key, child in value.items():
            _check_placeholder(report, f"{path}.{key}", child)


def validate_content(content: Any) -> Report:
    report = Report()
    if not isinstance(content, dict):
        report.error("$", "must be a JSON object")
        return report

    required = ("schemaVersion", "meta", "center", "nodes")
    _require_keys(report, "$", content, required)
    _check_keys(report, "$", content, set(required))
    if content.get("schemaVersion") != SCHEMA_VERSION:
        report.error("$.schemaVersion", f"must be '{SCHEMA_VERSION}'")

    meta = content.get("meta")
    if not isinstance(meta, dict):
        report.error("$.meta", "must be an object")
    else:
        _check_keys(
            report,
            "$.meta",
            meta,
            {
                "topic",
                "question",
                "slug",
                "summary",
                "category",
                "estimatedMinutes",
                "language",
                "asOf",
                "audience",
                "learningLevel",
                "evidenceGaps",
            },
        )
        _require_keys(
            report,
            "$.meta",
            meta,
            (
                "topic",
                "question",
                "slug",
                "summary",
                "category",
                "estimatedMinutes",
                "language",
                "asOf",
                "audience",
                "learningLevel",
                "evidenceGaps",
            ),
        )
        for key in ("topic", "question", "summary", "category", "language", "audience"):
            _require_text(report, f"$.meta.{key}", meta.get(key))
        if meta.get("learningLevel") not in {"primary", "middle", "high"}:
            report.error(
                "$.meta.learningLevel",
                "must be primary, middle, or high",
            )
        _check_id(report, "$.meta.slug", meta.get("slug"))
        minutes = meta.get("estimatedMinutes")
        if not isinstance(minutes, int) or isinstance(minutes, bool) or not 1 <= minutes <= 120:
            report.error("$.meta.estimatedMinutes", "must be an integer from 1 to 120")
        _check_date(report, "$.meta.asOf", meta.get("asOf"))
        gaps = meta.get("evidenceGaps")
        if not isinstance(gaps, list):
            report.error("$.meta.evidenceGaps", "must be an array")
        else:
            for index, gap in enumerate(gaps):
                _require_text(report, f"$.meta.evidenceGaps[{index}]", gap)

    center = content.get("center")
    if not isinstance(center, dict):
        report.error("$.center", "must be an object")
    else:
        _check_keys(
            report,
            "$.center",
            center,
            {
                "id",
                "question",
                "summary",
                "insight",
                "tags",
                "overviewVisual",
                "analogy",
            },
        )
        _require_keys(
            report,
            "$.center",
            center,
            (
                "id",
                "question",
                "summary",
                "insight",
                "tags",
                "overviewVisual",
                "analogy",
            ),
        )
        if center.get("id") != "root":
            report.error("$.center.id", "must be 'root'")
        for key in ("question", "summary", "insight"):
            _require_text(report, f"$.center.{key}", center.get(key))
        _check_tags(report, "$.center.tags", center.get("tags"))
        overview = center.get("overviewVisual")
        if not isinstance(overview, dict) or overview.get("kind") != "image":
            report.error("$.center.overviewVisual", "must be a static image visual")
        else:
            _check_visual(report, "$.center.overviewVisual", overview)
        _check_analogy(report, "$.center.analogy", center.get("analogy"))

    nodes = content.get("nodes")
    if not isinstance(nodes, list) or not 4 <= len(nodes) <= 8:
        report.error("$.nodes", "must contain 4–8 causal-chain steps")
        nodes = nodes if isinstance(nodes, list) else []
    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        path = f"$.nodes[{index}]"
        if not isinstance(node, dict):
            report.error(path, "must be an object")
            continue
        _check_keys(
            report,
            path,
            node,
            {
                "id",
                "parentId",
                "type",
                "question",
                "label",
                "answer",
                "summary",
                "nextQuestion",
                "knowledge",
                "facts",
                "tags",
                "analogy",
                "experiment",
                "visual",
                "videoLinks",
            },
        )
        _require_keys(
            report,
            path,
            node,
            (
                "id",
                "parentId",
                "type",
                "question",
                "label",
                "answer",
                "summary",
                "nextQuestion",
                "knowledge",
                "facts",
                "tags",
                "analogy",
            ),
        )
        node_id = node.get("id")
        _check_id(report, f"{path}.id", node_id)
        if isinstance(node_id, str):
            if node_id == "root":
                report.error(f"{path}.id", "'root' is reserved for the center question")
            elif node_id in node_ids:
                report.error(f"{path}.id", f"duplicate node ID '{node_id}'")
            node_ids.add(node_id)
        previous = nodes[index - 1] if index > 0 else {}
        expected_parent = (
            "root"
            if index == 0
            else previous.get("id") if isinstance(previous, dict) else None
        )
        if node.get("parentId") != expected_parent:
            report.error(
                f"{path}.parentId",
                f"must be '{expected_parent}' to keep one ordered causal chain",
            )
        if node.get("type") not in NODE_TYPES:
            report.error(f"{path}.type", f"must be one of {sorted(NODE_TYPES)}")
        for key in ("question", "label", "answer", "summary"):
            _require_text(report, f"{path}.{key}", node.get(key))
        answer = node.get("answer")
        if isinstance(answer, str) and len(answer.strip()) > 140:
            report.warn(path + ".answer", "keep the one-sentence answer <=140 characters")
        next_question = node.get("nextQuestion")
        if index < len(nodes) - 1:
            _require_text(report, f"{path}.nextQuestion", next_question)
            following = nodes[index + 1]
            following_question = (
                following.get("question") if isinstance(following, dict) else None
            )
            if next_question != following_question:
                report.error(
                    f"{path}.nextQuestion",
                    "must exactly match the next node's question",
                )
        elif next_question is not None:
            report.error(
                f"{path}.nextQuestion",
                "must be null on the final node",
            )
        _check_tags(report, f"{path}.tags", node.get("tags"))
        _check_analogy(report, f"{path}.analogy", node.get("analogy"))
        knowledge = node.get("knowledge")
        _require_text(report, f"{path}.knowledge", knowledge)
        facts = node.get("facts")
        if not isinstance(facts, list) or not 2 <= len(facts) <= 4:
            report.error(f"{path}.facts", "must contain 2–4 facts")
        else:
            for fact_index, fact in enumerate(facts):
                _require_text(report, f"{path}.facts[{fact_index}]", fact)
        _check_experiment(report, f"{path}.experiment", node.get("experiment"))
        if node.get("visual") is not None:
            _check_visual(
                report,
                f"{path}.visual",
                node.get("visual"),
            )
        videos = node.get("videoLinks", [])
        if not isinstance(videos, list):
            report.error(f"{path}.videoLinks", "must be an array; use [] when no video is verified")
        else:
            if len(videos) > 2:
                report.error(f"{path}.videoLinks", "must contain at most 2 videos")
            video_ids: set[str] = set()
            for video_index, video in enumerate(videos):
                _check_video(
                    report,
                    f"{path}.videoLinks[{video_index}]",
                    video,
                )
                if isinstance(video, dict) and isinstance(video.get("id"), str):
                    if video["id"] in video_ids:
                        report.error(
                            f"{path}.videoLinks[{video_index}].id",
                            f"duplicate video ID '{video['id']}' within this node",
                        )
                    video_ids.add(video["id"])

    _check_placeholder(report, "$", content)
    return report


def load_content(path: Path) -> tuple[Any | None, Report]:
    report = Report()
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error("$", f"file not found: {path}")
        return None, report
    except (OSError, json.JSONDecodeError) as error:
        report.error("$", f"could not load JSON: {error}")
        return None, report
    validation = validate_content(content)
    report.errors = validation.errors
    report.warnings = validation.warnings
    return content, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content", type=Path, help="AskWhy content JSON")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    args = parser.parse_args()

    _, report = load_content(args.content)
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        for warning in report.warnings:
            print(f"WARNING {warning}", file=sys.stderr)
        for error in report.errors:
            print(f"ERROR   {error}", file=sys.stderr)
        if report.ok:
            print(f"Valid AskWhy {SCHEMA_VERSION} content: {args.content}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
