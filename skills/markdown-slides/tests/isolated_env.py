"""Strip parent Make variables so nested ``make`` in tests is isolated."""

from __future__ import annotations

import os
from pathlib import Path

MAKE_LEAK = (
    "SKILL",
    "MARKDOWN_SLIDES_HOME",
    "MARKDOWN_PAGES_HOME",
    "DECK_ROOT",
    "SLIDES",
    "PAGES",
    "MAKEFLAGS",
    "MAKELEVEL",
    "MFLAGS",
    "MAKEOVERRIDES",
)


def isolated(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key in MAKE_LEAK:
        env.pop(key, None)
    env.setdefault("MARKDOWN_SLIDES_EMBED_FONTS", "0")
    # Avoid picking up the developer's ~/.agents/skills installs.
    env["HOME"] = str(Path(__file__).resolve().parent / "_empty_home")
    if extra:
        env.update(extra)
    return env


def write_meta(
    directory: Path,
    name: str,
    title: str = "",
    kind: str = "slides",
    *,
    order: str = "",
    sort: str = "",
    theme: str = "",
    presenter: str | None = None,
    presented_at: str | None = None,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)

    def quoted(value: str) -> str:
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = [f"type = {quoted(kind)}", f"name = {quoted(name)}"]
    if title:
        lines.append(f"title = {quoted(title)}")
    if theme:
        lines.append(f"theme = {quoted(theme)}")
    deck_lines = []
    if order:
        deck_lines.append(f"order = {quoted(order)}")
    if sort:
        deck_lines.append(f"sort = {quoted(sort)}")
    if deck_lines:
        lines.extend(("", "[deck]", *deck_lines))
    cover_lines = []
    if presenter is not None:
        cover_lines.append(f"presenter = {quoted(presenter)}")
    if presented_at is not None:
        cover_lines.append(f"presented_at = {quoted(presented_at)}")
    if cover_lines:
        lines.extend(("", "[cover]", *cover_lines))
    (directory / "meta.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
