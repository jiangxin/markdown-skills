#!/usr/bin/env python3
"""Deck-root trampoline: resolve slides or pages skill, then forward.

Copy this file next to the deck Makefile. It uses the stdlib only so the
deck can find the engine before that engine is on PYTHONPATH.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

QUALITY = ("lint", "fmt", "test", "fonts")
FORMATS = ("html", "ppt", "pdf", "serve")
NEEDS_SLIDES = ("ppt", "pdf")
SCAN_SKIP = {
    ".cache",
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "node_modules",
    "scripts",
    "skills",
    "templates",
    "tests",
    "themes",
}
SLIDES_MARKER = Path("scripts") / "build-slides.py"
PAGES_MARKER = Path("scripts") / "build-pages.py"
LOCAL_SLIDES = Path("scripts") / "markdown-slides" / "build-slides.py"
LOCAL_PAGES = Path("scripts") / "markdown-pages" / "build-pages.py"
LOCAL_PY = {
    "slides": {"html": "build-slides.py", "serve": "serve.py"},
    "pages": {"html": "build-pages.py"},
}
LOCAL_TARGETS = {
    "slides": ("html", "serve"),
    "pages": ("html",),
}


def deck_root() -> Path:
    return Path(__file__).resolve().parent


def _is_engine(path: Path, kind: str) -> bool:
    marker = PAGES_MARKER if kind == "pages" else SLIDES_MARKER
    return (path / marker).is_file() and (path / "templates").is_dir()


def _kind_type(directory: Path) -> str:
    meta = directory / "meta.toml"
    if not meta.is_file():
        return ""
    try:
        data = tomllib.loads(meta.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        sys.stderr.write(f"{directory.name}/meta.toml: {exc}\n")
        sys.exit(1)
    if not isinstance(data, dict):
        return ""
    value = data.get("type", "")
    return value.strip() if isinstance(value, str) else ""


def _scan_kinds(root: Path) -> set[str]:
    found: set[str] = set()
    try:
        children = root.iterdir()
    except OSError:
        return found
    for child in children:
        if not child.is_dir() or child.name.startswith(".") or child.name in SCAN_SKIP:
            continue
        kind = _kind_type(child)
        if kind in {"slides", "pages"}:
            found.add(kind)
    return found


def choose_kind(root: Path, target: str, directory: str | None) -> str:
    if target in QUALITY or target == "serve":
        return "slides"
    if directory:
        kind = _kind_type(root / directory)
        if kind == "pages":
            if target == "ppt":
                sys.stderr.write("make ppt is only for type=slides directories\n")
                sys.exit(1)
            return "pages"
        if kind and kind != "slides":
            sys.stderr.write(f"{directory}/meta.toml type is {kind!r}; expected slides or pages\n")
            sys.exit(1)
        return "slides"
    kinds = _scan_kinds(root)
    if "slides" in kinds and "pages" in kinds:
        sys.stderr.write("pass a directory: make html slides or make html pages\n")
        sys.exit(1)
    if kinds == {"pages"}:
        return "pages"
    return "slides"


def resolve_skill(root: Path, kind: str) -> Path:
    if kind == "pages":
        raw = os.environ.get("MARKDOWN_PAGES_HOME", "").strip()
        marker = PAGES_MARKER
        named = "markdown-pages"
        hint = "set MARKDOWN_PAGES_HOME, or put the skill under skills/\n"
        missing = f"not a markdown-pages skill (missing {marker}): {{raw}}\n"
    else:
        raw = (
            os.environ.get("SKILL", "").strip()
            or os.environ.get("MARKDOWN_SLIDES_HOME", "").strip()
        )
        marker = SLIDES_MARKER
        named = "markdown-slides"
        hint = "set SKILL= or MARKDOWN_SLIDES_HOME, or put the skill under skills/\n"
        missing = f"not a markdown-slides skill (missing {marker}): {{raw}}\n"
    if raw:
        path = Path(raw).expanduser()
        path = path if path.is_absolute() else (root / path)
        path = path.resolve()
        if not path.is_dir() or not (path / marker).is_file():
            sys.stderr.write(missing.format(raw=raw))
            sys.exit(1)
        return path
    if _is_engine(root, kind):
        return root
    skills = root / "skills"
    found: list[Path] = []
    if skills.is_dir():
        for child in sorted(skills.iterdir()):
            if _is_engine(child, kind):
                found.append(child.resolve())
    named_hits = [path for path in found if path.name == named]
    if named_hits:
        return named_hits[0]
    if len(found) == 1:
        return found[0]
    sys.stderr.write(hint)
    sys.exit(1)


def resolve_scripts(root: Path, kind: str) -> Path | None:
    if _is_engine(root, kind):
        return None
    marker = root / (LOCAL_PAGES if kind == "pages" else LOCAL_SLIDES)
    if not marker.is_file():
        return None
    return marker.parent.resolve()


def help_text() -> str:
    return (
        "Targets (run from the deck root):\n"
        "  make <dir>       build HTML for that slides or pages directory\n"
        "                   (example: make slides -> build/slides/)\n"
        "  make html <dir>  build HTML for that directory\n"
        "  make ppt <dir>   build PPTX for a type=slides directory\n"
        "  make pdf <dir>   export PDF for that directory\n"
        "  make serve       serve build/ locally\n"
        "  make fmt         format Python in the skill\n"
        "  make lint        ruff + markdownlint (skill, plus this deck's Markdown)\n"
        "  make test        run the skill unit tests\n"
        "  make fonts       vendor Google Fonts into the skill cache\n"
        "  python3 build.py <target> [dir]  same as make\n"
        "Set SKILL or MARKDOWN_SLIDES_HOME for slides, MARKDOWN_PAGES_HOME for\n"
        "pages, or nest the skills under skills/.\n"
        "A deck-local scripts/markdown-slides/ copy runs html and serve when present.\n"
        "A deck-local scripts/markdown-pages/ copy runs html when present.\n"
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


def run_engine(root: Path, target: str, slides: str | None, kind: str) -> int:
    env = os.environ.copy()
    env["DECK_ROOT"] = str(root)
    if slides:
        env["SLIDES"] = slides
    else:
        env.pop("SLIDES", None)
    local = resolve_scripts(root, kind)
    if local is not None and target in LOCAL_TARGETS[kind]:
        result = subprocess.run(
            ["python3", str(local / LOCAL_PY[kind][target])],
            cwd=str(root),
            env=env,
            check=False,
        )
        return result.returncode
    skill = resolve_skill(root, kind)
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
    kind = choose_kind(root, target, slides)
    raise SystemExit(run_engine(root, target, slides, kind))


if __name__ == "__main__":
    main()
