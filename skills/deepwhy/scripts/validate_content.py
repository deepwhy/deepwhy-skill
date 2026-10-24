#!/usr/bin/env python3
"""Validate DeepWhy knowledge-chain content before building a page."""

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


SCHEMA_VERSION = "2.0"
STYLE_PRESETS = {"deepwhy", "atlas", "chronicle", "fieldnotes"}
NODE_TYPES = ["phenomenon", "mechanism", "principle", "theory", "frontier", "boundary"]
NODE_RANK = {name: index for index, name in enumerate(NODE_TYPES)}
CONTENT_STATUSES = {"complete", "partial", "insufficient"}
SOURCE_KINDS = {
    "paper",
    "official",
    "reference",
    "standard",
    "book",
    "report",
    "dataset",
    "video",
    "other",
}
EVENT_TYPES = {
    "background",
    "paper",
    "proposal",
    "prototype",
    "operational",
    "adoption",
    "boundary",
}
CLAIM_STATUSES = {"verified", "research", "speculative"}
QUIZ_TYPES = {"concept", "derivation", "counterexample", "prediction", "transfer"}
ARCHETYPES = {
    "phenomenon_exploration",
    "principle_derivation",
    "historical_evolution",
    "cross_domain_connection",
    "understanding_assessment",
}
INTERACTION_KINDS = {"inverse-square", "range", "prediction", "toggle"}
LAB_KINDS = {
    "simulation",
    "diagram",
    "code",
    "game",
    "spatial3d",
    "procedural",
}
VISUAL_KINDS = {
    "illustration",
    "force",
    "motion",
    "geometry",
    "equation",
    "graph",
    "architecture",
    "execution_trace",
    "timeline",
    "comparison",
    "causal",
    "feedback_loop",
    "evidence",
}
MANIM_KEYS = {
    "sceneSource",
    "sceneClass",
    "videoSrc",
    "posterSrc",
    "durationSeconds",
    "alt",
    "caption",
    "transcript",
    "fallbackSvg",
}
PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|FIXME|lorem ipsum|place your .* here)\b", re.IGNORECASE
)


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


def _date(report: Report, path: str, value: Any) -> None:
    if not isinstance(value, str):
        report.error(path, "must be a YYYY-MM-DD string")
        return
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        report.error(path, "must be a valid YYYY-MM-DD date")


def _url(report: Report, path: str, value: Any) -> None:
    if not _text(value):
        report.error(path, "must be a non-empty URL")
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        report.error(path, "must be an absolute http(s) URL")


def _local_path(report: Report, path: str, value: Any, suffix: str) -> None:
    if not _text(value):
        report.error(path, "must be a non-empty local path")
        return
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        report.error(path, "must be a local path, not a URL")
    if not value.lower().endswith(suffix):
        report.error(path, f"must point to a {suffix} file")


