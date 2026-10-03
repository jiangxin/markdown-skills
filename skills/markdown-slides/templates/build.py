#!/usr/bin/env python3
"""Deck-root trampoline: resolve the markdown-slides skill, then forward.

Copy this file next to the deck Makefile. It uses the stdlib only so the
deck can find the engine before that engine is on PYTHONPATH.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

QUALITY = ("lint", "fmt", "test", "fonts")
FORMATS = ("html", "ppt", "pdf", "serve")
NEEDS_SLIDES = ("ppt", "pdf")
LOCAL_TARGETS = ("html", "serve")
LOCAL_PY = {
    "html": "build-slides.py",
    "serve": "serve.py",
}
ENGINE = Path("scripts") / "build-slides.py"


def deck_root() -> Path:
    return Path(__file__).resolve().parent


def _is_engine(path: Path) -> bool:
    return (path / ENGINE).is_file() and (path / "templates").is_dir()


def resolve_skill(root: Path) -> Path:
    raw = os.environ.get("SKILL", "").strip() or os.environ.get("MARKDOWN_SLIDES_HOME", "").strip()
    if raw:
        path = Path(raw).expanduser()
        path = path if path.is_absolute() else (root / path)
        path = path.resolve()
        if not path.is_dir() or not (path / ENGINE).is_file():
            sys.stderr.write(f"not a markdown-slides skill (missing {ENGINE}): {raw}\n")
            sys.exit(1)
        return path
    if _is_engine(root):
        return root
    skills = root / "skills"
    found: list[Path] = []
    if skills.is_dir():
        for child in sorted(skills.iterdir()):
            if _is_engine(child):
                found.append(child.resolve())
    named = [path for path in found if path.name == "markdown-slides"]
    if named:
        return named[0]
    if len(found) == 1:
        return found[0]
    sys.stderr.write("set SKILL= or MARKDOWN_SLIDES_HOME, or put the skill under skills/\n")
    sys.exit(1)


def resolve_scripts(root: Path) -> Path | None:
    if _is_engine(root):
        return None
    marker = root / "scripts" / "build-slides.py"
    if not marker.is_file():
        return None
    return marker.parent.resolve()


def help_text() -> str:
    return (
        "Targets (run from the deck root):\n"
        "  make <dir>       build HTML for that slides directory\n"
        "                   (example: make slides -> build/slides/)\n"
        "  make html <dir>  build HTML for that directory\n"
        "  make ppt <dir>   build PPTX for that directory\n"
        "  make pdf <dir>   export PDF for that directory\n"
        "  make serve       serve build/ locally\n"
        "  make fmt         format Python in the skill\n"
        "  make lint        ruff + markdownlint (skill, plus this deck's Markdown)\n"
        "  make test        run the skill unit tests\n"
        "  make fonts       vendor Google Fonts into the skill cache\n"
        "  python3 build.py <target> [dir]  same as make\n"
        "Set SKILL or MARKDOWN_SLIDES_HOME, or nest the skill under skills/.\n"
        "A deck-local scripts/ copy runs html and serve when present.\n"
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
        return rest[0], slides
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
