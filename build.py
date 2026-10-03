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

TARGETS = ("html", "ppt", "pdf", "serve", "lint", "fmt", "test", "fonts")
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
        "  make html    build HTML via the markdown-slides skill\n"
        "  make ppt     build PPTX\n"
        "  make pdf     export PDF\n"
        "  make serve   serve the deck locally\n"
        "  make fmt     format Python in the skill\n"
        "  make lint    ruff + markdownlint (skill, plus this deck's Markdown)\n"
        "  make test    run the skill unit tests\n"
        "  make fonts   vendor Google Fonts into the skill cache\n"
        "  python3 build.py <target>  same as make <target>\n"
        "Set SKILL or MARKDOWN_SLIDES_HOME, or [build] skill in config.ini.\n"
        "Optional [build] scripts runs local html and serve.\n"
    )


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    root = deck_root()
    if not args or args[0] in {"-h", "--help", "help"}:
        sys.stdout.write(help_text())
        return
    target = args[0]
    if target not in TARGETS:
        sys.stderr.write(f"unknown target: {target}\n")
        sys.exit(1)
    local = resolve_scripts(root)
    if local is not None and target in LOCAL_TARGETS:
        env = os.environ.copy()
        env["DECK_ROOT"] = str(root)
        result = subprocess.run(
            ["python3", str(local / LOCAL_PY[target])],
            cwd=str(root),
            env=env,
            check=False,
        )
        raise SystemExit(result.returncode)
    skill = resolve_skill(root)
    result = subprocess.run(
        ["make", "-C", str(skill), target, f"DECK_ROOT={root}"],
        check=False,
    )
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
