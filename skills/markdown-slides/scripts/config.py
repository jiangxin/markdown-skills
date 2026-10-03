#!/usr/bin/env python3
"""Read presentation configuration from a deck-root config.ini.

The skill root is the directory that contains ``scripts/``. The deck root is
``--deck-root``, else the ``DECK_ROOT`` environment variable, else the skill
root. ``config.ini`` is read from the deck root.
"""

from __future__ import annotations

import configparser
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 8000
DEFAULT_SLIDES = "slides"
COVER_FIELDS = ("presenter", "presented_at")
_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")


@dataclass(frozen=True)
class Deck:
    name: str
    title: str
    slides: Path
    slides_rel: str


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
    """Load ``[deck]`` name, title, and slides for ``deck_root``."""
    root = _existing_dir(deck_root)
    parser = _load_parser(root)
    name = _deck_name(parser, root)
    title = parser.get("deck", "title", fallback="").strip() or name
    slides_rel = parser.get("deck", "slides", fallback="").strip() or DEFAULT_SLIDES
    return Deck(name, title, _slides_dir(root, slides_rel), slides_rel)


def serve_port(deck_root: Path) -> int:
    """Return the local server port, defaulting to 8000."""
    parser = _load_parser(_existing_dir(deck_root))
    raw = parser.get("serve", "port", fallback="").strip()
    if not raw:
        return DEFAULT_PORT
    return _parse_port(raw)


def cover_overrides(
    deck_root: Path, path: Path, meta: dict[str, str]
) -> dict[str, str]:
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


def _slides_dir(root: Path, slides_rel: str) -> Path:
    relative = Path(slides_rel)
    if relative.is_absolute():
        sys.exit(
            "config.ini [deck] slides must be a path relative to the deck "
            f"root, got: {slides_rel!r}"
        )
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        sys.exit(
            "config.ini [deck] slides escapes the deck root, "
            f"got: {slides_rel!r}"
        )
    return resolved


def _parse_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError:
        sys.exit(f"config.ini [serve] port must be an integer, got: {raw!r}")
    if not 1 <= port <= 65535:
        sys.exit(f"config.ini [serve] port must be in 1..65535, got: {port}")
    return port
