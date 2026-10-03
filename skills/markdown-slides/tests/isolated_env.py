"""Strip parent Make variables so nested ``make`` in tests is isolated."""

from __future__ import annotations

import os

MAKE_LEAK = (
    "SKILL",
    "MARKDOWN_SLIDES_HOME",
    "DECK_ROOT",
    "SLIDES",
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
    if extra:
        env.update(extra)
    return env
