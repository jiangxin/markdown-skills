#!/usr/bin/env python3
"""Parse a deck's slide directory into a JSON-serializable model.

Shared by the HTML builder and the PPTX builder. Do not put presentation
markup here — only page data.

Slide order defaults to filename order of ``NNN-slug.md`` in the page
directory. Set ``[deck] sort`` in that directory's ``meta.toml`` to a
Markdown file whose ``## Slides`` links list the pages. ``[deck] order =
auto`` is the explicit filename mode.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

import config

PAGE_NAME = re.compile(r"^(?:(\d{3})-)?([a-z0-9-]+)\.md$")
_GIT_DESCRIBE: dict[Path, str] = {}

_MARKDOWN_LINK = re.compile(r"\[([^\]]+?)\]\(([^)]+?)\)")
_BARE_URL = re.compile(
    r"https?://[^\s<>\]]+"
    r"|(?<![\w./:@])(?:www\.)?(?:[A-Za-z0-9-]+\.)+"
    r"(?:com|org|net|edu|io|ai|dev|app|blog|co|cn)(?:/[^\s<>)\]]*)?",
    re.I,
)
_TRAIL_PUNCT = ".,;:)]）」』、。！？"
_SLIDES_HEADING = re.compile(r"^## Slides\s*$([\s\S]*?)(?=^## |\Z)", re.M)


def _fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def href_for(url: str) -> str:
    target = url.strip()
    lowered = target.lower()
    if lowered.startswith(("http://", "https://")):
        return target
    if target.startswith("//"):
        return "https:" + target
    return "https://" + target


def linkify_footer(text: str) -> str:
    """Wrap bare http(s) URLs and scheme-less hosts as Markdown links."""
    if not text:
        return text
    protected = [(m.start(), m.end()) for m in _MARKDOWN_LINK.finditer(text)]

    def covered(index: int) -> bool:
        return any(start <= index < end for start, end in protected)

    chunks: list[str] = []
    pos = 0
    for match in _BARE_URL.finditer(text):
        if covered(match.start()):
            continue
        raw = match.group(0).rstrip(_TRAIL_PUNCT)
        if not raw:
            continue
        start = match.start()
        end = start + len(raw)
        chunks.append(text[pos:start])
        chunks.append(f"[{raw}]({href_for(raw)})")
        pos = end
    chunks.append(text[pos:])
    return "".join(chunks)


def _strip_one_quote_pair(value: str) -> str:
    """Strip whitespace, then exactly one matching quote pair.

    ``"engineers'"`` stays ``engineers'``. ``"'hello'"`` stays ``'hello'``.
    A value that is not wrapped in matching quotes is left unchanged.
    """
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for raw in parts[1].splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = _strip_one_quote_pair(value)
    if meta.get("footer"):
        meta["footer"] = linkify_footer(meta["footer"])
    return meta, parts[2].strip()


TEXT_SIZES = {"s", "l", "xl", "xxl"}
CARD_TONES = {"filled", "red"}
IMAGE_FITS = frozenset({"contain", "cover", "fill", "width", "height"})


def normalize_image_fit(value: str | None) -> str:
    fit = (value or "contain").strip().lower()
    return fit if fit in IMAGE_FITS else "contain"


def parse_note_slot(flags: list[str]) -> str:
    """``:::note`` flags: ``foot`` (or ``slot:foot``) is the footer; otherwise a band."""
    for flag in flags:
        if flag == "foot" or flag in {"slot:foot", "slot:footer"}:
            return "foot"
    return ""


def note_parts(note: dict | None) -> tuple[str | None, str | None]:
    """Split a note into ``(band_note, foot_note)``."""
    if not note:
        return None, None
    text = note.get("text") or ""
    if not text:
        return None, None
    if note.get("slot") == "foot":
        return None, text
    return text, None


def parse_cards(
    body: str,
    *,
    slide_dir: Path | None = None,
    deck_root: Path | None = None,
) -> tuple[list[dict], dict | None]:
    cards: list[dict] = []
    note = None
    pattern = re.compile(r":::([a-z]+)([^\n]*)\n(.*?):::", re.S)
    for match in pattern.finditer(body):
        kind = match.group(1).strip()
        flags = match.group(2).strip().split()
        inner = match.group(3).strip()
        card = {
            "tone": "default",
            "num": "",
            "title": "",
            "paragraphs": [],
            "bullets": [],
            "slot": "",
            "marker": "",
            "size": "",
            "weight": "",
            "height": "",
            "inline_head": "",
            "image": None,
            "image_max_height": "",
            "image_max_width": "",
            "image_fit": "",
            "image_height": "",
            "alt": "",
            "scroll": "",
            "html_only": "",
            "include": "",
            "markdown": "",
        }
        for flag in flags:
            if flag in CARD_TONES:
                card["tone"] = flag
            elif flag in {"left", "mid", "right"}:
                card["slot"] = flag
            elif flag == "marker":
                card["marker"] = "on"
            elif flag == "inline-head":
                card["inline_head"] = "on"
            elif flag == "scroll":
                card["scroll"] = "on"
            elif flag == "html-only":
                card["html_only"] = "on"
            elif flag in TEXT_SIZES:
                card["size"] = flag
        if kind == "note":
            note = {"text": inner, "slot": parse_note_slot(flags)}
            continue
        paragraphs: list[str] = []
        bullets: list[dict] = []
        buf: list[str] = []
        indents: list[int] = []

        def flush():
            if buf:
                paragraphs.append(" ".join(buf))
                buf.clear()

        for raw in inner.splitlines():
            line = raw.rstrip()
            stripped = line.strip()
            if stripped.startswith("num:"):
                flush()
                card["num"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("title:"):
                flush()
                card["title"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("tone:"):
                value = stripped.split(":", 1)[1].strip()
                if value in CARD_TONES:
                    card["tone"] = value
            elif stripped.startswith("slot:"):
                card["slot"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("size:"):
                card["size"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("weight:"):
                card["weight"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("height:"):
                card["height"] = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            elif stripped.startswith("inline_head:"):
                card["inline_head"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("marker:"):
                card["marker"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("scroll:"):
                card["scroll"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("html_only:"):
                card["html_only"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("include:"):
                flush()
                spec = stripped.split(":", 1)[1].strip()
                resolved = resolve_include(spec, slide_dir=slide_dir, deck_root=deck_root)
                if not resolved:
                    where = slide_dir if slide_dir is not None else deck_root
                    _fail(f"include not found: {spec} ({where})")
                card["include"] = resolved["src"]
                card["markdown"] = resolved["text"]
            elif stripped.startswith("image:"):
                flush()
                spec = stripped.split(":", 1)[1].strip()
                resolved = resolve_image(spec, slide_dir=slide_dir, deck_root=deck_root)
                if not resolved:
                    where = slide_dir if slide_dir is not None else deck_root
                    _fail(f"image not found: {spec} ({where})")
                card["image"] = resolved
            elif stripped.startswith("image_max_height:"):
                card["image_max_height"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("image_max_width:"):
                card["image_max_width"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("image_fit:"):
                card["image_fit"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("image_height:"):
                card["image_height"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("alt:"):
                card["alt"] = stripped.split(":", 1)[1].strip().strip('"')
            elif stripped.startswith("body:"):
                flush()
                rest = stripped.split(":", 1)[1].strip()
                if rest:
                    buf.append(rest)
            elif stripped.startswith("- "):
                flush()
                # Indentation sets the level: deeper than the parent pushes,
                # shallower pops, and depth is the stack size minus one.
                indent = len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())
                while indents and indent < indents[-1]:
                    indents.pop()
                if not indents or indent > indents[-1]:
                    indents.append(indent)
                bullets.append({"text": stripped[2:].strip(), "depth": len(indents) - 1})
            elif stripped == "":
                flush()
            else:
                buf.append(stripped)
        flush()
        card["paragraphs"] = paragraphs
        card["bullets"] = bullets
        cards.append(card)
    return cards, note


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return (0, 0)
    import struct

    return struct.unpack(">II", data[16:24])


def _locate(spec: str, *, slide_dir: Path | None, deck_root: Path | None) -> Path | None:
    """Find ``spec`` in the slide file's directory, then the deck root.

    A resolved file must stay inside the deck root. ``../note.md`` from a
    slides directory is fine when it lands on a file in the deck; an absolute
    path or a ``../`` that resolves outside the deck is not.
    """
    cleaned = spec.strip().strip('"').strip("'")
    if not cleaned:
        return None
    if slide_dir is None or deck_root is None:
        _fail(f"path resolution requires the slide directory and deck root: {cleaned}")
    raw = Path(cleaned)
    candidates = [raw] if raw.is_absolute() else [slide_dir / raw, deck_root / raw]
    root = deck_root.resolve()
    for cand in candidates:
        resolved = cand.resolve()
        if not resolved.is_file():
            continue
        try:
            resolved.relative_to(root)
        except ValueError:
            _fail(f"path outside deck: {cleaned} ({resolved})")
        return cand
    return None


def _src_for(path: Path, deck_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(deck_root.resolve()).as_posix()
    except ValueError:
        _fail(f"path outside deck: {resolved}")


def resolve_include(
    spec: str,
    *,
    slide_dir: Path | None = None,
    deck_root: Path | None = None,
) -> dict | None:
    """Resolve a Markdown include from the slide directory, then the deck root."""
    found = _locate(spec, slide_dir=slide_dir, deck_root=deck_root)
    if found is None or deck_root is None:
        return None
    return {
        "src": _src_for(found, deck_root),
        "text": found.read_text(encoding="utf-8"),
    }


def resolve_image(
    spec: str,
    *,
    slide_dir: Path | None = None,
    deck_root: Path | None = None,
) -> dict | None:
    """Resolve an image from the slide directory, then the deck root."""
    found = _locate(spec, slide_dir=slide_dir, deck_root=deck_root)
    if found is None or deck_root is None:
        return None
    width, height = png_size(found)
    return {
        "src": _src_for(found, deck_root),
        "abs": str(found.resolve()),
        "width": width,
        "height": height,
    }


def parse_table(body: str) -> tuple[list[str], list[list[tuple[str, bool]]]]:
    rows: list[list[tuple[str, bool]]] = []
    headers: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") and c for c in cells):
            continue
        if not headers:
            headers = cells
            continue
        parsed = []
        for cell in cells:
            hl = cell.startswith("!")
            parsed.append((cell[1:].strip() if hl else cell, hl))
        rows.append(parsed)
    return headers, rows


class PageSlugError(ValueError):
    """Slug is missing, duplicated, or not a page name."""


def slug_of(name: str) -> str:
    """``010-cover.md`` and ``cover.md`` both yield ``cover``."""
    match = PAGE_NAME.fullmatch(Path(name).name)
    if not match:
        raise PageSlugError(f"cannot parse slide name: {name}")
    return match.group(2)


def numbered_pages(slides_dir: Path) -> dict[str, Path]:
    """Map each slug to its ``NNN-slug.md`` file in ``slides_dir``."""
    found: dict[str, list[Path]] = {}
    if slides_dir.is_dir():
        for path in sorted(slides_dir.glob("[0-9][0-9][0-9]-*.md")):
            found.setdefault(slug_of(path.name), []).append(path)
    dupes = {slug: paths for slug, paths in found.items() if len(paths) > 1}
    if dupes:
        detail = "; ".join(
            f"{slug} ({', '.join(str(path) for path in paths)})"
            for slug, paths in sorted(dupes.items())
        )
        raise PageSlugError(f"duplicate slide slug in {slides_dir}: {detail}")
    return {slug: paths[0] for slug, paths in found.items()}


def resolve_page(slug: str, slides_dir: Path) -> Path:
    pages = numbered_pages(slides_dir)
    if slug not in pages:
        raise PageSlugError(f"missing slide file: {slides_dir / slug}.md")
    return pages[slug]


def ordered_pages(deck: config.Deck) -> list[Path]:
    """Return slide files in config order: filename auto, or ``[deck] sort``."""
    if deck.sort is not None:
        return pages_from_index(deck.slides, deck.sort)
    return auto_pages(deck.slides)


def auto_pages(slides_dir: Path) -> list[Path]:
    """Return ``NNN-slug.md`` files in ``slides_dir``, sorted by filename."""
    try:
        catalog = numbered_pages(slides_dir)
    except PageSlugError as exc:
        _fail(str(exc))
    paths = list(catalog.values())
    if not paths:
        _fail(f"no numbered slide files in {slides_dir}")
    return paths


def pages_from_index(slides_dir: Path, index: Path) -> list[Path]:
    """Load ``NNN-slug.md`` paths in the order listed under ``## Slides``."""
    if not index.is_file():
        _fail(f"missing slide index: {index}")
    text = index.read_text(encoding="utf-8")
    section = _SLIDES_HEADING.search(text)
    if not section:
        _fail(f"{index}: missing heading ## Slides")
    try:
        catalog = numbered_pages(slides_dir)
    except PageSlugError as exc:
        _fail(str(exc))
    paths: list[Path] = []
    seen: set[str] = set()
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", section.group(1)):
        rel = match.group(1).strip()
        try:
            slug = slug_of(Path(rel).name)
        except PageSlugError as exc:
            _fail(f"{index}: {exc}")
        path = catalog.get(slug)
        if path is None:
            _fail(f"{index}: slide link does not resolve: {rel}")
        if slug in seen:
            _fail(f"{index}: duplicate slide slug: {slug} ({path})")
        seen.add(slug)
        paths.append(path)
    if not paths:
        _fail(f"{index}: ## Slides list is empty")
    return paths