def _source_refs(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key == "sourceIds":
                yield child_path, child
            else:
                yield from _source_refs(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _source_refs(child, f"{path}[{index}]")


def _require_sources(report: Report, path: str, item: dict[str, Any]) -> None:
    refs = item.get("sourceIds")
    if not isinstance(refs, list) or not refs:
        report.error(f"{path}.sourceIds", "substantive content needs at least one source")


def _required(report: Report, path: str, obj: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        if key not in obj:
            report.error(path, f"missing required key '{key}'")


def _array(report: Report, path: str, value: Any, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        report.error(path, "must be an array")
        return []
    if nonempty and not value:
        report.error(path, "must not be empty")
    return value


def _short_answer(report: Report, path: str, value: Any) -> None:
    if not _text(value):
        report.error(path, "must be a non-empty string")
        return
    length = len(value.strip())
    if length < 12:
        report.error(path, "must contain a complete one-sentence answer (>=12 chars)")
    elif length > 60:
        report.error(path, "must stay <=60 chars to prevent a main-surface text wall")
    elif length < 20:
        report.warn(path, "target 20–60 chars for a complete one-sentence answer")


def _check_visual(report: Report, path: str, visual: dict[str, Any]) -> None:
    if visual.get("mode") not in {"svg", "image"}:
        report.error(f"{path}.mode", "must be svg or image")
    if visual.get("kind") not in VISUAL_KINDS:
        report.error(f"{path}.kind", f"must be one of {sorted(VISUAL_KINDS)}")
    if visual.get("mode") == "svg" and not _text(visual.get("svg")):
        report.error(f"{path}.svg", "required for SVG mode")
    if visual.get("mode") == "image":
        _url(report, f"{path}.src", visual.get("src"))
    for key in ("alt", "caption"):
        if not _text(visual.get(key)):
            report.error(f"{path}.{key}", "must be non-empty")
    formula = visual.get("formula")
    if formula is not None and not isinstance(formula, str):
        report.error(f"{path}.formula", "must be a string or null")
    _require_sources(report, path, visual)

    interaction = visual.get("interaction")
    if interaction is None:
        return
    interaction_path = f"{path}.interaction"
    if not isinstance(interaction, dict):
        report.error(interaction_path, "must be an object or null")
        return
    kind = interaction.get("kind")
    if kind not in INTERACTION_KINDS:
        report.error(
            f"{interaction_path}.kind",
            f"must be one of {sorted(INTERACTION_KINDS)}",
        )
        return
    if not _text(interaction.get("prompt")):
        report.error(f"{interaction_path}.prompt", "must be non-empty")

    if kind in {"inverse-square", "range"}:
        _required(
            report,
            interaction_path,
            interaction,
            ("label", "min", "max", "step", "initial", "resultTemplate"),
        )
        for key in ("label", "resultTemplate"):
            if not _text(interaction.get(key)):
                report.error(f"{interaction_path}.{key}", "must be non-empty")
        numeric: dict[str, float] = {}
        for key in ("min", "max", "step", "initial"):
            value = interaction.get(key)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                report.error(f"{interaction_path}.{key}", "must be a number")
            elif key == "step" and float(value) <= 0:
                report.error(f"{interaction_path}.step", "must be positive")
            elif kind == "inverse-square" and float(value) <= 0:
                report.error(f"{interaction_path}.{key}", "must be positive")
            else:
                numeric[key] = float(value)
        if len(numeric) == 4:
            if numeric["min"] >= numeric["max"]:
                report.error(interaction_path, "min must be less than max")
            if not numeric["min"] <= numeric["initial"] <= numeric["max"]:
                report.error(interaction_path, "initial must be within min and max")
        return

    if kind == "prediction":
        _required(report, interaction_path, interaction, ("options", "correctIndex"))
        options = _array(report, f"{interaction_path}.options", interaction.get("options"))
        if not 2 <= len(options) <= 4:
            report.error(f"{interaction_path}.options", "must contain 2–4 options")
        for option_index, option in enumerate(options):
            option_path = f"{interaction_path}.options[{option_index}]"
            if not isinstance(option, dict):
                report.error(option_path, "must be an object")
                continue
            _required(report, option_path, option, ("label", "feedback"))
            for key in ("label", "feedback"):
                if not _text(option.get(key)):
                    report.error(f"{option_path}.{key}", "must be non-empty")
        correct_index = interaction.get("correctIndex")
        if (
            not isinstance(correct_index, int)
            or isinstance(correct_index, bool)
            or not 0 <= correct_index < len(options)
        ):
            report.error(
                f"{interaction_path}.correctIndex",
                "must point to an existing option",
            )
        return

    _required(
        report,
        interaction_path,
        interaction,
        (
            "label",
            "onLabel",
            "offLabel",
            "onFeedback",
            "offFeedback",
            "initial",
        ),
    )
    for key in ("label", "onLabel", "offLabel", "onFeedback", "offFeedback"):
        if not _text(interaction.get(key)):
            report.error(f"{interaction_path}.{key}", "must be non-empty")
    if not isinstance(interaction.get("initial"), bool):
        report.error(f"{interaction_path}.initial", "must be a boolean")


def _check_manim(report: Report, path: str, manim: dict[str, Any]) -> None:
    _required(report, path, manim, tuple(sorted(MANIM_KEYS)))
    for key in sorted(set(manim) - MANIM_KEYS):
        report.error(path, f"unknown key '{key}'")
    _local_path(report, f"{path}.sceneSource", manim.get("sceneSource"), ".py")
    _local_path(report, f"{path}.videoSrc", manim.get("videoSrc"), ".webm")
    _local_path(report, f"{path}.posterSrc", manim.get("posterSrc"), ".webp")
    scene_class = manim.get("sceneClass")
    if not isinstance(scene_class, str) or not re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*", scene_class
    ):
        report.error(f"{path}.sceneClass", "must be a valid Python class identifier")
    duration = manim.get("durationSeconds")
    if (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not 0 < float(duration) <= 30
    ):
        report.error(f"{path}.durationSeconds", "must be a number from 0 to 30 seconds")
    for key in ("alt", "caption"):
        if not _text(manim.get(key)):
            report.error(f"{path}.{key}", "must be non-empty")
    fallback_svg = manim.get("fallbackSvg")
    if not isinstance(fallback_svg, str) or "<svg" not in fallback_svg.lower():
        report.error(f"{path}.fallbackSvg", "must contain an inline SVG fallback")
    elif "<script" in fallback_svg.lower():
        report.error(f"{path}.fallbackSvg", "must not contain scripts")

    transcript = manim.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        report.error(f"{path}.transcript", "must contain at least one caption cue")
        return
    previous_end = -1.0
    for index, cue in enumerate(transcript):
        cue_path = f"{path}.transcript[{index}]"
        if not isinstance(cue, dict):
            report.error(cue_path, "must be an object")
            continue
        for key in ("start", "end", "text"):
            if key not in cue:
                report.error(cue_path, f"missing required key '{key}'")
        for key in sorted(set(cue) - {"start", "end", "text"}):
            report.error(cue_path, f"unknown key '{key}'")
        start = cue.get("start")
        end = cue.get("end")
        if (
            not isinstance(start, (int, float))
            or isinstance(start, bool)
            or not isinstance(end, (int, float))
            or isinstance(end, bool)
            or float(start) < 0
            or float(end) <= float(start)
        ):
            report.error(cue_path, "start/end must be numbers with 0 <= start < end")
        elif float(start) < previous_end:
            report.error(cue_path, "caption cues must be ordered and non-overlapping")
        else:
            previous_end = float(end)
        if not _text(cue.get("text")):
            report.error(f"{cue_path}.text", "must be non-empty")


def validate_content(data: Any) -> Report:
    report = Report()
    if not isinstance(data, dict):
        report.error("$", "top-level content must be an object")
        return report

    top_keys = {
        "schemaVersion",
        "meta",
        "presentation",
        "sources",
        "chain",
        "videos",
        "background",
        "assessment",
        "nextQuestions",
    }
    _required(report, "$", data, tuple(top_keys))
    for key in sorted(set(data) - top_keys):
        report.error("$", f"unknown top-level key '{key}'")
    if data.get("schemaVersion") != SCHEMA_VERSION:
        report.error("$.schemaVersion", f"must be '{SCHEMA_VERSION}'")

    meta = data.get("meta")
    if not isinstance(meta, dict):
        report.error("$.meta", "must be an object")
        meta = {}
    else:
        _required(
            report,
            "$.meta",
            meta,
            (
                "topic",
                "question",
                "slug",
                "hook",
                "asOf",
                "language",
                "audience",
                "premiseCheck",
                "scope",
                "evidenceGaps",
            ),
        )
        for key in ("topic", "question", "hook"):
            if not _text(meta.get(key)):
                report.error(f"$.meta.{key}", "must be a non-empty string")
        if isinstance(meta.get("hook"), str) and len(meta["hook"]) > 180:
            report.error("$.meta.hook", "must be <=180 chars")
        slug = meta.get("slug")
        if not isinstance(slug, str) or not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", slug
        ):
            report.error("$.meta.slug", "must be lowercase ASCII hyphen-case")
        _date(report, "$.meta.asOf", meta.get("asOf"))

        audience = meta.get("audience")
        if not isinstance(audience, dict):
            report.error("$.meta.audience", "must be an object")
        else:
            for key in ("description", "priorKnowledge"):
                if not _text(audience.get(key)):
                    report.error(f"$.meta.audience.{key}", "must be non-empty")
            if audience.get("explanationLevel") not in {
                "child",
                "beginner",
                "teen",
                "expert",
            }:
                report.error(
                    "$.meta.audience.explanationLevel",
                    "must be child, beginner, teen, or expert",
                )
            _array(report, "$.meta.audience.assumptions", audience.get("assumptions"))

        premise = meta.get("premiseCheck")
        if not isinstance(premise, dict):
            report.error("$.meta.premiseCheck", "must be an object")
        else:
            if premise.get("status") not in {"confirmed", "corrected", "uncertain"}:
                report.error(
                    "$.meta.premiseCheck.status",
                    "must be confirmed, corrected, or uncertain",
                )
            for key in ("original", "note"):
                if not _text(premise.get(key)):
                    report.error(f"$.meta.premiseCheck.{key}", "must be non-empty")

        scope = meta.get("scope")
        if not isinstance(scope, dict):
            report.error("$.meta.scope", "must be an object")
        else:
            for key in ("included", "excluded"):
                _array(report, f"$.meta.scope.{key}", scope.get(key))
        _array(report, "$.meta.evidenceGaps", meta.get("evidenceGaps"))

    presentation = data.get("presentation")
    if not isinstance(presentation, dict):
        report.error("$.presentation", "must be an object")
    else:
        _required(
            report,
            "$.presentation",
            presentation,
            (
                "preset",
                "source",
                "rationale",
                "archetype",
                "centralInsight",
                "focalRepresentation",
                "hierarchy",
                "sectionRhythm",
            ),
        )
        if presentation.get("preset") not in STYLE_PRESETS:
            report.error("$.presentation.preset", f"must be one of {sorted(STYLE_PRESETS)}")
        if presentation.get("source") not in {"auto", "user", "default"}:
            report.error("$.presentation.source", "must be auto, user, or default")
        if not _text(presentation.get("rationale")):
            report.error("$.presentation.rationale", "must be non-empty")
        if presentation.get("archetype") not in ARCHETYPES:
            report.error(
                "$.presentation.archetype",
                f"must be one of {sorted(ARCHETYPES)}",
            )
        for key in ("centralInsight", "focalRepresentation"):
            value = presentation.get(key)
            if not _text(value):
                report.error(f"$.presentation.{key}", "must be non-empty")
            elif len(value) > 240:
                report.error(f"$.presentation.{key}", "must be <=240 chars")
        for key in ("hierarchy", "sectionRhythm"):
            values = _array(
                report,
                f"$.presentation.{key}",
                presentation.get(key),
                nonempty=True,
            )
            if len(values) < 2 or len(values) > 8:
                report.error(f"$.presentation.{key}", "must contain 2–8 entries")
            if any(not _text(value) for value in values):
                report.error(f"$.presentation.{key}", "entries must be non-empty")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        report.error("$.sources", "must be a non-empty array")
        sources = []
    all_source_ids: set[str] = set()
    for index, source in enumerate(sources):
        path = f"$.sources[{index}]"
        if not isinstance(source, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            source,
            ("id", "title", "publisher", "url", "kind", "publishedAt", "accessedAt", "notes"),
        )
        source_id = source.get("id")
        if not isinstance(source_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]*", source_id
        ):
            report.error(f"{path}.id", "must be lowercase hyphen-case")
        elif source_id in all_source_ids:
            report.error(f"{path}.id", f"duplicate source id '{source_id}'")
        else:
            all_source_ids.add(source_id)
        for key in ("title", "publisher"):
            if not _text(source.get(key)):
                report.error(f"{path}.{key}", "must be non-empty")
        _url(report, f"{path}.url", source.get("url"))
        if source.get("kind") not in SOURCE_KINDS:
            report.error(f"{path}.kind", f"must be one of {sorted(SOURCE_KINDS)}")
        if source.get("publishedAt") is not None:
            _date(report, f"{path}.publishedAt", source.get("publishedAt"))
        _date(report, f"{path}.accessedAt", source.get("accessedAt"))

    chain = data.get("chain")
    main_ids: set[str] = set()
    branch_ids: set[str] = set()
    video_ids: set[str] = set()
    diagram_count = 0
    interaction_count = 0
    lab_count = 0
    previous_lab_kind: str | None = None
    if not isinstance(chain, dict):
        report.error("$.chain", "must be an object")
        chain = {}
    else:
        _required(
            report,
            "$.chain",
            chain,
            (
                "title",
                "openingScenario",
                "openingQuestion",
                "openingVisual",
                "nodes",
                "takeaway",
            ),
        )
        for key in ("title", "openingScenario", "openingQuestion", "takeaway"):
            if not _text(chain.get(key)):
                report.error(f"$.chain.{key}", "must be non-empty")
        if isinstance(chain.get("openingScenario"), str) and len(chain["openingScenario"]) > 180:
            report.error("$.chain.openingScenario", "must be <=180 chars")

    opening_visual = chain.get("openingVisual")
    if not isinstance(opening_visual, dict):
        report.error("$.chain.openingVisual", "must be a visual object")
    else:
        _check_visual(report, "$.chain.openingVisual", opening_visual)
        if opening_visual.get("interaction") is not None:
            interaction_count += 1

    nodes = _array(report, "$.chain.nodes", chain.get("nodes"), nonempty=True)
    if not 3 <= len(nodes) <= 6:
        report.error("$.chain.nodes", "must contain 3–6 main nodes")
    previous_rank = -1
    for index, node in enumerate(nodes):
        path = f"$.chain.nodes[{index}]"
        if not isinstance(node, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            node,
            (
                "id",
                "parentId",
                "type",
                "concept",
                "question",
                "answer",
                "analogy",
                "guide",
                "status",
                "sourceIds",
                "detail",
                "diagram",
                "videoIds",
                "lab",
                "branches",
            ),
        )
        node_id = node.get("id")
        if not isinstance(node_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]*", node_id
        ):
            report.error(f"{path}.id", "must be lowercase hyphen-case")
        elif node_id in main_ids:
            report.error(f"{path}.id", f"duplicate main node id '{node_id}'")
        else:
            main_ids.add(node_id)
        if node.get("parentId") is not None:
            report.error(f"{path}.parentId", "main-chain nodes must use null")
        node_type = node.get("type")
        if node_type not in NODE_RANK:
            report.error(f"{path}.type", f"must be one of {NODE_TYPES}")
        else:
            rank = NODE_RANK[node_type]
            if index == 0 and node_type != "phenomenon":
                report.error(f"{path}.type", "the first main node must be phenomenon")
            if rank < previous_rank:
                report.error(f"{path}.type", "node depth cannot move backward")
            previous_rank = max(previous_rank, rank)
        for key, max_length in (("concept", 16), ("question", 100), ("analogy", 100)):
            if not isinstance(node.get(key), str):
                report.error(f"{path}.{key}", "must be a string")
            elif len(node[key]) > max_length:
                report.error(f"{path}.{key}", f"must be <={max_length} chars")
        if node_type in {"mechanism", "principle", "theory", "frontier"} and not _text(
            node.get("analogy")
        ):
            report.error(
                f"{path}.analogy",
                "must provide one unfamiliar-concept teaching metaphor",
            )
        _short_answer(report, f"{path}.answer", node.get("answer"))
        guide = node.get("guide")
        if not isinstance(guide, dict):
            report.error(f"{path}.guide", "must be an object")
        else:
            _required(
                report,
                f"{path}.guide",
                guide,
                ("bridge", "plainLanguage", "steps", "check"),
            )
            for key, max_length in (("bridge", 240), ("plainLanguage", 400)):
                value = guide.get(key)
                if not _text(value):
                    report.error(f"{path}.guide.{key}", "must be non-empty")
                elif len(value) > max_length:
                    report.error(f"{path}.guide.{key}", f"must be <={max_length} chars")
            steps = _array(
                report,
                f"{path}.guide.steps",
                guide.get("steps"),
                nonempty=True,
            )
            if not 2 <= len(steps) <= 6:
                report.error(f"{path}.guide.steps", "must contain 2–6 steps")
            for step_index, step in enumerate(steps):
                if not _text(step):
                    report.error(
                        f"{path}.guide.steps[{step_index}]",
                        "must be non-empty",
                    )
                elif len(step) > 240:
                    report.error(
                        f"{path}.guide.steps[{step_index}]",
                        "must be <=240 chars",
                    )
            check = guide.get("check")
            if not isinstance(check, dict):
                report.error(f"{path}.guide.check", "must be an object")
            else:
                _required(
                    report,
                    f"{path}.guide.check",
                    check,
                    ("prompt", "answer"),
                )
                for key in ("prompt", "answer"):
                    if not _text(check.get(key)):
                        report.error(f"{path}.guide.check.{key}", "must be non-empty")
        if node.get("status") not in CONTENT_STATUSES:
            report.error(f"{path}.status", f"must be one of {sorted(CONTENT_STATUSES)}")
        _require_sources(report, path, node)

        detail = node.get("detail")
        if not isinstance(detail, dict):
            report.error(f"{path}.detail", "must be an object")
        else:
            _required(
                report,
                f"{path}.detail",
                detail,
                ("deepDive", "whyItMatters", "experimentOrProof", "frontier"),
            )
            for key, max_length in (
                ("deepDive", 800),
                ("whyItMatters", 400),
                ("experimentOrProof", 400),
                ("frontier", 400),
            ):
                value = detail.get(key)
                if not isinstance(value, str):
                    report.error(f"{path}.detail.{key}", "must be a string")
                elif len(value) > max_length:
                    report.error(f"{path}.detail.{key}", f"must be <={max_length} chars")

        diagram = node.get("diagram")
        if diagram is not None:
            diagram_count += 1
            diagram_path = f"{path}.diagram"
            if not isinstance(diagram, dict):
                report.error(diagram_path, "must be an object or null")
            else:
                _required(
                    report,
                    diagram_path,
                    diagram,
                    (
                        "mode",
                        "kind",
                        "svg",
                        "src",
                        "alt",
                        "caption",
                        "formula",
                        "sourceIds",
                        "interaction",
                    ),
                )
                _check_visual(report, diagram_path, diagram)
                if diagram.get("interaction") is not None:
                    interaction_count += 1

        node_video_ids = _array(report, f"{path}.videoIds", node.get("videoIds"))
        for video_id in node_video_ids:
            if not isinstance(video_id, str):
                report.error(f"{path}.videoIds", "entries must be strings")

        manim = node.get("manim")
        if manim is not None:
            if not isinstance(manim, dict):
                report.error(f"{path}.manim", "must be an object or null")
            else:
                _check_manim(report, f"{path}.manim", manim)

        lab = node.get("lab")
        if lab is None:
            if node_type in {"mechanism", "principle"}:
                report.error(
                    f"{path}.lab",
                    "mechanism and principle nodes require a hands-on lab",
                )
        elif not isinstance(lab, dict):
            report.error(f"{path}.lab", "must be an object or null")
        else:
            lab_count += 1
            lab_path = f"{path}.lab"
            _required(
                report,
                lab_path,
                lab,
                (
                    "kind",
                    "title",
                    "goal",
                    "html",
                    "height",
                    "fallbackText",
                    "completionText",
                    "reflectionPrompt",
                ),
            )
            lab_kind = lab.get("kind")
            if lab_kind not in LAB_KINDS:
                report.error(f"{lab_path}.kind", f"must be one of {sorted(LAB_KINDS)}")
            elif previous_lab_kind == lab_kind:
                report.error(
                    f"{lab_path}.kind",
                    "adjacent lab nodes must not repeat the same lab kind",
                )
            if isinstance(lab_kind, str) and lab_kind in LAB_KINDS:
                previous_lab_kind = lab_kind
            for key, max_length in (
                ("title", 80),
                ("goal", 180),
                ("fallbackText", 1000),
                ("completionText", 500),
                ("reflectionPrompt", 240),
            ):
                value = lab.get(key)
                if not _text(value):
                    report.error(f"{lab_path}.{key}", "must be non-empty")
                elif len(value) > max_length:
                    report.error(f"{lab_path}.{key}", f"must be <={max_length} chars")
            height = lab.get("height")
            if (
                not isinstance(height, int)
                or isinstance(height, bool)
                or not 320 <= height <= 720
            ):
                report.error(f"{lab_path}.height", "must be an integer from 320 to 720")
            html = lab.get("html")
            if not _text(html):
                report.error(f"{lab_path}.html", "must be a complete HTML document")
            else:
                lowered = html.lower()
                if not (
                    "<!doctype html" in lowered
                    and "<html" in lowered
                    and "</html>" in lowered
                ):
                    report.error(
                        f"{lab_path}.html",
                        "must be a complete HTML document",
                    )
                for marker in (
                    'id="lab-root"',
                    'id="lab-state"',
                    'id="lab-feedback"',
                    'id="lab-reset"',
                    'name="viewport"',
                    "postMessage",
                ):
                    if marker.lower() not in lowered:
                        report.error(
                            f"{lab_path}.html",
                            f"must include required lab contract marker {marker}",
                        )

        branches = _array(report, f"{path}.branches", node.get("branches"))
        if len(branches) > 3:
            report.error(f"{path}.branches", "at most 3 branches are allowed")
        for branch_index, branch in enumerate(branches):
            branch_path = f"{path}.branches[{branch_index}]"
            if not isinstance(branch, dict):
                report.error(branch_path, "must be an object")
                continue
            _required(
                report,
                branch_path,
                branch,
                ("id", "type", "question", "answer", "sourceIds"),
            )
            branch_id = branch.get("id")
            if not isinstance(branch_id, str) or not re.fullmatch(
                r"[a-z0-9][a-z0-9-]*", branch_id
            ):
                report.error(f"{branch_path}.id", "must be lowercase hyphen-case")
            elif branch_id in branch_ids or branch_id in main_ids:
                report.error(f"{branch_path}.id", f"duplicate node id '{branch_id}'")
            else:
                branch_ids.add(branch_id)
            if branch.get("type") not in NODE_RANK:
                report.error(f"{branch_path}.type", f"must be one of {NODE_TYPES}")
            if not _text(branch.get("question")):
                report.error(f"{branch_path}.question", "must be non-empty")
            _short_answer(report, f"{branch_path}.answer", branch.get("answer"))
            _require_sources(report, branch_path, branch)

    if nodes and diagram_count == 0:
        report.error("$.chain.nodes", "at least one node needs a sourced mechanism diagram")
    if nodes and interaction_count == 0:
        report.error(
            "$.chain",
            "at least one knowledge visual needs a learner interaction",
        )
    if lab_count == 0:
        report.error("$.chain.nodes", "at least one node needs a hands-on lab")

    videos = data.get("videos")
    if not isinstance(videos, dict):
        report.error("$.videos", "must be an object")
        videos = {}
    else:
        _required(report, "$.videos", videos, ("platformsSearched", "items", "gap"))
        platforms = _array(
            report, "$.videos.platformsSearched", videos.get("platformsSearched")
        )
        if set(platforms) != {"youtube", "bilibili"}:
            report.error(
                "$.videos.platformsSearched",
                "must record searches on both youtube and bilibili",
            )
        items = _array(report, "$.videos.items", videos.get("items"))
        if len(items) > 30:
            report.error("$.videos.items", "at most 30 videos are supported across 6 nodes")
        covered_platforms: set[str] = set()
        for index, video in enumerate(items):
            path = f"$.videos.items[{index}]"
            if not isinstance(video, dict):
                report.error(path, "must be an object")
                continue
            _required(
                report,
                path,
                video,
                (
                    "id",
                    "title",
                    "author",
                    "platform",
                    "url",
                "embedUrl",
                    "thumbnailUrl",
                "durationSeconds",
                    "publishedAt",
                    "queryDate",
                    "metricsStatus",
                    "metrics",
                    "selectionRationale",
                    "sourceIds",
                ),
            )
            video_id = video.get("id")
            if not _text(video_id):
                report.error(f"{path}.id", "must be non-empty")
            elif video_id in video_ids:
                report.error(f"{path}.id", f"duplicate video id '{video_id}'")
            else:
                video_ids.add(video_id)
            if video.get("platform") not in {"youtube", "bilibili"}:
                report.error(f"{path}.platform", "must be youtube or bilibili")
            else:
                covered_platforms.add(video["platform"])
            _url(report, f"{path}.url", video.get("url"))
            _url(report, f"{path}.embedUrl", video.get("embedUrl"))
            _url(report, f"{path}.thumbnailUrl", video.get("thumbnailUrl"))
            duration = video.get("durationSeconds")
            if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
                report.error(f"{path}.durationSeconds", "must be a positive integer")
            embed_url = video.get("embedUrl")
            if _text(embed_url):
                parsed_embed = urlparse(embed_url)
                if video.get("platform") == "bilibili":
                    if parsed_embed.netloc != "player.bilibili.com":
                        report.error(
                            f"{path}.embedUrl",
                            "Bilibili videos must use player.bilibili.com",
                        )
                    else:
                        embed_bvid = parse_qs(parsed_embed.query).get("bvid", [None])[0]
                        page_bvid = re.search(r"/video/(BV[0-9A-Za-z]+)", video.get("url", ""))
                        if not embed_bvid or not page_bvid or embed_bvid != page_bvid.group(1):
                            report.error(
                                f"{path}.embedUrl",
                                "Bilibili embed URL must reference the same BVID as url",
                            )
                elif video.get("platform") == "youtube":
                    if parsed_embed.netloc not in {
                        "www.youtube.com",
                        "www.youtube-nocookie.com",
                    } or not parsed_embed.path.startswith("/embed/"):
                        report.error(
                            f"{path}.embedUrl",
                            "YouTube videos must use an /embed/ URL",
                        )
            if video.get("publishedAt") is not None:
                _date(report, f"{path}.publishedAt", video.get("publishedAt"))
            _date(report, f"{path}.queryDate", video.get("queryDate"))
            for key in ("title", "author", "selectionRationale"):
                if not _text(video.get(key)):
                    report.error(f"{path}.{key}", "must be non-empty")
            status = video.get("metricsStatus")
            if status not in {"captured", "partial", "unavailable"}:
                report.error(f"{path}.metricsStatus", "invalid metrics status")
            metrics = video.get("metrics")
            if not isinstance(metrics, dict):
                report.error(f"{path}.metrics", "must be an object")
            else:
                values: list[int | None] = []
                for key in ("views", "likes", "comments"):
                    value = metrics.get(key)
                    if value is not None and (
                        not isinstance(value, int) or isinstance(value, bool) or value < 0
                    ):
                        report.error(
                            f"{path}.metrics.{key}",
                            "must be a non-negative integer or null",
                        )
                    values.append(value)
                if status == "captured" and any(value is None for value in values):
                    report.error(f"{path}.metricsStatus", "captured metrics cannot contain null")
                if status == "unavailable" and any(value is not None for value in values):
                    report.error(f"{path}.metricsStatus", "unavailable metrics must all be null")
            _require_sources(report, path, video)
        if covered_platforms != {"youtube", "bilibili"} and not _text(videos.get("gap")):
            report.error(
                "$.videos.gap",
                "video platforms: gap must explain why one required platform is absent",
            )

    node_video_sets: dict[str, set[str]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_video_ids = node.get("videoIds", [])
        if not isinstance(node_video_ids, list):
            report.error(
                "$.chain.nodes.videoIds",
                f"node '{node.get('id')}' videoIds must be an array",
            )
            continue
        if len(node_video_ids) != 5:
            report.error(
                "$.chain.nodes.videoIds",
                f"node '{node.get('id')}' requires exactly 5 external videos",
            )
        node_video_sets[str(node.get("id"))] = {
            video_id for video_id in node_video_ids if isinstance(video_id, str)
        }
        for video_id in node_video_ids:
            if isinstance(video_id, str) and video_id not in video_ids:
                report.error(
                    "$.chain.nodes.videoIds",
                    f"dangling video id '{video_id}'",
                )
    checked_nodes: list[str] = []
    for node_id, video_set in node_video_sets.items():
        for previous_id in checked_nodes:
            overlap = video_set & node_video_sets[previous_id]
            if overlap:
                report.error(
                    "$.chain.nodes.videoIds",
                    f"nodes '{previous_id}' and '{node_id}' must use different videos; "
                    f"overlap: {', '.join(sorted(overlap))}",
                )
        checked_nodes.append(node_id)

    background = data.get("background")
    if not isinstance(background, dict):
        report.error("$.background", "must be an object")
        background = {}
    else:
        _required(
            report,
            "$.background",
            background,
            (
                "summary",
                "people",
                "institutions",
                "applications",
                "timeline",
                "frontier",
                "gap",
            ),
        )
        if not isinstance(background.get("summary"), str):
            report.error("$.background.summary", "must be a string")
        for key in ("people", "institutions", "applications", "timeline", "frontier"):
            _array(report, f"$.background.{key}", background.get(key))

    for index, person in enumerate(background.get("people", [])):
        path = f"$.background.people[{index}]"
        if not isinstance(person, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            person,
            ("name", "contribution", "context", "limits", "profileUrl", "sourceIds"),
        )
        for key in ("name", "contribution", "context", "limits"):
            if not _text(person.get(key)):
                report.error(f"{path}.{key}", "must be non-empty")
        _url(report, f"{path}.profileUrl", person.get("profileUrl"))
        _require_sources(report, path, person)

    for index, institution in enumerate(background.get("institutions", [])):
        path = f"$.background.institutions[{index}]"
        if not isinstance(institution, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            institution,
            ("name", "role", "homepage", "representativeWork", "sourceIds"),
        )
        for key in ("name", "role", "representativeWork"):
            if not _text(institution.get(key)):
                report.error(f"{path}.{key}", "must be non-empty")
        _url(report, f"{path}.homepage", institution.get("homepage"))
        _require_sources(report, path, institution)

    for index, application in enumerate(background.get("applications", [])):
        path = f"$.background.applications[{index}]"
        if not isinstance(application, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            application,
            ("name", "case", "value", "limitations", "sourceIds"),
        )
        for key in ("name", "case", "value", "limitations"):
            if not _text(application.get(key)):
                report.error(f"{path}.{key}", "must be non-empty")
        _require_sources(report, path, application)

    for index, item in enumerate(background.get("timeline", [])):
        path = f"$.background.timeline[{index}]"
        if not isinstance(item, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            item,
            ("date", "sortDate", "eventType", "title", "description", "impact", "sourceIds"),
        )
        _date(report, f"{path}.sortDate", item.get("sortDate"))
        if item.get("eventType") not in EVENT_TYPES:
            report.error(f"{path}.eventType", f"must be one of {sorted(EVENT_TYPES)}")
        for key in ("date", "title", "description", "impact"):
            if not _text(item.get(key)):
                report.error(f"{path}.{key}", "must be non-empty")
        _require_sources(report, path, item)

    for index, item in enumerate(background.get("frontier", [])):
        path = f"$.background.frontier[{index}]"
        if not isinstance(item, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            item,
            ("title", "publishedAt", "status", "route", "finding", "unresolved", "sourceIds"),
        )
        _date(report, f"{path}.publishedAt", item.get("publishedAt"))
        if item.get("status") not in CLAIM_STATUSES:
            report.error(f"{path}.status", f"must be one of {sorted(CLAIM_STATUSES)}")
        for key in ("title", "route", "finding", "unresolved"):
            if not _text(item.get(key)):
                report.error(f"{path}.{key}", "must be non-empty")
        _require_sources(report, path, item)

    assessment = data.get("assessment")
    if not isinstance(assessment, dict):
        report.error("$.assessment", "must be an object")
        assessment = {}
    else:
        _required(report, "$.assessment", assessment, ("instructions", "items"))
        if not _text(assessment.get("instructions")):
            report.error("$.assessment.instructions", "must be non-empty")
    quiz_ids: set[str] = set()
    quiz_counts = {node_id: 0 for node_id in main_ids}
    quiz_items = _array(report, "$.assessment.items", assessment.get("items"))
    for index, item in enumerate(quiz_items):
        path = f"$.assessment.items[{index}]"
        if not isinstance(item, dict):
            report.error(path, "must be an object")
            continue
        _required(
            report,
            path,
            item,
            (
                "id",
                "nodeId",
                "type",
                "prompt",
                "format",
                "options",
                "correctIndex",
                "modelAnswer",
                "rubric",
                "explanation",
                "sourceIds",
            ),
        )
        quiz_id = item.get("id")
        if not _text(quiz_id):
            report.error(f"{path}.id", "must be non-empty")
        elif quiz_id in quiz_ids:
            report.error(f"{path}.id", f"duplicate quiz id '{quiz_id}'")
        else:
            quiz_ids.add(quiz_id)
        node_id = item.get("nodeId")
        if node_id not in main_ids:
            report.error(f"{path}.nodeId", f"must reference a main node, got '{node_id}'")
        else:
            quiz_counts[node_id] += 1
        if item.get("type") not in QUIZ_TYPES:
            report.error(f"{path}.type", f"must be one of {sorted(QUIZ_TYPES)}")
        if item.get("format") != "choice":
            report.error(f"{path}.format", "must be a single-choice question")
        options = _array(report, f"{path}.options", item.get("options"))
        correct_index = item.get("correctIndex")
        if not 2 <= len(options) <= 4:
            report.error(f"{path}.options", "single-choice questions require 2–4 options")
        if (
            not isinstance(correct_index, int)
            or isinstance(correct_index, bool)
            or correct_index < 0
            or correct_index >= len(options)
        ):
            report.error(f"{path}.correctIndex", "must index an existing option")
        if not _text(item.get("modelAnswer")):
            report.error(f"{path}.modelAnswer", "must be non-empty")
        rubric = _array(report, f"{path}.rubric", item.get("rubric"), nonempty=True)
        if any(not _text(entry) for entry in rubric):
            report.error(f"{path}.rubric", "entries must be non-empty")
        if not _text(item.get("explanation")):
            report.error(f"{path}.explanation", "must be non-empty")
        _require_sources(report, path, item)

    for node_id, count in quiz_counts.items():
        if count != 5:
            report.error(
                f"$.assessment.items[{node_id}]",
                f"each main node requires exactly 5 single-choice questions; found {count}",
            )

    next_questions = _array(
        report, "$.nextQuestions", data.get("nextQuestions"), nonempty=True
    )
    for index, item in enumerate(next_questions):
        path = f"$.nextQuestions[{index}]"
        if not isinstance(item, dict):
            report.error(path, "must be an object")
            continue
        _required(report, path, item, ("question", "why", "sourceIds"))
        for key in ("question", "why"):
            if not _text(item.get(key)):
                report.error(f"{path}.{key}", "must be non-empty")
        _require_sources(report, path, item)

    for path, refs in _source_refs(data):
        if not isinstance(refs, list):
            report.error(path, "must be an array")
            continue
        seen: set[str] = set()
        for index, source_id in enumerate(refs):
            if not isinstance(source_id, str):
                report.error(f"{path}[{index}]", "must be a string")
            elif source_id in seen:
                report.error(f"{path}[{index}]", f"duplicate source id '{source_id}'")
            elif source_id not in all_source_ids:
                report.error(f"{path}[{index}]", f"dangling source id '{source_id}'")
            else:
                seen.add(source_id)

    serialized = json.dumps(data, ensure_ascii=False)
    if PLACEHOLDER_PATTERN.search(serialized):
        report.error("$", "contains an unfinished placeholder marker")

    return report


def load_and_validate(path: Path) -> tuple[dict[str, Any] | None, Report]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report = Report()
        report.error(str(path), "file not found")
        return None, report
    except json.JSONDecodeError as error:
        report = Report()
        report.error(str(path), f"invalid JSON: {error}")
        return None, report
    return data, validate_content(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content", type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()
    _, report = load_and_validate(args.content)
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        for warning in report.warnings:
            print(f"WARNING {warning}")
        for error in report.errors:
            print(f"ERROR   {error}")
        if report.ok:
            print(
                f"Valid: {args.content} "
                f"({len(report.warnings)} warning(s), 0 error(s))"
            )
        else:
            print(f"Invalid: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
