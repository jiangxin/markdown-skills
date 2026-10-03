#!/usr/bin/env python3
"""Read presentation configuration from a deck-root config.ini.

The skill root is the directory that contains ``scripts/``. The deck root is
``--deck-root``, else the ``DECK_ROOT`` environment variable, else the skill
root. ``config.ini`` is read from the deck root.
"""

from __future__ import annotations

import configparser
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 8000
DEFAULT_SLIDES = "slides"
DEFAULT_ORDER = "auto"
DEFAULT_THEME = "swiss-modern"
ENGINE_MARKER = Path("scripts") / "build-slides.py"
THEME_MARKERS = (
    Path("deck.css"),
    Path("deck.js"),
    Path("pptx") / "theme.json",
)
COVER_FIELDS = ("presenter", "presented_at")
_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")


@dataclass(frozen=True)
class Deck:
    name: str
    title: str
    slides: Path
    slides_rel: str
    order: str
    sort: Path | None
    sort_rel: str
    theme: str
    theme_dir: Path


@dataclass(frozen=True)
class Outputs:
    """Default artifact paths for one deck. All of them live in ``root``."""

    root: Path
    name: str
    title: str
    html: Path
    pptx: Path
    pdf: Path
    theme: str
    theme_dir: Path


def skill_root() -> Path:
    """Return the directory that contains ``scripts/``."""
    return Path(__file__).resolve().parent.parent


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
    """Load ``[deck]`` name, title, slides, and page-order keys for ``deck_root``."""
    root = _existing_dir(deck_root)
    parser = _load_parser(root)
    name = _deck_name(parser, root)
    title = parser.get("deck", "title", fallback="").strip() or name
    slides_rel = parser.get("deck", "slides", fallback="").strip() or DEFAULT_SLIDES
    order, sort, sort_rel = _deck_order(parser, root)
    theme, theme_dir = _deck_theme(parser, root)
    return Deck(
        name,
        title,
        _relative_path(root, slides_rel, "slides"),
        slides_rel,
        order,
        sort,
        sort_rel,
        theme,
        theme_dir,
    )


def output_paths(root: Path | None = None) -> Outputs:
    """Return ``<root>/<name>.html``, ``.pptx``, and ``.pdf``.

    ``name`` comes from ``[deck] name``. When ``root`` is omitted, the deck
    root is ``deck_root()`` (``--deck-root``, else ``DECK_ROOT``, else the
    skill root).
    """
    resolved = deck_root() if root is None else _existing_dir(root)
    deck = load_deck(resolved)
    return Outputs(
        root=resolved,
        name=deck.name,
        title=deck.title,
        html=resolved / f"{deck.name}.html",
        pptx=resolved / f"{deck.name}.pptx",
        pdf=resolved / f"{deck.name}.pdf",
        theme=deck.theme,
        theme_dir=deck.theme_dir,
    )


def load_build_skill(deck_root: Path, environ: dict[str, str] | None = None) -> Path | None:
    """Return the engine directory for a deck, or None if unset.

    Override order: ``SKILL``, then ``MARKDOWN_SLIDES_HOME``, then
    ``[build] skill`` in the deck ``config.ini``. Relative values are
    resolved from the deck root. Absolute paths and ``~`` are allowed, and
    the path may leave the deck root. The directory must contain
    ``scripts/build-slides.py``.
    """
    root = _existing_dir(deck_root)
    env = os.environ if environ is None else environ
    raw = _env_skill(env)
    if not raw:
        parser = _load_parser(root)
        raw = parser.get("build", "skill", fallback="").strip()
    if not raw:
        return None
    return _engine_dir(root, raw)


def load_build_scripts(deck_root: Path) -> Path | None:
    """Return a deck-local scripts directory, or None if unset.

    ``[build] scripts`` is relative to the deck root and must stay inside
    it. The directory must contain ``build-slides.py``.
    """
    root = _existing_dir(deck_root)
    parser = _load_parser(root)
    raw = parser.get("build", "scripts", fallback="").strip()
    if not raw:
        return None
    resolved = _relative_path(root, raw, "scripts")
    marker = resolved / "build-slides.py"
    if not marker.is_file():
        sys.exit(
            "config.ini [build] scripts is not a markdown-slides scripts "
            f"directory (missing build-slides.py): {raw}"
        )
    return resolved


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
    """
    result = dict(meta)
    if Path(path).name != "010-cover.md":
        return result
    parser = _load_parser(_existing_dir(deck_root))
    if not parser.has_section("cover"):
        return result
    for field in COVER_FIELDS:
        if not parser.has_option("cover", field):
            continue
        value = parser.get("cover", field, fallback="").strip()
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


def _deck_name(parser: configparser.ConfigParser, root: Path) -> str:
    raw = parser.get("deck", "name", fallback="").strip()
    if not raw:
        return root.name
    if _NAME_RE.fullmatch(raw) is None:
        sys.exit(
            "config.ini [deck] name must contain only letters, digits, and "
            f"hyphens, got: {raw!r}"
        )
    return raw


def _deck_order(parser: configparser.ConfigParser, root: Path) -> tuple[str, Path | None, str]:
    order = parser.get("deck", "order", fallback="").strip()
    sort_rel = parser.get("deck", "sort", fallback="").strip()
    if order and order != DEFAULT_ORDER:
        sys.exit("config.ini [deck] order must be auto, " f"got: {order!r}")
    if order == DEFAULT_ORDER and sort_rel:
        sys.exit("config.ini [deck] order and sort cannot both be set")
    if sort_rel:
        return "", _relative_path(root, sort_rel, "sort"), sort_rel
    return DEFAULT_ORDER, None, ""


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


def _deck_theme(parser: configparser.ConfigParser, root: Path) -> tuple[str, Path]:
    raw = parser.get("build", "theme", fallback="").strip() or DEFAULT_THEME
    if _NAME_RE.fullmatch(raw) is None:
        sys.exit(
            "config.ini [build] theme must contain only letters, digits, and "
            f"hyphens, got: {raw!r}"
        )
    local = root / "themes" / raw
    if _theme_complete(local):
        return raw, local.resolve()
    bundled = _bundled_theme_dir(root, raw)
    if bundled is not None:
        return raw, bundled.resolve()
    sys.exit(
        "config.ini [build] theme is not a complete directory in deck "
        f"themes/ or skill templates/: {raw}"
    )


def _relative_path(root: Path, raw: str, key: str) -> Path:
    relative = Path(raw)
    section = "build" if key == "scripts" else "deck"
    if relative.is_absolute():
        sys.exit(
            f"config.ini [{section}] {key} must be a path relative to the "
            f"deck root, got: {raw!r}"
        )
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        sys.exit(f"config.ini [{section}] {key} escapes the deck root, got: {raw!r}")
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
            sys.exit("set SKILL= or MARKDOWN_SLIDES_HOME, or [build] skill in " "config.ini")
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
