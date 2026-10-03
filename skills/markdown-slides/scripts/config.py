#!/usr/bin/env python3
"""Read presentation configuration from meta.toml and optional config.ini.

The skill root is the directory that contains ``scripts/build-slides.py``.
The deck root is ``--deck-root``, else the ``DECK_ROOT`` environment
variable, else the skill root. ``config.ini`` holds ``[serve]``. Page
directories are selected by
``--slides`` / ``SLIDES``, or by scanning for ``meta.toml`` with
``type = "slides"``.
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
DEFAULT_ORDER = "auto"
DEFAULT_THEME = "swiss-modern"
DOC_TYPE_SLIDES = "slides"
META_FILE = "meta.toml"
ENGINE_MARKER = Path("scripts") / "build-slides.py"
LOCAL_ENGINE = Path("scripts") / "markdown-slides" / "build-slides.py"
THEME_MARKERS = (
    Path("deck.css"),
    Path("deck.js"),
    Path("pptx") / "theme.json",
)
COVER_FIELDS = ("presenter", "presented_at")
_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")


@dataclass(frozen=True)
class DocMeta:
    kind: str
    name: str
    title: str
    order: str
    sort_rel: str
    theme: str


@dataclass(frozen=True)
class Deck:
    name: str
    title: str
    kind: str
    slides: Path
    slides_rel: str
    order: str
    sort: Path | None
    sort_rel: str
    theme: str
    theme_dir: Path


@dataclass(frozen=True)
class Outputs:
    """Artifact paths under ``root/build/<slides>/``."""

    root: Path
    name: str
    title: str
    kind: str
    slides_rel: str
    html: Path
    pptx: Path
    pdf: Path
    theme: str
    theme_dir: Path


def skill_root() -> Path:
    """Return the skill directory, or the deck when this file is vendored.

    In the skill, this file lives in ``scripts/``. A deck-local copy lives in
    ``scripts/markdown-slides/`` so sibling tools can share ``scripts/``.
    """
    here = Path(__file__).resolve().parent
    if here.name == "markdown-slides":
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


def load_deck(deck_root: Path) -> Deck:
    """Load identity and slides options from that directory's ``meta.toml``.

    ``--slides`` or ``SLIDES`` selects a page directory. When omitted, a
    single ``type = "slides"`` directory under the deck root is used.
    ``config.ini`` holds ``[serve]``. This skill only builds
    ``type = "slides"``.
    """
    root = _existing_dir(deck_root)
    slides_rel = _requested_slides_rel() or _default_slides_rel(root)
    slides = _relative_path(root, slides_rel, "slides")
    doc = _load_doc_meta(slides, slides_rel)
    order, sort, sort_rel = _meta_order(slides, slides_rel, doc)
    theme, theme_dir = _resolve_theme(root, slides_rel, doc.theme)
    return Deck(
        doc.name,
        doc.title,
        doc.kind,
        slides,
        slides_rel,
        order,
        sort,
        sort_rel,
        theme,
        theme_dir,
    )


def output_paths(root: Path | None = None) -> Outputs:
    """Return ``<root>/build/<slides>/<name>.html``, ``.pptx``, and ``.pdf``.

    ``name`` comes from that directory's ``meta.toml``. When ``root`` is
    omitted, the deck root is ``deck_root()`` (``--deck-root``, else
    ``DECK_ROOT``, else the skill root). ``--slides`` and ``SLIDES``
    select the page directory.
    """
    resolved = deck_root() if root is None else _existing_dir(root)
    deck = load_deck(resolved)
    out_dir = resolved / "build" / Path(deck.slides_rel)
    return Outputs(
        root=resolved,
        name=deck.name,
        title=deck.title,
        kind=deck.kind,
        slides_rel=deck.slides_rel,
        html=out_dir / f"{deck.name}.html",
        pptx=out_dir / f"{deck.name}.pptx",
        pdf=out_dir / f"{deck.name}.pdf",
        theme=deck.theme,
        theme_dir=deck.theme_dir,
    )


def load_build_skill(deck_root: Path, environ: dict[str, str] | None = None) -> Path | None:
    """Return the engine directory for a deck, or None if not found.

    Override order: ``SKILL``, then ``MARKDOWN_SLIDES_HOME``, then this
    directory if it is the skill, then ``skills/<name>/`` under the deck
    that contains ``scripts/build-slides.py`` (the skill layout, not a
    deck-local ``scripts/markdown-slides/`` copy).
    """
    root = _existing_dir(deck_root)
    env = os.environ if environ is None else environ
    raw = _env_skill(env)
    if raw:
        return _engine_dir(root, raw)
    if _is_engine(root):
        return root
    return _nested_engine(root)


def load_build_scripts(deck_root: Path) -> Path | None:
    """Return a deck-local scripts directory, or None.

    When the deck is not the skill itself and
    ``scripts/markdown-slides/build-slides.py`` exists, html and serve run
    from that copy. A file at ``scripts/build-slides.py`` is the skill
    layout, not a vendored deck copy.
    """
    root = _existing_dir(deck_root)
    if _is_engine(root):
        return None
    marker = root / LOCAL_ENGINE
    if not marker.is_file():
        return None
    return marker.parent.resolve()


def _env_skill(env: dict[str, str]) -> str:
    for key in ("SKILL", "MARKDOWN_SLIDES_HOME"):
        raw = env.get(key, "").strip()
        if raw:
            return raw
    return ""


def _engine_dir(deck_root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = deck_root / path
    resolved = path.resolve()
    if not resolved.is_dir():
        sys.exit(f"markdown-slides skill is not a directory: {raw}")
    marker = resolved / ENGINE_MARKER
    if not marker.is_file():
        sys.exit("not a markdown-slides skill " f"(missing {ENGINE_MARKER}): {raw}")
    return resolved


def _is_engine(root: Path) -> bool:
    return (root / ENGINE_MARKER).is_file() and (root / "templates").is_dir()


def _nested_engine(root: Path) -> Path | None:
    skills = root / "skills"
    if not skills.is_dir():
        return None
    found: list[Path] = []
    for child in sorted(skills.iterdir()):
        if _is_engine(child):
            found.append(child.resolve())
    named = [path for path in found if path.name == "markdown-slides"]
    if named:
        return named[0]
    if len(found) == 1:
        return found[0]
    return None


def serve_port(deck_root: Path) -> int:
    """Return the local server port, defaulting to 8000."""
    parser = _load_parser(_existing_dir(deck_root))
    raw = parser.get("serve", "port", fallback="").strip()
    if not raw:
        return DEFAULT_PORT
    return _parse_port(raw)


def cover_overrides(deck_root: Path, path: Path, meta: dict[str, str]) -> dict[str, str]:
    """Return a copy of ``meta`` with optional ``[cover]`` overrides.

    Only a file named ``010-cover.md`` is updated. Empty values do not override.
    Values come from that page directory's ``meta.toml``.
    """
    result = dict(meta)
    if Path(path).name != "010-cover.md":
        return result
    root = _existing_dir(deck_root)
    page = Path(path)
    page = page if page.is_absolute() else (root / page)
    try:
        rel = page.parent.resolve().relative_to(root)
        where = f"{rel.as_posix()}/{META_FILE}"
    except ValueError:
        where = f"{page.parent.name}/{META_FILE}"
    data = _read_toml(page.parent / META_FILE, where)
    cover = _toml_table(data, "cover", where)
    for field in COVER_FIELDS:
        value = _toml_str(cover, field, f"{where} [cover]")
        if value:
            result[field] = value
    return result


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


def _norm_slides_rel(raw: str) -> str:
    text = raw.strip().replace("\\", "/")
    if not text or text in {".", ".."}:
        sys.exit(f"slides directory is empty or invalid: {raw!r}")
    relative = Path(text)
    if relative.is_absolute():
        sys.exit(f"slides directory must be relative to the deck root, got: {raw!r}")
    return relative.as_posix().strip("/")


def _requested_slides_rel() -> str | None:
    chosen = _option_value(list(sys.argv), "--slides")
    if chosen is None:
        chosen = os.environ.get("SLIDES", "").strip() or None
    if chosen is None:
        return None
    return _norm_slides_rel(chosen)


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


def _default_slides_rel(root: Path) -> str:
    found = _scan_slides_rels(root)
    if len(found) == 1:
        return found[0]
    if not found:
        sys.exit("pass a slides directory (make slides)")
    listed = ", ".join(found)
    sys.exit(f"multiple type=slides directories ({listed}); pass make <dir>")


def _scan_slides_rels(root: Path, current: Path | None = None, depth: int = 0) -> list[str]:
    if depth > 4:
        return []
    here = root if current is None else current
    found: list[str] = []
    try:
        children = sorted(here.iterdir())
    except OSError:
        return []
    for child in children:
        if not child.is_dir() or child.name.startswith(".") or child.name in _SCAN_SKIP:
            continue
        meta = child / META_FILE
        if meta.is_file():
            rel = child.relative_to(root).as_posix()
            data = _read_toml(meta, f"{rel}/{META_FILE}")
            kind = _toml_str(data, "type", f"{rel}/{META_FILE}") or DOC_TYPE_SLIDES
            if kind == DOC_TYPE_SLIDES:
                found.append(rel)
        found.extend(_scan_slides_rels(root, child, depth + 1))
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


def _load_doc_meta(slides_dir: Path, slides_rel: str) -> DocMeta:
    """Return identity and slides options from ``meta.toml``, or defaults."""
    where = f"{slides_rel}/{META_FILE}"
    data = _read_toml(slides_dir / META_FILE, where)
    folder = Path(slides_rel).name
    if not data:
        name = _check_name(folder, f"{slides_rel}/ (directory)")
        return DocMeta(DOC_TYPE_SLIDES, name, name, DEFAULT_ORDER, "", DEFAULT_THEME)
    kind = _toml_str(data, "type", where) or DOC_TYPE_SLIDES
    if kind != DOC_TYPE_SLIDES:
        sys.exit(f'{where} type is {kind!r}; this skill only builds type = "slides"')
    name = _toml_str(data, "name", where) or folder
    name = _check_name(name, f"{where} name")
    title = _toml_str(data, "title", where) or name
    deck = _toml_table(data, "deck", where)
    order = _toml_str(deck, "order", f"{where} [deck]")
    sort_rel = _toml_str(deck, "sort", f"{where} [deck]")
    theme = _toml_str(data, "theme", where)
    return DocMeta(
        kind,
        name,
        title,
        order,
        sort_rel,
        theme or DEFAULT_THEME,
    )


def _meta_order(
    slides_dir: Path,
    slides_rel: str,
    doc: DocMeta,
) -> tuple[str, Path | None, str]:
    where = f"{slides_rel}/{META_FILE}"
    order = doc.order
    sort_rel = doc.sort_rel
    if order and order != DEFAULT_ORDER:
        sys.exit(f"{where} [deck] order must be auto, got: {order!r}")
    if order == DEFAULT_ORDER and sort_rel:
        sys.exit(f"{where} [deck] order and sort cannot both be set")
    if sort_rel:
        return "", _sort_path(slides_dir, sort_rel, where), sort_rel
    return DEFAULT_ORDER, None, ""


def _sort_path(slides_dir: Path, raw: str, where: str) -> Path:
    relative = Path(raw)
    if relative.is_absolute():
        sys.exit(
            f"{where} [deck] sort must be a path relative to the slides " f"directory, got: {raw!r}"
        )
    resolved = (slides_dir / relative).resolve()
    try:
        resolved.relative_to(slides_dir.resolve())
    except ValueError:
        sys.exit(f"{where} [deck] sort escapes the slides directory, got: {raw!r}")
    return resolved


def _theme_complete(theme_dir: Path) -> bool:
    return theme_dir.is_dir() and all((theme_dir / marker).is_file() for marker in THEME_MARKERS)


def _bundled_theme_dir(root: Path, name: str) -> Path | None:
    """Skill ``templates/<name>/``, including when scripts are vendored."""
    here = skill_root() / "templates" / name
    if _theme_complete(here):
        return here
    engine = load_build_skill(root)
    if engine is None:
        return None
    bundled = engine / "templates" / name
    if _theme_complete(bundled):
        return bundled
    return None


def _resolve_theme(root: Path, slides_rel: str, raw: str) -> tuple[str, Path]:
    where = f"{slides_rel}/{META_FILE}"
    if _NAME_RE.fullmatch(raw) is None:
        sys.exit(f"{where} theme must contain only letters, digits, and " f"hyphens, got: {raw!r}")
    local = root / "themes" / raw
    if _theme_complete(local):
        return raw, local.resolve()
    bundled = _bundled_theme_dir(root, raw)
    if bundled is not None:
        return raw, bundled.resolve()
    sys.exit(
        f"{where} theme is not a complete directory in deck " f"themes/ or skill templates/: {raw}"
    )


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


_OUTPUT_KINDS = ("html", "pptx", "pdf", "json")


def _print_output(kind: str, paths: Outputs) -> None:
    if kind == "json":
        json.dump(
            {
                "root": str(paths.root),
                "skillRoot": str(skill_root()),
                "name": paths.name,
                "title": paths.title,
                "type": paths.kind,
                "slides": paths.slides_rel,
                "html": str(paths.html),
                "pptx": str(paths.pptx),
                "pdf": str(paths.pdf),
                "theme": paths.theme,
                "themeDir": str(paths.theme_dir),
            },
            sys.stdout,
            ensure_ascii=False,
        )
        sys.stdout.write("\n")
        return
    sys.stdout.write(str(getattr(paths, kind)) + "\n")


def main(argv: list[str] | None = None) -> None:
    """Print a default artifact path or the configured engine directory.

    ``python3 scripts/config.py --print-output pptx`` prints the PPTX path.
    ``pdf``, ``html``, and ``json`` are the other kinds. ``--print-skill``
    prints the engine path. ``--deck-root`` and ``DECK_ROOT`` are read by
    ``deck_root()``.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if "--print-skill" in args:
        saved = sys.argv
        try:
            if argv is not None:
                sys.argv = ["config.py", *args]
            engine = load_build_skill(deck_root())
        finally:
            sys.argv = saved
        if engine is None:
            sys.exit("set SKILL= or MARKDOWN_SLIDES_HOME, or put the skill under skills/")
        sys.stdout.write(str(engine) + "\n")
        return
    flag = "--print-output"
    if flag not in args:
        sys.exit(
            "usage: python3 scripts/config.py --print-output "
            "{html,pptx,pdf,json} | --print-skill"
        )
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
