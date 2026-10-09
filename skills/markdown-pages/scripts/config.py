#!/usr/bin/env python3
"""Read book configuration from meta.toml and optional config.ini.

The skill root is the directory that contains this file's ``scripts/``
parent. The deck root is ``--deck-root``, else the ``DECK_ROOT``
environment variable, else the skill root. ``config.ini`` holds
``[serve]`` and optional ``[paths]`` / ``[assets]``. Book directories
are selected by ``--doc`` / ``DOC``, or by scanning for ``meta.toml``
with ``type = "pages"``.
"""

from __future__ import annotations

import configparser
import json
import os
import re
import sys
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 8000
DEFAULT_BUILD_ROOT = "build"
DEFAULT_ORDER = "auto"
DOC_TYPE_PAGES = "pages"
META_FILE = "meta.toml"
_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")
_CHAPTER_RE = re.compile(r"^[0-9]{2,3}-[a-z0-9-]+\.md$")
_WEBFONT_ON = frozenset({"1", "true", "yes", "on"})
_WEBFONT_OFF = frozenset({"", "0", "false", "no", "off"})


@dataclass(frozen=True)
class DocMeta:
    kind: str
    name: str
    title: str
    order: str
    sort_rel: str


@dataclass(frozen=True)
class Book:
    name: str
    title: str
    kind: str
    pages: Path
    pages_rel: str
    order: str
    sort: Path | None
    sort_rel: str


@dataclass(frozen=True)
class Outputs:
    """Artifact paths under ``<build_root>/<pages>/``.

    ``site`` is the multi-page directory. ``html`` and ``pdf`` are the
    one-file ebook and PDF beside it.
    """

    root: Path
    name: str
    title: str
    kind: str
    pages_rel: str
    html: Path
    pdf: Path
    site: Path
    build_root: Path


def skill_root() -> Path:
    """Return the skill directory, or the deck when this file is vendored.

    In the skill, this file lives in ``scripts/``. A deck-local copy lives in
    ``scripts/markdown-pages/`` so sibling tools can share ``scripts/``.
    """
    here = Path(__file__).resolve().parent
    if here.name == "markdown-pages":
        return here.parent.parent
    return here.parent


def deck_root(argv: list[str] | None = None) -> Path:
    """Resolve the deck root. The path must be an existing directory."""
    args = list(sys.argv if argv is None else argv)
    chosen = _option_value(args, "--deck-root")
    if chosen is None:
        chosen = os.environ.get("DECK_ROOT", "").strip() or None
    if chosen is None:
        return skill_root()
    return _existing_dir(chosen)


def load_book(deck_root: Path) -> Book:
    """Load identity and book options from that directory's ``meta.toml``.

    ``--doc`` or ``DOC`` selects a book directory. When omitted, a
    single ``type = "pages"`` directory under the deck root is used.
    This skill only builds ``type = "pages"``.
    """
    root = _existing_dir(deck_root)
    pages_rel = _requested_doc_rel() or _default_pages_rel(root)
    pages = _relative_path(root, pages_rel, "doc")
    doc = _load_doc_meta(pages, pages_rel)
    order, sort, sort_rel = _meta_order(pages, pages_rel, doc)
    return Book(
        doc.name,
        doc.title,
        doc.kind,
        pages,
        pages_rel,
        order,
        sort,
        sort_rel,
    )


load_deck = load_book


def build_root(deck_root: Path) -> Path:
    """Return the artifact root directory (default ``<deck>/build``).

    ``config.ini`` ``[paths] build_root`` overrides the default. Relative
    paths are resolved from the deck root.
    """
    root = _existing_dir(deck_root)
    parser = _load_parser(root)
    raw = parser.get("paths", "build_root", fallback="").strip()
    if not raw:
        raw = DEFAULT_BUILD_ROOT
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def output_paths(root: Path | None = None) -> Outputs:
    """Return artifact paths for the selected book.

    The multi-page site is ``<build_root>/<pages>/pages/``. The one-file
    HTML and PDF are ``<build_root>/<pages>/<name>.html`` and ``.pdf``.
    ``name`` comes from that directory's ``meta.toml``. When ``root`` is
    omitted, the deck root is ``deck_root()``. ``--doc`` and ``DOC``
    select the book directory. ``[paths] build_root`` overrides ``build/``.
    """
    resolved = deck_root() if root is None else _existing_dir(root)
    book = load_book(resolved)
    artifacts = build_root(resolved)
    out_dir = artifacts / Path(book.pages_rel)
    return Outputs(
        root=resolved,
        name=book.name,
        title=book.title,
        kind=book.kind,
        pages_rel=book.pages_rel,
        html=out_dir / f"{book.name}.html",
        pdf=out_dir / f"{book.name}.pdf",
        site=out_dir / "pages",
        build_root=artifacts,
    )


