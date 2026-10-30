#!/usr/bin/env python3
"""Render a short Manim scene into inline-ready WebM and WebP assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


QUALITY_FLAGS = {"low": "-ql", "medium": "-qm", "high": "-qh"}
SCENE_CLASS_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CACHE_VERSION = 1


def _executable(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name} is required but was not found on PATH")
    return found


def _run(argv: list[str]) -> None:
    print(f"+ {' '.join(argv)}", file=sys.stderr)
    subprocess.run(argv, check=True)


def _capture(argv: list[str]) -> str:
    result = subprocess.run(
        argv,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout.strip()


def _duration(ffprobe: str, video: Path) -> float:
    raw = _capture(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ]
    )
    try:
        value = float(raw)
    except ValueError as error:
        raise RuntimeError(f"ffprobe returned invalid duration: {raw}") from error
    if value <= 0:
        raise RuntimeError("rendered video has no positive duration")
    return value


def _cache_key(scene: Path, scene_class: str, quality: str) -> str:
    digest = hashlib.sha256()
    digest.update(f"askwhy-manim-v{CACHE_VERSION}\0".encode())
    digest.update(scene_class.encode())
    digest.update(b"\0")
    digest.update(quality.encode())
    digest.update(b"\0")
    with scene.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cache_meta_path(output_dir: Path, slug: str) -> Path:
    return output_dir / f".{slug}.cache.json"


def _read_render_cache(
    *,
    output_dir: Path,
    slug: str,
    cache_key: str,
    max_duration: float,
    max_video_bytes: int,
) -> dict[str, Any] | None:
    video_path = output_dir / f"{slug}.webm"
    poster_path = output_dir / f"{slug}.webp"
    meta_path = _cache_meta_path(output_dir, slug)
    if not video_path.is_file() or not poster_path.is_file() or not meta_path.is_file():
        return None
    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(metadata, dict) or metadata.get("cacheKey") != cache_key:
        return None
    duration = metadata.get("durationSeconds")
    if (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not 0 < duration <= max_duration
    ):
        return None
    if video_path.stat().st_size > max_video_bytes:
        return None
    if poster_path.stat().st_size > 1024 * 1024:
        return None
    return {
        "durationSeconds": round(float(duration), 2),
        "videoBytes": video_path.stat().st_size,
        "posterBytes": poster_path.stat().st_size,
    }


def _load_transcript(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError(f"transcript not found: {path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid transcript JSON: {path}") from error
    if not isinstance(data, list):
        raise RuntimeError("transcript must be a JSON array")
    cues: list[dict[str, Any]] = []
    previous_end = 0.0
    for index, cue in enumerate(data):
        if not isinstance(cue, dict):
            raise RuntimeError(f"transcript[{index}] must be an object")
        start = cue.get("start")
        end = cue.get("end")
        text = cue.get("text")
        if (
            not isinstance(start, (int, float))
            or isinstance(start, bool)
            or not isinstance(end, (int, float))
            or isinstance(end, bool)
            or start < 0
            or end <= start
        ):
            raise RuntimeError(f"transcript[{index}] needs end > start")
        if start < previous_end:
            raise RuntimeError(f"transcript[{index}] overlaps the previous cue")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"transcript[{index}].text must be non-empty")
        cues.append(
            {
                "start": round(float(start), 2),
                "end": round(float(end), 2),
                "text": text.strip(),
            }
        )
        previous_end = float(end)
    return cues


def render(
    scene: Path,
    scene_class: str,
    *,
    output_dir: Path,
    alt: str,
    caption: str,
    transcript_path: Path | None,
    fallback_svg: str | None,
    quality: str,
    max_duration: float,
    max_video_bytes: int,
    force: bool,
) -> dict[str, Any]:
    scene = scene.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not scene.is_file() or scene.suffix.lower() != ".py":
        raise RuntimeError(f"Manim scene must be an existing .py file: {scene}")
    if not SCENE_CLASS_PATTERN.fullmatch(scene_class):
        raise RuntimeError("scene class must be a valid Python class identifier")
    if quality not in QUALITY_FLAGS:
        raise RuntimeError(f"quality must be one of {sorted(QUALITY_FLAGS)}")
    if max_duration <= 0 or max_duration > 30:
        raise RuntimeError("max duration must be from 0 to 30 seconds")
    if max_video_bytes <= 0:
        raise RuntimeError("max video bytes must be positive")
    if not alt.strip() or not caption.strip():
        raise RuntimeError("alt and caption must be non-empty")

    slug = re.sub(r"(?<!^)(?=[A-Z])", "-", scene_class).lower()
    video_path = output_dir / f"{slug}.webm"
    poster_path = output_dir / f"{slug}.webp"
    transcript = _load_transcript(transcript_path)
    fallback = fallback_svg or (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450">'
        '<rect width="800" height="450" fill="#f7f5ff"/>'
        '<text x="400" y="225" text-anchor="middle" fill="#5b42c1" '
        'font-size="24">动画不可用时，请阅读节点文字说明</text></svg>'
    )
    cache_key = _cache_key(scene, scene_class, quality)
    if not force:
        cached = _read_render_cache(
            output_dir=output_dir,
            slug=slug,
            cache_key=cache_key,
            max_duration=max_duration,
            max_video_bytes=max_video_bytes,
        )
        if cached is not None:
            visual = {
                "kind": "manim",
                "sceneSource": str(scene),
                "sceneClass": scene_class,
                "videoSrc": str(video_path),
                "posterSrc": str(poster_path),
                "durationSeconds": cached["durationSeconds"],
                "alt": alt,
                "caption": caption,
                "transcript": transcript,
                "fallbackSvg": fallback,
            }
            return {
                "ok": True,
                "cached": True,
                "visual": visual,
                "videoBytes": cached["videoBytes"],
                "posterBytes": cached["posterBytes"],
            }

    manim = _executable("manim")
    ffmpeg = _executable("ffmpeg")
    ffprobe = _executable("ffprobe")
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="askwhy-manim-") as tmp:
        staging = Path(tmp)
        media_dir = staging / "media"
        _run(
            [
                manim,
                "render",
                QUALITY_FLAGS[quality],
                "--format=mp4",
                "--media_dir",
                str(media_dir),
                "--output_file",
                f"{slug}-render",
                str(scene),
                scene_class,
            ]
        )
        rendered = sorted(
            media_dir.rglob("*.mp4"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if not rendered:
            raise RuntimeError("Manim produced no MP4 output")
        source_mp4 = rendered[0]
        duration = _duration(ffprobe, source_mp4)
        if duration > max_duration:
            raise RuntimeError(
                f"rendered video is {duration:.1f}s; limit is {max_duration:.1f}s"
            )

        staged_video = staging / "animation.webm"
        _run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source_mp4),
                "-an",
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "0",
                "-crf",
                "34",
                "-row-mt",
                "1",
                "-deadline",
                "good",
                "-cpu-used",
                "2",
                str(staged_video),
            ]
        )
        if staged_video.stat().st_size > max_video_bytes:
            raise RuntimeError(
                f"WebM is {staged_video.stat().st_size / 1024 / 1024:.1f} MiB; "
                f"limit is {max_video_bytes / 1024 / 1024:.1f} MiB"
            )

        poster_png = staging / "poster.png"
        _run(
            [
                ffmpeg,
                "-y",
                "-sseof",
                "-0.1",
                "-i",
                str(source_mp4),
                "-frames:v",
                "1",
                "-update",
                "1",
                str(poster_png),
            ]
        )
        try:
            from PIL import Image
        except ImportError as error:
            raise RuntimeError("Pillow is required to create the WebP poster") from error
        staged_poster = staging / "poster.webp"
        image = Image.open(poster_png).convert("RGB")
        image.save(staged_poster, "WEBP", quality=86, method=6)
        if staged_poster.stat().st_size > 1024 * 1024:
            raise RuntimeError("WebP poster exceeds the 1 MiB limit")
        shutil.copy2(staged_video, video_path)
        shutil.copy2(staged_poster, poster_path)

    _cache_meta_path(output_dir, slug).write_text(
        json.dumps(
            {
                "cacheVersion": CACHE_VERSION,
                "cacheKey": cache_key,
                "sceneClass": scene_class,
                "quality": quality,
                "durationSeconds": round(duration, 2),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    visual = {
        "kind": "manim",
        "sceneSource": str(scene),
        "sceneClass": scene_class,
        "videoSrc": str(video_path),
        "posterSrc": str(poster_path),
        "durationSeconds": round(duration, 2),
        "alt": alt,
        "caption": caption,
        "transcript": transcript,
        "fallbackSvg": fallback,
    }
    return {
        "ok": True,
        "cached": False,
        "visual": visual,
        "videoBytes": video_path.stat().st_size,
        "posterBytes": poster_path.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("scene_class")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--alt", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--fallback-svg", type=Path)
    parser.add_argument("--quality", choices=sorted(QUALITY_FLAGS), default="medium")
    parser.add_argument("--max-duration", type=float, default=15.0)
    parser.add_argument("--max-video-mb", type=float, default=4.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        fallback_svg = (
            args.fallback_svg.read_text(encoding="utf-8")
            if args.fallback_svg
            else None
        )
        result = render(
            args.scene,
            args.scene_class,
            output_dir=args.output_dir,
            alt=args.alt,
            caption=args.caption,
            transcript_path=args.transcript,
            fallback_svg=fallback_svg,
            quality=args.quality,
            max_duration=args.max_duration,
            max_video_bytes=max(1, round(args.max_video_mb * 1024 * 1024)),
            force=args.force,
        )
    except Exception as error:
        print(
            json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2)
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
