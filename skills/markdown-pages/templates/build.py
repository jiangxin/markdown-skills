#!/usr/bin/env python3
"""Deck-root trampoline: resolve slides or pages skill, then forward.

Copy this file next to the deck Makefile. It uses the stdlib only so the
deck can find the engine before that engine is on PYTHONPATH.

Keep this file identical in both skills:

- skills/markdown-slides/templates/build.py
- skills/markdown-pages/templates/build.py

On install, either skill copies it to the project root as build.py.
"""

from __future__ import annotations

import configparser
import os
import subprocess
import sys
import tomllib
from pathlib import Path

QUALITY = ("lint", "fmt", "test", "fonts")
FORMATS = ("html", "ppt", "pdf", "serve")
NEEDS_DOC = ("ppt", "pdf")
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
SKILL_NAMES = {"slides": "markdown-slides", "pages": "markdown-pages"}
SLIDES_MARKER = Path("scripts") / "build-slides.py"
PAGES_MARKER = Path("scripts") / "build-pages.py"


def deck_root() -> Path:
    return Path(__file__).resolve().parent


def _marker(kind: str) -> Path:
    return PAGES_MARKER if kind == "pages" else SLIDES_MARKER


def _skill_name(kind: str) -> str:
    return SKILL_NAMES[kind]


def _is_engine(path: Path, kind: str) -> bool:
    return (path / _marker(kind)).is_file() and (path / "templates").is_dir()


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


def _read_build_root_skip(root: Path) -> set[str]:
    skip = set(SCAN_SKIP)
    config_path = root / "config.ini"
    if not config_path.is_file():
        return skip
    parser = configparser.ConfigParser()
    try:
        parser.read(config_path, encoding="utf-8")
    except configparser.Error:
        return skip
    raw = parser.get("paths", "build_root", fallback="").strip()
    if not raw:
        return skip
    relative = Path(raw.replace("\\", "/"))
    if relative.is_absolute():
        return skip
    parts = relative.parts
    if parts and parts[0] not in {".", ".."}:
        skip.add(parts[0])
    return skip


def _scan_kinds(root: Path) -> set[str]:
    found: set[str] = set()
    skip = _read_build_root_skip(root)
    try:
        children = root.iterdir()
    except OSError:
        return found
    for child in children:
        if not child.is_dir() or child.name.startswith(".") or child.name in skip:
            continue
        kind = _kind_type(child)
        if kind in {"slides", "pages"}:
            found.add(kind)
    return found


def choose_kind(root: Path, target: str, directory: str | None) -> str:
    if target == "serve" or target == "fonts":
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


def _read_skills_root(root: Path) -> Path | None:
    config_path = root / "config.ini"
    if not config_path.is_file():
        return None
    parser = configparser.ConfigParser()
    try:
        parser.read(config_path, encoding="utf-8")
    except configparser.Error as exc:
        sys.stderr.write(f"config.ini: {exc}\n")
        sys.exit(1)
    raw = ""
    if parser.has_option("paths", "skills_root"):
        raw = parser.get("paths", "skills_root").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    path = path if path.is_absolute() else (root / path)
    return path.resolve()


def _env_skill(kind: str) -> str:
    if kind == "pages":
        return os.environ.get("MARKDOWN_PAGES_HOME", "").strip()
    return os.environ.get("SKILL", "").strip() or os.environ.get("MARKDOWN_SLIDES_HOME", "").strip()


def _skill_hint(kind: str) -> str:
    name = _skill_name(kind)
    return (
        f"engine not found for {name}. Set [paths] skills_root in config.ini,\n"
        f"install under .agents/skills/{name}, ~/.agents/skills/{name},\n"
        "or set SKILL / MARKDOWN_SLIDES_HOME / MARKDOWN_PAGES_HOME.\n"
    )


