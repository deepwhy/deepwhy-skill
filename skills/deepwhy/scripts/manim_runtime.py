#!/usr/bin/env python3
"""Probe, plan, install, and resolve the DeepWhy Manim runtime."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


MANIM_VERSION = "0.20.1"


def _command_version(executable: str, args: tuple[str, ...] = ("--version",)) -> str | None:
    try:
        result = subprocess.run(
            [executable, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (result.stdout or result.stderr or "").strip().splitlines()
    return output[0].strip() if result.returncode == 0 and output else None


def _platform_info() -> dict[str, str]:
    system = platform.system()
    release = platform.release()
    machine = platform.machine()
    if system == "Linux" and "microsoft" in release.lower():
        system = "WSL"
    return {"system": system, "release": release, "machine": machine}


def install_root() -> Path:
    override = os.environ.get("DEEPWHY_MANIM_RUNTIME")
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system()
    if system == "Darwin":
        return (
            Path.home()
            / "Library"
            / "Caches"
            / "deepwhy"
            / "manim-runtime"
        )
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
        return root / "DeepWhy" / "manim-runtime"
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg_cache).expanduser() if xdg_cache else Path.home() / ".cache"
    return base / "deepwhy" / "manim-runtime"


def _venv_bin(name: str) -> str:
    if platform.system() == "Windows":
        return f"{name}.exe"
    return name


def venv_python(root: Path) -> Path:
    if platform.system() == "Windows":
        return root / "venv" / "Scripts" / "python.exe"
    return root / "venv" / "bin" / "python"


def venv_manim(root: Path) -> Path:
    if platform.system() == "Windows":
        return root / "venv" / "Scripts" / "manim.exe"
    return root / "venv" / "bin" / "manim"


def manifest_path(root: Path | None = None) -> Path:
    return (root or install_root()) / "runtime.json"


def _probe_binary(name: str, args: tuple[str, ...] = ("--version",)) -> dict[str, Any]:
    executable = shutil.which(name)
    return {
        "available": bool(executable and _command_version(executable, args)),
        "executable": executable,
        "version": _command_version(executable, args) if executable else None,
    }


def _probe_manim(root: Path) -> dict[str, Any]:
    cached = venv_manim(root)
    if cached.exists():
        version = _command_version(str(cached))
        if version:
            return {
                "available": True,
                "source": "deepwhy-cache",
                "executable": str(cached),
                "version": version,
            }
    system = _probe_binary("manim")
    system["source"] = "system" if system["available"] else None
    return system


def _probe_latex() -> dict[str, Any]:
    for name in ("latex", "pdflatex"):
        executable = shutil.which(name)
        if not executable:
            continue
        version = _command_version(executable, ("--version",))
        if version:
            return {
                "available": True,
                "executable": executable,
                "version": version,
            }
    return {"available": False, "executable": None, "version": None}


def _probe_cairo_pango(system: str) -> dict[str, Any]:
    if system == "Windows":
        # The Python wheels used by a successful Manim import provide the
        # runtime libraries on supported Windows builds.
        return {"available": None, "detail": "checked during Manim smoke test"}
    pkg_config = shutil.which("pkg-config")
    if pkg_config:
        try:
            result = subprocess.run(
                [pkg_config, "--exists", "cairo", "pango"],
                check=False,
                capture_output=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result and result.returncode == 0:
            return {"available": True, "detail": "pkg-config cairo pango"}
    if system == "Darwin" and shutil.which("brew"):
        try:
            result = subprocess.run(
                ["brew", "list", "--versions", "cairo", "pango"],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None
        detail = (result.stdout or "").strip() if result else ""
        if result and result.returncode == 0 and "cairo" in detail and "pango" in detail:
            return {"available": True, "detail": detail}
    return {"available": False, "detail": "cairo/pango not detected"}


def probe() -> dict[str, Any]:
    root = install_root()
    info = _platform_info()
    dependencies = {
        "manim": _probe_manim(root),
        "ffmpeg": _probe_binary("ffmpeg", ("-version",)),
        "ffprobe": _probe_binary("ffprobe", ("-version",)),
        "latex": _probe_latex(),
        "cairo_pango": _probe_cairo_pango(info["system"]),
    }
    ready = all(
        dependency["available"] is not False
        for dependency in dependencies.values()
    )
    return {
        "ready": ready,
        "platform": info,
        "installRoot": str(root),
        "manifest": str(manifest_path(root)),
        "installedManifest": manifest_path(root).exists(),
        "dependencies": dependencies,
    }


def _system_commands(system: str, missing: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    commands: list[dict[str, Any]] = []
    notes: list[str] = []
    packages: list[str] = []

    if system == "Darwin":
        if not shutil.which("brew"):
            return [], ["Homebrew is required for automatic installation on macOS."]
        if "ffmpeg" in missing or "ffprobe" in missing:
            packages.append("ffmpeg")
        if "cairo_pango" in missing:
            packages.extend(["cairo", "pango"])
        if packages:
            commands.append(
                {
                    "label": "Install video and graphics libraries",
                    "argv": ["brew", "install", *dict.fromkeys(packages)],
                    "requiresElevation": False,
                }
            )
        if "latex" in missing:
            commands.append(
                {
                    "label": "Install a LaTeX distribution",
                    "argv": ["brew", "install", "--cask", "mactex-no-gui"],
                    "requiresElevation": False,
                }
            )
    elif system in {"Linux", "WSL"}:
        if shutil.which("apt-get"):
            packages = ["ffmpeg"]
            if "cairo_pango" in missing:
                packages.extend(["libcairo2-dev", "libpango1.0-dev"])
            if "latex" in missing:
                packages.extend(
                    [
                        "texlive-latex-extra",
                        "texlive-fonts-recommended",
                        "texlive-science",
                        "latexmk",
                    ]
                )
            commands.extend(
                [
                    {
                        "label": "Refresh apt package index",
                        "argv": ["sudo", "apt-get", "update"],
                        "requiresElevation": True,
                    },
                    {
                        "label": "Install Manim system dependencies",
                        "argv": ["sudo", "apt-get", "install", "-y", *packages],
                        "requiresElevation": True,
                    },
                ]
            )
        elif shutil.which("dnf"):
            packages = ["ffmpeg"]
            if "cairo_pango" in missing:
                packages.extend(["cairo-devel", "pango-devel"])
            if "latex" in missing:
                packages.extend(["texlive-scheme-medium", "latexmk"])
            commands.append(
                {
                    "label": "Install Manim system dependencies",
                    "argv": ["sudo", "dnf", "install", "-y", *packages],
                    "requiresElevation": True,
                }
            )
        elif shutil.which("pacman"):
            packages = ["ffmpeg"]
            if "cairo_pango" in missing:
                packages.extend(["cairo", "pango"])
            if "latex" in missing:
                packages.extend(["texlive-latexextra", "latexmk"])
            commands.append(
                {
                    "label": "Install Manim system dependencies",
                    "argv": ["sudo", "pacman", "-S", "--needed", *packages],
                    "requiresElevation": True,
                }
            )
        else:
            notes.append("No supported Linux package manager was found.")
    elif system == "Windows":
        if shutil.which("winget"):
            if "ffmpeg" in missing or "ffprobe" in missing:
                commands.append(
                    {
                        "label": "Install FFmpeg",
                        "argv": ["winget", "install", "--id", "Gyan.FFmpeg", "-e"],
                        "requiresElevation": False,
                    }
                )
            if "latex" in missing:
                commands.append(
                    {
                        "label": "Install MiKTeX",
                        "argv": ["winget", "install", "--id", "MiKTeX.MiKTeX", "-e"],
                        "requiresElevation": False,
                    }
                )
        elif shutil.which("choco"):
            packages = []
            if "ffmpeg" in missing or "ffprobe" in missing:
                packages.append("ffmpeg")
            if "latex" in missing:
                packages.append("miktex")
            if packages:
                commands.append(
                    {
                        "label": "Install Manim system dependencies",
                        "argv": ["choco", "install", *packages, "-y"],
                        "requiresElevation": True,
                    }
                )
        else:
            notes.append("winget or Chocolatey is required for automatic Windows setup.")
        notes.append(
            "Cairo/Pango support is verified by the final Manim smoke test on Windows."
        )
    else:
        notes.append(f"Automatic installation is not implemented for {system}.")
    return commands, notes


def _python_commands(root: Path) -> list[dict[str, Any]]:
    python_path = venv_python(root)
    if python_path.exists():
        return [
            {
                "label": f"Install Manim {MANIM_VERSION} into the DeepWhy cache",
                "argv": [
                    str(python_path),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    f"manim=={MANIM_VERSION}",
                ],
                "requiresElevation": False,
            }
        ]
    if shutil.which("uv"):
        return [
            {
                "label": "Create an isolated DeepWhy Python environment",
                "argv": ["uv", "venv", "--python", "3.12", str(root / "venv")],
                "requiresElevation": False,
            },
            {
                "label": f"Install Manim {MANIM_VERSION} into the DeepWhy cache",
                "argv": [
                    "uv",
                    "pip",
                    "install",
                    "--python",
                    str(python_path),
                    f"manim=={MANIM_VERSION}",
                ],
                "requiresElevation": False,
            },
        ]
    return [
        {
            "label": "Create an isolated DeepWhy Python environment",
            "argv": [sys.executable, "-m", "venv", str(root / "venv")],
            "requiresElevation": False,
        },
        {
            "label": f"Install Manim {MANIM_VERSION} into the DeepWhy cache",
            "argv": [
                str(python_path),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                f"manim=={MANIM_VERSION}",
            ],
            "requiresElevation": False,
        },
    ]


def plan() -> dict[str, Any]:
    current = probe()
    root = install_root()
    dependencies = current["dependencies"]
    missing = {
        name
        for name, value in dependencies.items()
        if value["available"] is False
    }
    system_commands, notes = _system_commands(
        current["platform"]["system"], missing
    )
    python_commands = _python_commands(root)
    commands = [*system_commands, *python_commands]
    return {
        "platform": current["platform"],
        "installRoot": str(root),
        "missing": sorted(missing),
        "commands": commands,
        "notes": notes,
        "requiresConfirmation": not current["ready"] or not venv_manim(root).exists(),
        "confirmationPrompt": (
            "Manim is not fully available. The DeepWhy Skill can install an "
            "isolated runtime and required system dependencies. Continue?"
        ),
    }


def _run(argv: list[str]) -> None:
    print(f"+ {' '.join(argv)}", file=sys.stderr)
    subprocess.run(argv, check=True)


def _smoke_test(root: Path) -> None:
    manim = venv_manim(root)
    if not manim.exists():
        raise RuntimeError(f"Manim executable was not created: {manim}")
    with tempfile.TemporaryDirectory(prefix="deepwhy-manim-smoke-") as tmp:
        directory = Path(tmp)
        scene = directory / "smoke_scene.py"
        scene.write_text(
            "from manim import Scene, Circle, BLUE\n"
            "class DeepWhySmoke(Scene):\n"
            "    def construct(self):\n"
            "        self.add(Circle(color=BLUE))\n",
            encoding="utf-8",
        )
        _run(
            [
                str(manim),
                "render",
                "-ql",
                "--format=mp4",
                "--media_dir",
                str(directory / "media"),
                str(scene),
                "DeepWhySmoke",
            ]
        )
        if not list((directory / "media").rglob("*.mp4")):
            raise RuntimeError("Manim smoke test produced no video")


def resolve() -> dict[str, Any]:
    current = probe()
    manim = current["dependencies"]["manim"]
    if not current["ready"] or not manim["available"]:
        return {
            "ready": False,
            "reason": "Manim runtime is incomplete",
            "probe": current,
        }
    return {
        "ready": True,
        "manim": manim,
        "ffmpeg": current["dependencies"]["ffmpeg"],
        "ffprobe": current["dependencies"]["ffprobe"],
        "latex": current["dependencies"]["latex"],
        "installRoot": current["installRoot"],
    }


def install(confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise PermissionError(
            "Manim installation requires --confirmed after explicit user consent."
        )
    installation = plan()
    root = install_root()
    root.mkdir(parents=True, exist_ok=True)
    for command in installation["commands"]:
        _run(command["argv"])
    _smoke_test(root)
    current = probe()
    if not current["ready"]:
        raise RuntimeError("Manim runtime still has missing dependencies after install")
    manifest = {
        "schemaVersion": "1.0",
        "installedAt": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "manimVersion": MANIM_VERSION,
        "installRoot": str(root),
        "dependencies": current["dependencies"],
    }
    manifest_path(root).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"ok": True, "manifest": str(manifest_path(root)), "probe": current}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("probe", "plan", "resolve"):
        child = subparsers.add_parser(name)
        child.add_argument("--json", action="store_true")
    installer = subparsers.add_parser("install")
    installer.add_argument("--confirmed", action="store_true")
    installer.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        if args.command == "probe":
            result = probe()
        elif args.command == "plan":
            result = plan()
        elif args.command == "resolve":
            result = resolve()
        else:
            result = install(args.confirmed)
    except Exception as error:
        result = {"ok": False, "error": str(error)}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