def list_chapters(pages_dir: Path) -> list[Path]:
    """Return the home ``README.md`` (if present) then numbered chapters.

    Numbered files match ``NN-slug.md`` or ``NNN-slug.md`` in that
    directory only. ``meta.toml`` is not a chapter.
    """
    directory = Path(pages_dir)
    chapters: list[Path] = []
    home = directory / "README.md"
    if home.is_file():
        chapters.append(home.resolve())
    numbered = [
        path.resolve()
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
        if path.is_file() and _CHAPTER_RE.fullmatch(path.name)
    ]
    chapters.extend(numbered)
    return chapters


def serve_port(deck_root: Path) -> int:
    """Return the local server port, defaulting to 8000."""
    parser = _load_parser(_existing_dir(deck_root))
    raw = parser.get("serve", "port", fallback="").strip()
    if not raw:
        return DEFAULT_PORT
    return _parse_port(raw)


def webfont_enabled(deck_root: Path) -> bool:
    """Return whether HTML should inline cached webfonts (default off)."""
    parser = _load_parser(_existing_dir(deck_root))
    raw = parser.get("assets", "webfont", fallback="off").strip().lower()
    if raw in _WEBFONT_ON:
        return True
    if raw in _WEBFONT_OFF:
        return False
    sys.exit(f"config.ini [assets] webfont must be on or off, got: {raw!r}")


def _paths_build_root_skip(root: Path) -> set[str]:
    """Top-level names to skip when scanning, including custom build_root."""
    skip = set(_SCAN_SKIP)
    raw = _load_parser(root).get("paths", "build_root", fallback="").strip()
    if not raw:
        return skip
    relative = Path(raw.replace("\\", "/"))
    if relative.is_absolute():
        return skip
    parts = relative.parts
    if parts and parts[0] not in {".", ".."}:
        skip.add(parts[0])
    return skip


def _existing_dir(raw: str | Path) -> Path:
    path = Path(raw).expanduser()
    if not path.is_dir():
        sys.exit(f"deck root does not exist or is not a directory: {raw}")
    return path.resolve()


def _option_value(argv: list[str], flag: str) -> str | None:
    prefix = f"{flag}="
    for index, arg in enumerate(argv):
        if arg == flag:
            if index + 1 >= len(argv):
                sys.exit(f"missing value for {flag}")
            return argv[index + 1]
        if arg.startswith(prefix):
            value = arg[len(prefix) :]
            if not value:
                sys.exit(f"missing value for {flag}")
            return value
    return None


def _norm_doc_rel(raw: str) -> str:
    text = raw.strip().replace("\\", "/")
    if not text or text in {".", ".."}:
        sys.exit(f"doc directory is empty or invalid: {raw!r}")
    relative = Path(text)
    if relative.is_absolute():
        sys.exit(f"doc directory must be relative to the deck root, got: {raw!r}")
    return relative.as_posix().strip("/")


def _requested_doc_rel() -> str | None:
    chosen = _option_value(list(sys.argv), "--doc")
    if chosen is None:
        chosen = os.environ.get("DOC", "").strip() or None
    if chosen is None:
        return None
    return _norm_doc_rel(chosen)


