#!/usr/bin/env python3
"""Deck-root trampoline: resolve the markdown-slides skill, then forward.

Copy this file next to the deck Makefile. It uses the stdlib only so the
deck can find the engine before that engine is on PYTHONPATH.
"""

from __future__ import annotations

import configparser
import os
import subprocess
import sys
from pathlib import Path

QUALITY = ("lint", "fmt", "test", "fonts")
FORMATS = ("html", "ppt", "pdf", "serve")
NEEDS_SLIDES = ("ppt", "pdf")
TARGETS = ("help", *QUALITY, *FORMATS)
LOCAL_TARGETS = ("html", "serve")
LOCAL_PY = {
    "html": "build-slides.py",
    "serve": "serve.py",
}
ENGINE = Path("scripts") / "build-slides.py"


def deck_root() -> Path:
    return Path(__file__).resolve().parent


def _parser(root: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    ini = root / "config.ini"
    if ini.is_file():
        parser.read(ini, encoding="utf-8")
    return parser


def resolve_skill(root: Path) -> Path:
    raw = os.environ.get("SKILL", "").strip() or os.environ.get("MARKDOWN_SLIDES_HOME", "").strip()
    parser = _parser(root)
    if not raw:
        raw = parser.get("build", "skill", fallback="").strip()
    if not raw:
        sys.stderr.write("set SKILL= or MARKDOWN_SLIDES_HOME, or [build] skill in config.ini\n")
        sys.exit(1)
    path = Path(raw).expanduser()
    path = path if path.is_absolute() else (root / path)
    path = path.resolve()
    if not path.is_dir() or not (path / ENGINE).is_file():
        sys.stderr.write(f"not a markdown-slides skill (missing {ENGINE}): {raw}\n")
        sys.exit(1)
    return path


def resolve_scripts(root: Path) -> Path | None:
    raw = _parser(root).get("build", "scripts", fallback="").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if path.is_absolute():
        sys.stderr.write("[build] scripts must be relative to the deck root\n")
        sys.exit(1)
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        sys.stderr.write("[build] scripts escapes the deck root\n")
        sys.exit(1)
    if not (resolved / "build-slides.py").is_file():
        sys.stderr.write(f"not a markdown-slides scripts directory: {raw}\n")
        sys.exit(1)
    return resolved


def help_text() -> str:
    return (
        "Targets (run from the deck root):\n"
        "  make <dir>       build HTML for that slides directory\n"
        "                   (example: make slides -> build/slides/)\n"
        "  make ppt <dir>   build PPTX for that directory\n"
        "  make pdf <dir>   export PDF for that directory\n"
        "  make html        HTML for [deck] slides\n"
        "  make serve       serve the project locally\n"
        "  make fmt         format Python in the skill\n"
        "  make lint        ruff + markdownlint (skill, plus this deck's Markdown)\n"
        "  make test        run the skill unit tests\n"
        "  make fonts       vendor Google Fonts into the skill cache\n"
        "  python3 build.py <target> [dir]  same as make\n"
        "Set SKILL or MARKDOWN_SLIDES_HOME, or [build] skill in config.ini.\n"
        "Optional [build] scripts runs local html and serve.\n"
    )


def parse_args(args: list[str]) -> tuple[str, str | None]:
    if not args or args[0] in {"-h", "--help", "help"}:
        return "help", None
    first = args[0]
    rest = args[1:]
    if first in QUALITY:
        return first, None
    if first in FORMATS:
        slides = rest[0] if rest else None
        if first in NEEDS_SLIDES and not slides:
            sys.stderr.write(f"pass a slides directory: make {first} slides\n")
            sys.exit(1)
        return first, slides
    slides = first
    if rest and rest[0] in FORMATS:
        target = rest[0]
        if target in NEEDS_SLIDES or target in {"html", "serve"}:
            return target, slides
    return "html", slides


def run_engine(root: Path, target: str, slides: str | None) -> int:
    env = os.environ.copy()
    env["DECK_ROOT"] = str(root)
    if slides:
        env["SLIDES"] = slides
    else:
        env.pop("SLIDES", None)
    local = resolve_scripts(root)
    if local is not None and target in LOCAL_TARGETS:
        result = subprocess.run(
            ["python3", str(local / LOCAL_PY[target])],
            cwd=str(root),
            env=env,
            check=False,
        )
        return result.returncode
    skill = resolve_skill(root)
    make_args = ["make", "-C", str(skill), target, f"DECK_ROOT={root}"]
    if slides:
        make_args.append(f"SLIDES={slides}")
    result = subprocess.run(make_args, check=False, env=env)
    return result.returncode


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    root = deck_root()
    target, slides = parse_args(args)
    if target == "help":
        sys.stdout.write(help_text())
        return
    raise SystemExit(run_engine(root, target, slides))


if __name__ == "__main__":
    main()