def git_describe(root: Path | None = None) -> str:
    """``git describe --always --dirty`` in the deck root, or ``unknown``."""
    resolved = (root if root is not None else config.deck_root()).resolve()
    cached = _GIT_DESCRIBE.get(resolved)
    if cached is None:
        cached = _read_git_describe(resolved)
        _GIT_DESCRIBE[resolved] = cached
    return cached


def _read_git_describe(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "describe", "--always", "--dirty"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown"
    text = (result.stdout or "").strip()
    return text if result.returncode == 0 and text else "unknown"


def page_stamp(index: int, total: int, version: str | None = None) -> str:
    ver = git_describe() if version is None else version
    return f"{ver} · {index:02d} / {total:02d}"


def load_deck(root: Path | None = None) -> dict:
    """Load the deck at ``root`` (or the configured deck root)."""
    root_resolved = config.deck_root() if root is None else Path(root).expanduser().resolve()
    deck = config.load_deck(root_resolved)
    paths = ordered_pages(deck)
    total = len(paths)
    version = git_describe(root_resolved)
    slides = []
    for index, path in enumerate(paths, start=1):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        meta = config.cover_overrides(root_resolved, path, meta)
        layout = meta.get("layout", "cards")
        cards, note = parse_cards(body, slide_dir=path.parent, deck_root=root_resolved)
        note_text = (note or {}).get("text") or None
        note_slot = (note or {}).get("slot") or ""
        headers, rows = parse_table(body)
        slides.append(
            {
                "file": path.name,
                "slug": slug_of(path.name),
                "index": index,
                "total": total,
                "version": version,
                "stamp": page_stamp(index, total, version),
                "layout": layout,
                "meta": meta,
                "cards": cards,
                "note": note_text,
                "note_slot": note_slot,
                "table": {
                    "headers": headers,
                    "rows": [[{"text": text, "hl": hl} for text, hl in row] for row in rows],
                }
                if headers
                else None,
            }
        )
    return {
        "name": deck.name,
        "title": deck.title,
        "total": total,
        "version": version,
        "slides": slides,
    }


def main() -> None:
    json.dump(load_deck(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
