#!/usr/bin/env python3
"""Render a Manim scene into standalone-HTML video assets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import manim_runtime


DEFAULT_MAX_DURATION_SECONDS = 30.0
DEFAULT_MAX_VIDEO_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_POSTER_BYTES = 1024 * 1024
QUALITY_FLAGS = {"low": "-ql", "medium": "-qm", "high": "-qh"}
SCENE_CLASS_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _fail(message: str) -> None:
    raise RuntimeError(message)


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


def _duration_seconds(ffprobe: Path, video: Path) -> float:
    raw = _capture(
        [
            str(ffprobe),
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
        duration = float(raw)
    except ValueError as error:
        raise RuntimeError(f"ffprobe returned an invalid duration: {raw}") from error
    if duration <= 0:
        raise RuntimeError("rendered video has no positive duration")
    return duration


def _load_transcript(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError(f"transcript not found: {path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid transcript JSON: {path}") from error
    if not isinstance(raw, list):
        raise RuntimeError("transcript must be a JSON array of caption cues")

    transcript: list[dict[str, Any]] = []
    previous_end = 0.0
    for index, cue in enumerate(raw):
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
            raise RuntimeError(
                f"transcript[{index}] needs numeric start/end with end > start"
            )
        if start < previous_end:
            raise RuntimeError(f"transcript[{index}] overlaps the previous cue")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"transcript[{index}].text must be non-empty")
        transcript.append(
            {"start": round(float(start), 2), "end": round(float(end), 2), "text": text.strip()}
        )
        previous_end = float(end)
    return transcript


def _runtime() -> dict[str, Any]:
    runtime = manim_runtime.resolve()
    if not runtime.get("ready"):
        raise RuntimeError(
            "Manim runtime is incomplete. Run "
            "`python3 scripts/manim_runtime.py plan --json`, show the plan, "
            "and obtain explicit user confirmation before installing."
        )
    return runtime


def _has_pillow(python: Path) -> bool:
    if not python.is_file():
        return False
    try:
        result = subprocess.run(
            [str(python), "-c", "from PIL import Image"],
            check=False,
            capture_output=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _pillow_python(manim: Path) -> Path:
    names = ("python.exe", "python", "python3.exe", "python3")
    candidates = [Path(sys.executable), *(manim.parent / name for name in names)]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if _has_pillow(resolved):
            return resolved
    raise RuntimeError(
        "Pillow was not found in the renderer Python or the Manim environment; "
        "it is normally installed as a Manim dependency"
    )


def _extract_webp_poster(
    ffmpeg: Path,
    source_mp4: Path,
    staging: Path,
    manim: Path,
) -> Path:
    poster_png = staging / "poster.png"
    _run(
        [
            str(ffmpeg),
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
    poster_webp = staging / "poster.webp"
    python = _pillow_python(manim)
    _run(
        [
            str(python),
            "-c",
            (
                "import sys; from PIL import Image; "
                "im = Image.open(sys.argv[1]).convert('RGB'); "
                "im.save(sys.argv[2], 'WEBP', quality=86, method=6)"
            ),
            str(poster_png),
            str(poster_webp),
        ]
    )
    if not poster_webp.is_file():
        raise RuntimeError("Pillow did not create the WebP poster")
    return poster_webp


def render(
    scene: Path,
    scene_class: str,
    *,
    output_dir: Path,
    transcript_path: Path | None = None,
    alt: str = "Manim 动画演示",
    caption: str = "动画演示核心因果关系。",
    fallback_svg: str | None = None,
    quality: str = "medium",
    max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS,
    max_video_bytes: int = DEFAULT_MAX_VIDEO_BYTES,
    force: bool = False,
) -> dict[str, Any]:
    scene = scene.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not scene.is_file():
        raise RuntimeError(f"Manim scene not found: {scene}")
    if scene.suffix.lower() != ".py":
        raise RuntimeError("Manim scene must be a .py file")
    if not SCENE_CLASS_PATTERN.fullmatch(scene_class):
        raise RuntimeError("scene class must be a valid Python class identifier")
    if quality not in QUALITY_FLAGS:
        raise RuntimeError(f"quality must be one of {sorted(QUALITY_FLAGS)}")
    if max_duration_seconds <= 0:
        raise RuntimeError("max duration must be positive")
    if max_video_bytes <= 0:
        raise RuntimeError("max video bytes must be positive")
    if not alt.strip() or not caption.strip():
        raise RuntimeError("alt and caption must be non-empty")
    transcript = _load_transcript(transcript_path)

    runtime = _runtime()
    manim = Path(runtime["manim"]["executable"])
    ffmpeg = Path(runtime["ffmpeg"]["executable"])
    ffprobe = Path(runtime["ffprobe"]["executable"])
    slug = re.sub(r"(?<!^)(?=[A-Z])", "-", scene_class).lower()
    video_path = output_dir / f"{slug}.webm"
    poster_path = output_dir / f"{slug}.webp"
    if not force and (video_path.exists() or poster_path.exists()):
        raise RuntimeError(
            f"output already exists in {output_dir}; pass --force to replace it"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="deepwhy-manim-render-") as tmp:
        staging = Path(tmp)
        media_dir = staging / "media"
        _run(
            [
                str(manim),
                "render",
                QUALITY_FLAGS[quality],
                "--format=mp4",
                "--media_dir",
                str(media_dir),
                "--output_file",
                "deepwhy-render",
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
        duration = _duration_seconds(ffprobe, source_mp4)
        if duration > max_duration_seconds:
            raise RuntimeError(
                f"rendered video is {duration:.1f}s; limit is "
                f"{max_duration_seconds:.1f}s"
            )

        staged_video = staging / "animation.webm"
        _run(
            [
                str(ffmpeg),
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
        video_bytes = staged_video.stat().st_size
        if video_bytes > max_video_bytes:
            raise RuntimeError(
                f"WebM is {video_bytes / 1024 / 1024:.1f} MiB; limit is "
                f"{max_video_bytes / 1024 / 1024:.1f} MiB. Shorten or simplify "
                "the scene, or pass a deliberate higher --max-video-mb value."
            )

        staged_poster = _extract_webp_poster(
            ffmpeg, source_mp4, staging, manim
        )
        poster_bytes = staged_poster.stat().st_size
        if poster_bytes > DEFAULT_MAX_POSTER_BYTES:
            raise RuntimeError(
                f"WebP poster is {poster_bytes / 1024 / 1024:.1f} MiB; "
                "the standalone-page limit is 1.0 MiB"
            )
        shutil.copy2(staged_video, video_path)
        shutil.copy2(staged_poster, poster_path)

    fallback = fallback_svg
    if fallback is None:
        fallback = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" '
            'role="img"><rect width="800" height="450" fill="#f7f5ff"/>'
            '<text x="400" y="225" text-anchor="middle" fill="#4f46e5" '
            'font-size="24">动画不可用时，请阅读节点文字说明</text></svg>'
        )
    node = {
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
        "video": str(video_path),
        "poster": str(poster_path),
        "durationSeconds": round(duration, 2),
        "videoBytes": video_path.stat().st_size,
        "posterBytes": poster_path.stat().st_size,
        "node": node,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path, help="Python file containing the Manim Scene")
    parser.add_argument("scene_class", help="Scene class to render")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("manim-assets"),
        help="Directory for the WebM and WebP outputs",
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        help="JSON caption cues: [{start, end, text}, ...]",
    )
    parser.add_argument("--alt", default="Manim 动画演示")
    parser.add_argument("--caption", default="动画演示核心因果关系。")
    parser.add_argument(
        "--fallback-svg",
        type=Path,
        help="SVG shown when video playback is unavailable",
    )
    parser.add_argument("--quality", choices=sorted(QUALITY_FLAGS), default="medium")
    parser.add_argument("--max-duration", type=float, default=DEFAULT_MAX_DURATION_SECONDS)
    parser.add_argument("--max-video-mb", type=float, default=8.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
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
            transcript_path=args.transcript,
            alt=args.alt,
            caption=args.caption,
            fallback_svg=fallback_svg,
            quality=args.quality,
            max_duration_seconds=args.max_duration,
            max_video_bytes=max(1, round(args.max_video_mb * 1024 * 1024)),
            force=args.force,
        )
    except Exception as error:
        result = {"ok": False, "error": str(error)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
