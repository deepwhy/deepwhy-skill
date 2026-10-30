#!/usr/bin/env python3
"""Build one portable AskWhy HTML page from validated content."""

from __future__ import annotations

import argparse
import base64
import copy
import html
import json
import re
import sys
from pathlib import Path

from validate_content import load_content


DATA_TOKEN = "__ASKWHY_DATA__"
TITLE_TOKEN = "__ASKWHY_TITLE__"
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_VIDEO_BYTES = 4 * 1024 * 1024
MAX_POSTER_BYTES = 1024 * 1024
MAX_TOTAL_VIDEO_BYTES = 20 * 1024 * 1024
MEDIA_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".webm": "video/webm",
}


def safe_json_for_script(data: dict) -> str:
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r"</", r"<\\/", serialized, flags=re.IGNORECASE)


def _data_file(path: Path, max_bytes: int, label: str) -> tuple[str, int]:
    if not path.is_file():
        raise ValueError(f"{label}: file not found: {path}")
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(
            f"{label}: {size / 1024 / 1024:.1f} MiB exceeds "
            f"{max_bytes / 1024 / 1024:.1f} MiB"
        )
    media_type = MEDIA_TYPES.get(path.suffix.lower())
    if media_type is None:
        raise ValueError(f"{label}: unsupported media type {path.suffix}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}", size


def _inline_visual(
    visual: dict,
    path: str,
    base_dir: Path,
    total_video_bytes: int,
) -> tuple[int, int]:
    if visual["kind"] == "image":
        source = visual["src"]
        if not source.startswith("data:"):
            asset = Path(source).expanduser()
            if not asset.is_absolute():
                asset = base_dir / asset
            visual["src"], _ = _data_file(
                asset,
                MAX_IMAGE_BYTES,
                f"{path}.src",
            )
    else:
        scene_source = Path(visual["sceneSource"]).expanduser()
        if not scene_source.is_absolute():
            scene_source = base_dir / scene_source
        if not scene_source.is_file():
            raise ValueError(f"{path}.sceneSource: file not found: {scene_source}")
        for key, suffix, max_bytes, count_video in (
            ("videoSrc", ".webm", MAX_VIDEO_BYTES, True),
            ("posterSrc", ".webp", MAX_POSTER_BYTES, False),
        ):
            source = visual[key]
            if source.startswith("data:"):
                continue
            asset = Path(source).expanduser()
            if not asset.is_absolute():
                asset = base_dir / asset
            if asset.suffix.lower() != suffix:
                raise ValueError(f"{path}.{key}: must be a {suffix} file")
            visual[key], size = _data_file(asset, max_bytes, f"{path}.{key}")
            if count_video:
                total_video_bytes += size
        if total_video_bytes > MAX_TOTAL_VIDEO_BYTES:
            raise ValueError(
                "combined Manim videos exceed the "
                f"{MAX_TOTAL_VIDEO_BYTES / 1024 / 1024:.0f} MiB page budget"
            )
    return 1, total_video_bytes


def inline_visuals(content: dict, base_dir: Path) -> tuple[dict, int, int]:
    embedded = copy.deepcopy(content)
    visual_count = 0
    total_video_bytes = 0

    overview_visual = embedded.get("center", {}).get("overviewVisual")
    if overview_visual:
        count, total_video_bytes = _inline_visual(
            overview_visual,
            "$.center.overviewVisual",
            base_dir,
            total_video_bytes,
        )
        visual_count += count

    center_analogy_visual = (
        embedded.get("center", {}).get("analogy", {}).get("visual")
    )
    if center_analogy_visual:
        count, total_video_bytes = _inline_visual(
            center_analogy_visual,
            "$.center.analogy.visual",
            base_dir,
            total_video_bytes,
        )
        visual_count += count

    for index, node in enumerate(embedded.get("nodes", [])):
        visual = node.get("visual")
        if visual:
            count, total_video_bytes = _inline_visual(
                visual,
                f"$.nodes[{index}].visual",
                base_dir,
                total_video_bytes,
            )
            visual_count += count

        analogy_visual = node.get("analogy", {}).get("visual")
        if analogy_visual:
            count, total_video_bytes = _inline_visual(
                analogy_visual,
                f"$.nodes[{index}].analogy.visual",
                base_dir,
                total_video_bytes,
            )
            visual_count += count
    return embedded, visual_count, total_video_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content", type=Path, help="AskWhy content JSON")
    parser.add_argument("--output", type=Path, help="Output HTML path")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "template.html",
    )
    parser.add_argument("--data-out", type=Path, help="Copy the validated JSON here")
    args = parser.parse_args()

    content, report = load_content(args.content)
    if content is None or not report.ok:
        for warning in report.warnings:
            print(f"WARNING {warning}", file=sys.stderr)
        for error in report.errors:
            print(f"ERROR   {error}", file=sys.stderr)
        print("Build aborted because the content is invalid.", file=sys.stderr)
        return 1

    try:
        template = args.template.read_text(encoding="utf-8")
    except OSError as error:
        print(f"ERROR   Could not read template {args.template}: {error}", file=sys.stderr)
        return 1

    for token in (DATA_TOKEN, TITLE_TOKEN):
        if token not in template:
            print(f"ERROR   Template is missing token {token}.", file=sys.stderr)
            return 1

    try:
        embedded_content, visual_count, total_video_bytes = inline_visuals(
            content,
            args.content.resolve().parent,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR   {error}", file=sys.stderr)
        return 1

    title = f"{content['meta']['topic']} · AskWhy"
    output = template.replace(DATA_TOKEN, safe_json_for_script(embedded_content))
    output = output.replace(TITLE_TOKEN, html.escape(title, quote=True))

    leftovers = sorted(set(re.findall(r"__ASKWHY_[A-Z_]+__", output)))
    if leftovers:
        print(f"ERROR   Unreplaced token(s): {', '.join(leftovers)}", file=sys.stderr)
        return 1

    output_path = args.output or (Path.cwd() / f"{content['meta']['slug']}.html")
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
    print(f"Causal chain: {len(content['nodes'])} layers")
    print(f"Embedded visuals: {visual_count}")
    if total_video_bytes:
        print(f"Embedded Manim video: {total_video_bytes / 1024 / 1024:.1f} MiB")
    if args.data_out:
        print(f"Content JSON: {args.data_out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