_SCAN_SKIP = {
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


def _default_pages_rel(root: Path) -> str:
    found = _scan_pages_rels(root)
    if len(found) == 1:
        return found[0]
    if not found:
        sys.exit("pass a pages directory (make html)")
    listed = ", ".join(found)
    sys.exit(f"multiple type=pages directories ({listed}); pass make <dir>")


def _scan_pages_rels(root: Path, current: Path | None = None, depth: int = 0) -> list[str]:
    if depth > 4:
        return []
    here = root if current is None else current
    found: list[str] = []
    skip = _paths_build_root_skip(root)
    try:
        children = sorted(here.iterdir())
    except OSError:
        return []
    for child in children:
        if not child.is_dir() or child.name.startswith(".") or child.name in skip:
            continue
        meta = child / META_FILE
        if meta.is_file():
            rel = child.relative_to(root).as_posix()
            data = _read_toml(meta, f"{rel}/{META_FILE}")
            kind = _toml_str(data, "type", f"{rel}/{META_FILE}") or DOC_TYPE_PAGES
            if kind == DOC_TYPE_PAGES:
                found.append(rel)
        found.extend(_scan_pages_rels(root, child, depth + 1))
    return found


def _load_parser(root: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    path = root / "config.ini"
    if not path.is_file():
        return parser
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error as exc:
        sys.exit(f"config.ini: {exc}")
    return parser


def _check_name(raw: str, where: str) -> str:
    if _NAME_RE.fullmatch(raw) is None:
        sys.exit(f"{where} must contain only letters, digits, and hyphens, got: {raw!r}")
    return raw


def _toml_str(data: Mapping[str, object], key: str, where: str) -> str:
    if key not in data:
        return ""
    value = data[key]
    if not isinstance(value, str):
        sys.exit(f"{where} {key} must be a string")
    return value.strip()


def _toml_table(data: Mapping[str, object], key: str, where: str) -> dict[str, object]:
    if key not in data:
        return {}
    value = data[key]
    if not isinstance(value, dict):
        sys.exit(f"{where} [{key}] must be a table")
    return {str(name): item for name, item in value.items()}


def _read_toml(path: Path, where: str) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        sys.exit(f"{where}: {exc}")
    if not isinstance(raw, dict):
        sys.exit(f"{where} must be a TOML table")
    return {str(name): item for name, item in raw.items()}


def _load_doc_meta(pages_dir: Path, pages_rel: str) -> DocMeta:
    """Return identity and book options from ``meta.toml``, or defaults."""
    where = f"{pages_rel}/{META_FILE}"
    data = _read_toml(pages_dir / META_FILE, where)
    folder = Path(pages_rel).name
    if not data:
        name = _check_name(folder, f"{pages_rel}/ (directory)")
        return DocMeta(DOC_TYPE_PAGES, name, name, DEFAULT_ORDER, "")
    kind = _toml_str(data, "type", where) or DOC_TYPE_PAGES
    if kind != DOC_TYPE_PAGES:
        sys.exit(f'{where} type is {kind!r}; this skill only builds type = "pages"')
    name = _toml_str(data, "name", where) or folder
    name = _check_name(name, f"{where} name")
    title = _toml_str(data, "title", where) or name
    book = _toml_table(data, "book", where)
    order = _toml_str(book, "order", f"{where} [book]")
    sort_rel = _toml_str(book, "sort", f"{where} [book]")
    return DocMeta(kind, name, title, order, sort_rel)


def _meta_order(
    pages_dir: Path,
    pages_rel: str,
    doc: DocMeta,
) -> tuple[str, Path | None, str]:
    where = f"{pages_rel}/{META_FILE}"
    order = doc.order
    sort_rel = doc.sort_rel
    if order and order != DEFAULT_ORDER:
        sys.exit(f"{where} [book] order must be auto, got: {order!r}")
    if order == DEFAULT_ORDER and sort_rel:
        sys.exit(f"{where} [book] order and sort cannot both be set")
    if sort_rel:
        return "", _sort_path(pages_dir, sort_rel, where), sort_rel
    return DEFAULT_ORDER, None, ""


def _sort_path(pages_dir: Path, raw: str, where: str) -> Path:
    relative = Path(raw)
    if relative.is_absolute():
        sys.exit(
            f"{where} [book] sort must be a path relative to the pages " f"directory, got: {raw!r}"
        )
    resolved = (pages_dir / relative).resolve()
    try:
        resolved.relative_to(pages_dir.resolve())
    except ValueError:
        sys.exit(f"{where} [book] sort escapes the pages directory, got: {raw!r}")
    return resolved


def _relative_path(root: Path, raw: str, key: str) -> Path:
    relative = Path(raw)
    if relative.is_absolute():
        sys.exit(f"{key} must be a path relative to the deck root, got: {raw!r}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        sys.exit(f"{key} escapes the deck root, got: {raw!r}")
    return resolved


_OUTPUT_KINDS = ("html", "pdf", "json")


def _print_output(kind: str, paths: Outputs) -> None:
    if kind == "json":
        json.dump(
            {
                "root": str(paths.root),
                "skillRoot": str(skill_root()),
                "name": paths.name,
                "title": paths.title,
                "type": paths.kind,
                "pages": paths.pages_rel,
                "html": str(paths.html),
                "pdf": str(paths.pdf),
                "buildRoot": str(paths.build_root),
            },
            sys.stdout,
            ensure_ascii=False,
        )
        sys.stdout.write("\n")
        return
    sys.stdout.write(str(getattr(paths, kind)) + "\n")


def main(argv: list[str] | None = None) -> None:
    """Print a default artifact path for the selected book directory."""
    args = list(sys.argv[1:] if argv is None else argv)
    flag = "--print-output"
    if flag not in args:
        sys.exit("usage: python3 scripts/config.py --print-output {html,pdf,json}")
    index = args.index(flag)
    kind = "json"
    if index + 1 < len(args) and not args[index + 1].startswith("-"):
        kind = args[index + 1]
    if kind not in _OUTPUT_KINDS:
        sys.exit("--print-output must be one of " f"{', '.join(_OUTPUT_KINDS)}, got: {kind}")
    saved = sys.argv
    try:
        if argv is not None:
            sys.argv = ["config.py", *args]
        paths = output_paths()
    finally:
        sys.argv = saved
    _print_output(kind, paths)


def _parse_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError:
        sys.exit(f"config.ini [serve] port must be an integer, got: {raw!r}")
    if not 1 <= port <= 65535:
        sys.exit(f"config.ini [serve] port must be in 1..65535, got: {port}")
    return port


if __name__ == "__main__":
    main()
