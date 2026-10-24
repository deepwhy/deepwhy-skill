#!/usr/bin/env python3
"""Build a standalone knowledge-chain page from DeepWhy v2 content."""

from __future__ import annotations

import argparse
import base64
import copy
import html
import json
import re
import sys
from pathlib import Path

from validate_content import STYLE_PRESETS, load_and_validate, validate_content


DATA_TOKEN = "__DEEPWHY_DATA__"
TITLE_TOKEN = "__DEEPWHY_TITLE__"
STYLE_TOKEN = "__DEEPWHY_STYLE__"
MAX_MANIM_VIDEO_BYTES = 8 * 1024 * 1024
MAX_MANIM_POSTER_BYTES = 1024 * 1024


def safe_json_for_script(data: dict) -> str:
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r"</", r"<\\/", serialized, flags=re.IGNORECASE)


def resolve_style(content: dict, cli_value: str | None) -> str:
    import os

    requested = cli_value or os.environ.get("DEEPWHY_PAGE_STYLE")
    if requested and requested != "auto":
        if requested not in STYLE_PRESETS:
            raise ValueError(
                f"unknown style '{requested}'; choose from {', '.join(sorted(STYLE_PRESETS))}"
            )
        original_rationale = content["presentation"].get("rationale", "").strip()
        content["presentation"]["preset"] = requested
        content["presentation"]["source"] = "user"
        content["presentation"]["rationale"] = (
            f"用户指定视觉预设 {requested}；原自动建议：{original_rationale}"
            if original_rationale
            else f"用户指定视觉预设 {requested}。"
        )
    return content["presentation"]["preset"]


def _data_uri(path: Path, mime: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inline_manim_assets(content: dict, base_dir: Path) -> tuple[dict, int]:
    embedded = copy.deepcopy(content)
    count = 0
    for index, node in enumerate(embedded["chain"]["nodes"]):
        manim = node.get("manim")
        if not manim:
            continue
        node_path = f"$.chain.nodes[{index}].manim"
        scene_path = Path(manim["sceneSource"]).expanduser()
        if not scene_path.is_absolute():
            scene_path = base_dir / scene_path
        if not scene_path.is_file():
            raise ValueError(f"{node_path}.sceneSource: file not found: {scene_path}")

        for key, suffix, mime, max_bytes in (
            ("videoSrc", ".webm", "video/webm", MAX_MANIM_VIDEO_BYTES),
            ("posterSrc", ".webp", "image/webp", MAX_MANIM_POSTER_BYTES),
        ):
            media_path = Path(manim[key]).expanduser()
            if not media_path.is_absolute():
                media_path = base_dir / media_path
            if not media_path.is_file():
                raise ValueError(f"{node_path}.{key}: file not found: {media_path}")
            if media_path.suffix.lower() != suffix:
                raise ValueError(f"{node_path}.{key}: must be a {suffix} file")
            size = media_path.stat().st_size
            if size > max_bytes:
                raise ValueError(
                    f"{node_path}.{key}: {size / 1024 / 1024:.1f} MiB exceeds "
                    f"the {max_bytes / 1024 / 1024:.1f} MiB standalone-page limit"
                )
            manim[key] = _data_uri(media_path, mime)
        count += 1
    return embedded, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content", type=Path, help="Knowledge-chain JSON")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output HTML path (default: <slug>.html)",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "template.html",
    )
    parser.add_argument(
        "--style",
        choices=[*sorted(STYLE_PRESETS), "auto"],
        help="Override visual preset; DEEPWHY_PAGE_STYLE is also supported",
    )
    parser.add_argument(
        "--data-out",
        type=Path,
        help="Write the final resolved JSON next to the HTML",
    )
    args = parser.parse_args()

    content, report = load_and_validate(args.content)
    if content is None or not report.ok:
        for warning in report.warnings:
            print(f"WARNING {warning}", file=sys.stderr)
        for error in report.errors:
            print(f"ERROR   {error}", file=sys.stderr)
        print("Build aborted because the content is invalid.", file=sys.stderr)
        return 1

    try:
        style = resolve_style(content, args.style)
    except ValueError as error:
        print(f"ERROR   {error}", file=sys.stderr)
        return 1
    report = validate_content(content)
    if not report.ok:
        for error in report.errors:
            print(f"ERROR   {error}", file=sys.stderr)
        print("Build aborted because the resolved content is invalid.", file=sys.stderr)
        return 1

    base_dir = args.content.resolve().parent
    try:
        embedded_content, manim_count = inline_manim_assets(content, base_dir)
    except (OSError, ValueError) as error:
        print(f"ERROR   {error}", file=sys.stderr)
        return 1

    try:
        template = args.template.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR   Template not found: {args.template}", file=sys.stderr)
        return 1

    for token in (DATA_TOKEN, TITLE_TOKEN, STYLE_TOKEN):
        if token not in template:
            print(f"ERROR   Template is missing token {token}.", file=sys.stderr)
            return 1

    title = f"{content['meta']['topic']} · DeepWhy"
    output = template.replace(DATA_TOKEN, safe_json_for_script(embedded_content))
    output = output.replace(TITLE_TOKEN, html.escape(title, quote=True))
    output = output.replace(STYLE_TOKEN, style)

    leftovers = sorted(set(re.findall(r"__DEEPWHY_[A-Z_]+__", output)))
    if leftovers:
        print(f"ERROR   Unreplaced token(s): {', '.join(leftovers)}", file=sys.stderr)
        return 1

    output_path = args.output or Path.cwd() / f"{content['meta']['slug']}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")

    if args.data_out:
        args.data_out.parent.mkdir(parents=True, exist_ok=True)
        args.data_out.write_text(
            json.dumps(content, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    for warning in report.warnings:
        print(f"WARNING {warning}")
    print(f"Built {output_path.resolve()}")
    print(f"Visual preset: {style}")
    print(f"Inlined Manim scenes: {manim_count}")
    if args.data_out:
        print(f"Content JSON: {args.data_out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