def try_resolve_skill(root: Path, kind: str) -> Path | None:
    """Resolve the skill root that contains scripts/ for this kind.

    Order:
    1. SKILL / MARKDOWN_SLIDES_HOME / MARKDOWN_PAGES_HOME (explicit override)
    2. config.ini [paths] skills_root / <skill-name>
    3. <deck>/.agents/skills/<skill-name>
    4. ~/.agents/skills/<skill-name>
    """
    named = _skill_name(kind)
    marker = _marker(kind)
    raw = _env_skill(kind)
    if raw:
        path = Path(raw).expanduser()
        path = path if path.is_absolute() else (root / path)
        path = path.resolve()
        if not path.is_dir() or not (path / marker).is_file():
            sys.stderr.write(f"not a {named} skill (missing {marker}): {raw}\n")
            sys.exit(1)
        return path

    candidates: list[Path] = []
    skills_root = _read_skills_root(root)
    if skills_root is not None:
        candidates.append(skills_root / named)
    candidates.append(root / ".agents" / "skills" / named)
    candidates.append(Path.home() / ".agents" / "skills" / named)

    for path in candidates:
        if _is_engine(path, kind):
            return path.resolve()
    return None


def resolve_skill(root: Path, kind: str) -> Path:
    path = try_resolve_skill(root, kind)
    if path is None:
        sys.stderr.write(_skill_hint(kind))
        sys.exit(1)
    return path


def iter_quality_skills(root: Path, target: str) -> list[tuple[str, Path]]:
    kinds = ("slides",) if target == "fonts" else ("slides", "pages")
    found: list[tuple[str, Path]] = []
    for kind in kinds:
        path = try_resolve_skill(root, kind)
        if path is not None:
            found.append((kind, path))
    return found


def run_quality(root: Path, target: str) -> int:
    found = iter_quality_skills(root, target)
    if not found:
        sys.stderr.write(
            "no slides/pages skill found. Set [paths] skills_root, install under\n"
            ".agents/skills/, ~/.agents/skills/, or set SKILL / MARKDOWN_*_HOME.\n"
        )
        sys.exit(1)
    for kind, _path in found:
        code = run_engine(root, target, None, kind)
        if code:
            return code
    return 0


def help_text() -> str:
    return (
        "Targets (run from the deck root):\n"
        "  make <dir>       build HTML for that slides or pages directory\n"
        "                   (example: make slides -> build/slides/)\n"
        "  make html <dir>  build HTML for that directory\n"
        "  make ppt <dir>   build PPTX for a type=slides directory\n"
        "  make pdf <dir>   export PDF for that directory\n"
        "  make serve       serve build/ locally\n"
        "  make fmt         format Python in each resolved skill\n"
        "  make lint        ruff + markdownlint in each resolved skill (plus this deck)\n"
        "  make test        run unit tests in each resolved skill\n"
        "  make fonts       vendor Google Fonts into the skill cache\n"
        "  python3 build.py <target> [dir]  same as make\n"
        "Engine lookup: [paths] skills_root/<skill>, then .agents/skills/<skill>,\n"
        "then ~/.agents/skills/<skill>. Override with SKILL / MARKDOWN_SLIDES_HOME\n"
        "or MARKDOWN_PAGES_HOME. Document type comes from that directory's meta.toml.\n"
    )


def parse_args(args: list[str]) -> tuple[str, str | None]:
    if not args or args[0] in {"-h", "--help", "help"}:
        return "help", None
    first = args[0]
    rest = args[1:]
    if first in QUALITY:
        return first, None
    if first in FORMATS:
        doc = rest[0] if rest else None
        if first in NEEDS_DOC and not doc:
            sys.stderr.write(f"pass a document directory: make {first} slides\n")
            sys.exit(1)
        return first, doc
    doc = first
    if rest and rest[0] in FORMATS:
        return rest[0], doc
    return "html", doc


def run_engine(root: Path, target: str, doc: str | None, kind: str) -> int:
    env = os.environ.copy()
    env["DECK_ROOT"] = str(root)
    if doc:
        env["DOC"] = doc
    else:
        env.pop("DOC", None)
    skill = resolve_skill(root, kind)
    make_args = ["make", "-C", str(skill), target, f"DECK_ROOT={root}"]
    if doc:
        make_args.append(f"DOC={doc}")
    result = subprocess.run(make_args, check=False, env=env)
    return result.returncode


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    root = deck_root()
    target, doc = parse_args(args)
    if target == "help":
        sys.stdout.write(help_text())
        return
    if target in ("fmt", "lint", "test"):
        raise SystemExit(run_quality(root, target))
    kind = choose_kind(root, target, doc)
    raise SystemExit(run_engine(root, target, doc, kind))


if __name__ == "__main__":
    main()
