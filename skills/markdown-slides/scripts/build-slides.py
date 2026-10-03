#!/usr/bin/env python3
"""Build a single-file HTML deck under build/<slides>/."""

from __future__ import annotations

import html
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import config
from embed_fonts import embedded_font_css
from md_html import render_markdown
from slide_model import (
    git_describe,
    ordered_pages,
    linkify_footer,
    normalize_image_fit,
    note_parts,
    page_stamp,
    parse_cards,
    parse_frontmatter,
    parse_table,
)


_DECK_PLACEHOLDER = "__DECK_NAME__"
_DEFAULT_FONT_HREF = (
    "https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800"
    "&family=Noto+Sans+SC:wght@400;500;700&family=Nunito:wght@400;600;700"
    "&family=IBM+Plex+Mono:wght@400;500&display=swap"
)
_FAVICON_FILES = ("favicon.svg", "favicon.ico", "favicon.png")
_FAVICON_TYPES = {
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".png": "image/png",
}


@dataclass
class _RenderState:
    root: Path
    version: str | None = None
    slide: Path | None = None
    asset_prefix: str = ""


_state: _RenderState | None = None


def _deck_root() -> Path:
    if _state is not None:
        return _state.root
    return config.deck_root()


def _parse_cards(body: str):
    """Parse cards using the slide directory, then the deck root."""
    slide = _state.slide if _state is not None else None
    slide_dir = slide.parent if slide is not None else None
    return parse_cards(body, slide_dir=slide_dir, deck_root=_deck_root())


def _js_string(value: str) -> str:
    """Escape ``value`` for placement inside a double-quoted JS string."""
    encoded = json.dumps(value, ensure_ascii=False)
    return encoded[1:-1]


def theme_font_href(theme_dir: Path) -> str:
    """Google Fonts stylesheet URL for a theme, or the Swiss Modern default."""
    path = theme_dir / "fonts.url"
    if path.is_file():
        href = path.read_text(encoding="utf-8").strip()
        if href:
            return href
    return _DEFAULT_FONT_HREF


def _asset_prefix(root: Path, dest: Path) -> str:
    """Prefix that walks from the HTML file back to the deck root."""
    rel = Path(os.path.relpath(root.resolve(), dest.parent.resolve())).as_posix()
    if rel in {".", ""}:
        return ""
    return rel + "/"


def deck_href(src: str) -> str:
    if not src or src.startswith(("http://", "https://", "data:", "#", "/")):
        return src
    prefix = _state.asset_prefix if _state is not None else ""
    return prefix + src


def favicon_link(root: Path) -> str:
    """Return an icon ``<link>`` when the deck root has a favicon file."""
    base = root.resolve()
    prefix = _state.asset_prefix if _state is not None else ""
    for name in _FAVICON_FILES:
        path = (base / name).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            continue
        if not path.is_file():
            continue
        mime = _FAVICON_TYPES.get(path.suffix.lower(), "image/png")
        href = html.escape(prefix + name, quote=True)
        return f'    <link rel="icon" href="{href}" type="{mime}">\n'
    return ""


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"==(.+?)==", r'<span class="accent">\1</span>', escaped)
    escaped = re.sub(r"`([^`]+)`", r'<span class="code">\1</span>', escaped)
    escaped = re.sub(
        r"\[([^\]]+?)\]\(([^)]+?)\)",
        lambda m: f'<a href="{html.escape(m.group(2))}" target="_blank">{m.group(1)}</a>',
        escaped,
    )
    escaped = escaped.replace("&lt;br&gt;", "<br>")
    return escaped


def render_note(note: str) -> str:
    """Convert note text with Markdown-style paragraphs and nested lists to HTML."""
    lines = note.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    def list_item_marker(line: str) -> tuple[int, str] | None:
        stripped = line.lstrip()
        for marker in ("- ", "* "):
            if stripped.startswith(marker):
                indent = len(line) - len(stripped)
                return (indent, stripped[len(marker) :])
        return None

    while i < n:
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue

        item = list_item_marker(line)
        if item is not None:
            stack: list[tuple[int, bool]] = []
            while i < n and lines[i].strip():
                current_item = list_item_marker(lines[i])
                if current_item is None:
                    break
                indent, content = current_item
                while stack and stack[-1][0] > indent:
                    out.append("</ul>")
                    stack.pop()
                if not stack or stack[-1][0] < indent:
                    out.append("<ul>")
                    stack.append((indent, True))
                out.append(f"<li>{inline(content)}</li>")
                i += 1
            while stack:
                out.append("</ul>")
                stack.pop()
        else:
            paras: list[str] = []
            while i < n and lines[i].strip():
                paras.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(paras))}</p>")

    return "".join(out)


TEXT_SIZES = ("s", "l", "xl", "xxl")


def text_size_class(value: str | None) -> str:
    """字号档位 s / l / xl / xxl 映射到 CSS 类；空或未知＝默认字号。"""
    token = (value or "").strip().lower()
    return f"text-{token}" if token in TEXT_SIZES else ""


MARKER_ON = {"on", "true", "1", "yes"}
MARKER_OFF = {"off", "false", "0", "no"}


def is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in MARKER_ON


def cards_for_html(cards: list[dict]) -> list[dict]:
    """If any card is html-only, HTML shows only those (full scroll report)."""
    only = [c for c in cards if is_truthy(c.get("html_only"))]
    return only if only else cards


def wants_marker(card: dict) -> bool:
    """列表要不要红方块项目符：`marker` 写了就听它，没写沿用旧推断（有 title、无 num）。"""
    token = (card.get("marker") or "").strip().lower()
    if token in MARKER_ON:
        return True
    if token in MARKER_OFF:
        return False
    return bool(card["title"]) and not card["num"]


def bullets_html(bullets: list[dict], marker: bool) -> str:
    """按 depth 嵌套：子列表放进上一级 li 里，而不是平铺成兄弟。"""
    cls = ' class="bullets"' if marker else ""
    parts = [f"<ul{cls}>"]
    depth = 0
    li_open = False
    for item in bullets:
        want = max(0, int(item.get("depth", 0)))
        while want > depth:
            if not li_open:
                parts.append("<li>")
            parts.append("<ul>")
            depth += 1
            li_open = False
        while want < depth:
            if li_open:
                parts.append("</li>")
            parts.append("</ul></li>")
            depth -= 1
            li_open = False
        if li_open:
            parts.append("</li>")
        parts.append(f"<li>{inline(item['text'])}")
        li_open = True
    while depth > 0:
        if li_open:
            parts.append("</li>")
        parts.append("</ul></li>")
        depth -= 1
        li_open = False
    if li_open:
        parts.append("</li>")
    parts.append("</ul>")
    return "".join(parts)


def card_html(card: dict, extra_style: str = "") -> str:
    classes = ["card"]
    if card["tone"] in {"filled", "red"}:
        classes.append(card["tone"])
    size_cls = text_size_class(card.get("size"))
    if size_cls:
        classes.append(size_cls)
    scroll_on = (card.get("scroll") or "").strip().lower() in {"on", "true", "1", "yes"}
    if scroll_on:
        classes.append("scroll")
    classes.append("reveal")
    styles = [extra_style] if extra_style else []
    weight = (card.get("weight") or "").strip()
    if weight:
        styles.append(f"flex: {weight}")
    height = (card.get("height") or "").strip()
    if height:
        styles.append(f"min-height: {html.escape(height)}")
    style = f' style="{"; ".join(styles)}"' if styles else ""
    if card.get("image"):
        img = card["image"]
        alt = html.escape(card.get("alt") or "")
        src = html.escape(deck_href(img["src"]))
        has_caption = bool(card["num"] or card["title"])
        if not has_caption:
            classes.append("card-image")
        image_fit = normalize_image_fit(card.get("image_fit"))
        if image_fit != "contain":
            classes.append(f"image-fit-{image_fit}")
        if image_fit in {"cover", "fill"}:
            img_styles = ["display:block;"]
        elif image_fit == "width":
            img_styles = ["display:block; width:100%; margin:0 auto;"]
            if card.get("image_height"):
                img_styles.append(f"height:{html.escape(card['image_height'])}")
                img_styles.append("object-fit:fill")
                img_styles.append("max-height:none")
            else:
                img_styles.append("height:auto")
        elif image_fit == "height":
            img_styles = ["display:block; height:100%; width:auto; margin:0 auto;"]
        else:
            img_styles = ["display:block; margin:0 auto;"]
        if card.get("image_max_height"):
            img_styles.append(f"max-height:{html.escape(card['image_max_height'])}")
        if card.get("image_max_width"):
            img_styles.append(f"max-width:{html.escape(card['image_max_width'])}")
        img_style = f' style="{"; ".join(s.rstrip(";") for s in img_styles)};"'
        img_class = f' class="image-fit-{image_fit}"' if image_fit != "contain" else ""
        parts = [f'<div class="{" ".join(classes)}"{style}>']
        if card["num"]:
            parts.append(f'<div class="num">{inline(card["num"])}</div>')
        if card["title"]:
            parts.append(f"<h3>{inline(card['title'])}</h3>")
        parts.append(f'<img src="{src}" alt="{alt}"{img_class}{img_style}>')
        parts.append("</div>")
        return "".join(parts)
    parts = [f'<div class="{" ".join(classes)}"{style}>']
    inline_head = (card.get("inline_head") or "").strip().lower() in {"on", "true", "1", "yes"}
    if inline_head and (card["num"] or card["title"]):
        head_parts = ['<div class="card-head">']
        if card["num"]:
            head_parts.append(f'<div class="num">{inline(card["num"])}</div>')
        if card["title"]:
            head_parts.append(f"<h3>{inline(card['title'])}</h3>")
        head_parts.append("</div>")
        parts.append("".join(head_parts))
    else:
        if card["num"]:
            parts.append(f'<div class="num">{inline(card["num"])}</div>')
        if card["title"]:
            parts.append(f"<h3>{inline(card['title'])}</h3>")
    if card.get("markdown"):
        parts.append(f'<div class="md-body">{render_markdown(card["markdown"])}</div>')
    else:
        for para in card["paragraphs"]:
            parts.append(f"<p>{inline(para)}</p>")
        if card["bullets"]:
            parts.append(bullets_html(card["bullets"], wants_marker(card)))
    parts.append("</div>")
    # consecutive paragraphs: add spacing on later p via CSS? existing CSS doesn't space p+p.
    html_out = "".join(parts)
    html_out = html_out.replace("</p><p>", '</p><p style="margin-top:12px;">')
    return html_out


def resolve_overline_style(text: str, style: str | None = None) -> str:
    raw = str(style or "auto").strip().lower() or "auto"
    if raw == "cn":
        return "cjk"
    if raw in {"cjk", "en"}:
        return raw
    return "en" if all(ord(c) < 128 for c in text) else "cjk"


def render_overline(meta: dict) -> str:
    text = meta.get("overline", "")
    if not text:
        return ""
    style = resolve_overline_style(text, meta.get("overline_style", "auto"))
    return f'<div class="overline {style} reveal">{inline(text)}</div>'


def render_title_block(meta: dict) -> str:
    title = meta.get("title", "").replace("\\n", "<br>")
    return f'<h2 class="reveal">{inline(title)}</h2>' if meta.get("layout") != "title" else ""


def render_summary(meta: dict, style: str = "") -> str:
    summary = meta.get("summary")
    if not summary:
        return ""
    attr = f' style="{style}"' if style else ""
    return f'<p class="summary reveal"{attr}>{inline(summary)}</p>'


def render_foot(
    meta: dict,
    index: int,
    total: int,
    version: str | None = None,
    foot_note: str | None = None,
) -> str:
    if version is None and _state is not None and _state.version is not None:
        version = _state.version
    if foot_note:
        if meta.get("footer"):
            warn(":::note foot 与 footer: 并存，已忽略 footer:")
        # 与通栏 :::note 一致：优先 note_size，否则继承页上 text_size（.slide 的 --card-body）
        size_cls = text_size_class(meta.get("note_size"))
        note_cls = " ".join(t for t in ["foot-note", size_cls] if t)
        left = f'<span class="{note_cls}">{render_note(foot_note)}</span>'
    else:
        left = f"<span>{inline(linkify_footer(meta.get('footer', '')))}</span>"
    stamp = html.escape(page_stamp(index, total, version))
    return f'<div class="foot reveal">{left}' f'<span class="stamp">{stamp}</span></div>'


def foot_from_body(meta: dict, body: str, index: int, total: int) -> str:
    _, note = _parse_cards(body)
    _, foot_note = note_parts(note)
    return render_foot(meta, index, total, foot_note=foot_note).strip()


def wrap_slide(inner: str, classes: str, first: bool, meta: dict | None = None) -> str:
    tokens = ["slide", *classes.split(), text_size_class((meta or {}).get("text_size"))]
    if first:
        tokens.append("active")
        tokens.append("visible")
    cls = " ".join(t for t in tokens if t)
    return (
        f'<section class="{cls}">\n'
        f'                <div class="red-bar"></div>\n'
        f'                <div class="frame">\n{inner}\n'
        f"                </div>\n"
        f"            </section>"
    )


def indent_inner(parts: list[str]) -> str:
    return "\n".join("                    " + p if p else "" for p in parts)


def render_title(meta: dict, body: str, index: int, total: int, first: bool) -> str:
    title = meta.get("title", "").replace("\\n", "<br>")
    title_style = meta.get("title_size")
    h1_attr = f' style="font-size:{html.escape(title_style)};"' if title_style else ""
    badge_cls = "title-square reveal"
    badge_style = meta.get("badge_style", "")
    badge_attr = f' style="{html.escape(badge_style)}"' if badge_style else ""
    eyebrow = meta.get("eyebrow", "").strip()
    wk = f'<div class="wk reveal">{inline(eyebrow)}</div>' if eyebrow else ""
    badge_text = meta.get("badge_text", "")
    en_cls = "en long" if len(badge_text) > 6 else "en"
    cover_session = ""
    if meta.get("presenter") or meta.get("presented_at"):
        lines: list[str] = []
        if meta.get("presenter"):
            lines.append(
                '<div class="session-line">'
                '<span class="lbl">Speaker</span>'
                f'<span class="val cn">{inline(meta["presenter"])}</span>'
                "</div>"
            )
        if meta.get("presented_at"):
            lines.append(
                '<div class="session-line">'
                '<span class="lbl">When</span>'
                f'<span class="val when">{inline(meta["presented_at"])}</span>'
                "</div>"
            )
        cover_session = '<div class="cover-session reveal">' + "".join(lines) + "</div>"
    inner = indent_inner(
        [
            '<div class="meta-row reveal">',
            f'    <span class="cn">{inline(meta.get("meta_left", ""))}</span>',
            f'    <span>{inline(meta.get("meta_right", ""))}</span>',
            "</div>",
            wk,
            f'<h1 class="reveal"{h1_attr}>{inline(title)}</h1>',
            f'<p class="sub reveal">{inline(meta.get("subtitle", ""))}</p>',
            f'<div class="{badge_cls}"{badge_attr}><div class="badge-pair"><span class="label">{inline(meta.get("badge_label", ""))}</span><span class="{en_cls}">{inline(badge_text)}</span></div></div>',
            cover_session,
            foot_from_body(meta, body, index, total),
        ]
    )
    return wrap_slide(inner, "title-slide grid-bg", first, meta)


def render_section(meta: dict, body: str, index: int, total: int, first: bool) -> str:
    inner = indent_inner(
        [
            f'<div class="big reveal">{inline(meta.get("number", ""))}</div>',
            f'<h2 class="reveal">{inline(meta.get("title", "").replace("\\n", "<br>"))}</h2>',
            render_summary(meta).strip(),
            foot_from_body(meta, body, index, total),
        ]
    )
    return wrap_slide(inner, "section-slide grid-bg", first, meta)


def grid_class(columns: str) -> str:
    return {"1": "grid-1", "2": "grid-2", "3": "grid-3", "4": "grid-4", "23": "grid-23"}.get(
        columns, "grid-2"
    )


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def width_tracks(meta: dict) -> list[str]:
    """把 frontmatter 的 widths 变成 grid track 列表。

    百分比按权重处理：写成 minmax(0, Nfr)，列宽才会在扣掉 gap 之后再分配，
    而且宽内容（图片、长代码）不会把列撑破。其他写法（fr、px）原样透传。
    """
    widths = [w.strip() for w in meta.get("widths", "").split(",") if w.strip()]
    return [re.sub(r"^([\d.]+)%$", r"minmax(0, \1fr)", w) for w in widths]


def _is_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in ("true", "1", "yes", "on")


def render_cards(meta: dict, body: str, index: int, total: int, first: bool) -> str:
    cards, note = _parse_cards(body)
    html_only_mode = any(is_truthy(c.get("html_only")) for c in cards)
    cards = cards_for_html(cards)
    band_note, foot_note = note_parts(note)
    # html-only 全文卡独占舞台：通栏 + 不叠 PPTX 用的摘要 note
    if html_only_mode:
        band_note = None
        columns = "1"
    else:
        columns = meta.get("columns", "2")
    grid = grid_class(columns)
    text_cards = [c for c in cards if not c.get("image")]
    image_cards = [c for c in cards if c.get("image")]
    images_inline = _is_true(meta.get("images_inline"))
    images_fill = bool(cards) and not text_cards
    if images_fill or images_inline:
        grid_cards = cards
        band_images = []
    else:
        grid_cards = text_cards
        band_images = image_cards
    grid_cls = grid
    # images_inline 时图留在网格里，通栏 note 直接跟在网格下，不要包 split-band
    use_band = bool(band_images) or (bool(band_note) and not images_inline)
    has_scroll = any(
        (c.get("scroll") or "").strip().lower() in {"on", "true", "1", "yes"} for c in cards
    )
    if has_scroll:
        grid_style = "flex:1; min-height:0; align-content:stretch;"
    elif images_inline:
        grid_style = "flex:1; align-content:start;"
    else:
        grid_style = (
            "flex:0 0 auto;" if (images_fill or band_images) else "flex:1; align-content:start;"
        )
    tracks = width_tracks(meta)
    if tracks:
        # widths 只能描述一行：列数对不上就说不清第二行该怎么分。
        if len(tracks) >= 2 and len(tracks) == len(grid_cards):
            grid_style += f" grid-template-columns:{' '.join(tracks)};"
        else:
            warn(
                f"cards 页 widths 有 {len(tracks)} 列，网格里是 {len(grid_cards)} 张卡，已忽略 widths"
            )
    parts = [
        render_overline(meta),
        f'<h2 class="reveal">{inline(meta.get("title", "").replace("\\n", "<br>"))}</h2>',
        render_summary(meta),
    ]

    def append_band_note() -> None:
        if not band_note:
            return
        note_cls = " ".join(
            t for t in ["card", "note", text_size_class(meta.get("note_size")), "reveal"] if t
        )
        parts.append(f'<div class="{note_cls}">{render_note(band_note)}</div>')

    if use_band:
        parts.append('<div class="split-band">')
        if grid_cards:
            parts.append(f'<div class="{grid_cls}" style="{grid_style}">')
            parts.extend(card_html(c) for c in grid_cards)
            parts.append("</div>")
        parts.extend(card_html(c) for c in band_images)
        append_band_note()
        parts.append("</div>")
    else:
        parts.append(f'<div class="{grid_cls}" style="{grid_style}">')
        parts.extend(card_html(c) for c in grid_cards)
        parts.append("</div>")
        append_band_note()
    parts.append(render_foot(meta, index, total, foot_note=foot_note).strip())
    return wrap_slide(indent_inner([p for p in parts if p]), "", first, meta)


def render_split(meta: dict, body: str, index: int, total: int, first: bool) -> str:
    cards, note = _parse_cards(body)
    _, foot_note = note_parts(note)
    text_cards = [c for c in cards if not c.get("image")]
    image_cards = [c for c in cards if c.get("image")]
    parts = [
        render_overline(meta),
        f'<h2 class="reveal">{inline(meta.get("title", "").replace("\\n", "<br>"))}</h2>',
        render_summary(meta),
    ]
    if image_cards:
        parts.append('<div class="split-band">')
        parts.append('<div class="grid-2">')
        parts.extend(card_html(c) for c in text_cards)
        parts.append("</div>")
        parts.extend(card_html(c) for c in image_cards)
        parts.append("</div>")
    else:
        parts.append('<div class="grid-2" style="flex:1;">')
        parts.extend(card_html(c) for c in text_cards)
        parts.append("</div>")
    parts.append(render_foot(meta, index, total, foot_note=foot_note).strip())
    return wrap_slide(indent_inner([p for p in parts if p]), "", first, meta)


def render_stack_split(meta: dict, body: str, index: int, total: int, first: bool) -> str:
    cards, note = _parse_cards(body)
    _, foot_note = note_parts(note)
    slots: dict[str, list[dict]] = {"left": [], "mid": [], "right": []}
    for i, card in enumerate(cards):
        slot = card.get("slot") or ("left" if i == 0 else "right")
        slots.setdefault(slot if slot in slots else "right", []).append(card)
    tracks = width_tracks(meta)
    used = tuple(name for name in ("left", "mid", "right") if slots[name])
    if len(tracks) >= 2 and len(tracks) == len(used):
        grid = f'<div class="grid-stack" style="grid-template-columns:{" ".join(tracks)}; flex:1; min-height:0;">'
        order = used
    elif slots["mid"]:
        grid = '<div class="grid-stack" style="grid-template-columns:1.05fr 0.95fr 1fr; flex:1; min-height:0;">'
        order = ("left", "mid", "right")
    else:
        grid = '<div class="grid-23" style="flex:1; min-height:0;">'
        order = ("left", "right")
    parts = [
        render_overline(meta),
        f'<h2 class="reveal">{inline(meta.get("title", "").replace("\\n", "<br>"))}</h2>',
        render_summary(meta),
        grid,
        *(
            f'<div class="stack-col">{"".join(card_html(c) for c in slots[name])}</div>'
            for name in order
        ),
        "</div>",
        render_foot(meta, index, total, foot_note=foot_note).strip(),
    ]
    return wrap_slide(indent_inner([p for p in parts if p]), "", first, meta)


def table_html(
    meta: dict,
    headers: list[str],
    rows: list[list[tuple[str, bool]]],
    extra_class: str = "",
) -> str:
    widths = [w.strip() for w in meta.get("widths", "").split(",") if w.strip()]
    thead = "<thead><tr>"
    for i, h in enumerate(headers):
        w = f' style="width:{html.escape(widths[i])}"' if i < len(widths) else ""
        thead += f"<th{w}>{inline(h)}</th>"
    thead += "</tr></thead>"
    tbody = "<tbody>"
    for row in rows:
        tbody += "<tr>"
        for text, hl in row:
            cls = ' class="hl"' if hl else ""
            tbody += f"<td{cls}>{inline(text)}</td>"
        tbody += "</tr>"
    tbody += "</tbody>"
    extra = f" {extra_class}" if extra_class else ""
    return f'<table class="dense reveal{extra}">{thead}{tbody}</table>'


def render_table(meta: dict, body: str, index: int, total: int, first: bool) -> str:
    headers, rows = parse_table(body)
    _, note = _parse_cards(body)
    _, foot_note = note_parts(note)
    summary_after = meta.get("summary_after", "")
    parts = [
        render_overline(meta),
        f'<h2 class="reveal">{inline(meta.get("title", "").replace("\\n", "<br>"))}</h2>',
        render_summary(meta) if not summary_after else "",
        table_html(meta, headers, rows),
        f'<p class="summary reveal" style="margin:22px 0 0;">{inline(summary_after)}</p>'
        if summary_after
        else "",
        render_foot(meta, index, total, foot_note=foot_note).strip(),
    ]
    return wrap_slide(indent_inner([p for p in parts if p]), "", first, meta)


def render_table_cards(meta: dict, body: str, index: int, total: int, first: bool) -> str:
    cards, note = _parse_cards(body)
    _, foot_note = note_parts(note)
    headers, rows = parse_table(body)
    grid = grid_class(meta.get("columns", "3"))
    parts = [
        render_overline(meta),
        f'<h2 class="reveal">{inline(meta.get("title", "").replace("\\n", "<br>"))}</h2>',
        render_summary(meta),
        '<div class="manifesto-stack">',
    ]
    if meta.get("table_title"):
        parts.append(f'<h3 class="manifesto-section reveal">{inline(meta["table_title"])}</h3>')
    if headers:
        parts.append(table_html(meta, headers, rows, extra_class="manifesto-table"))
    if meta.get("cards_title"):
        parts.append(f'<h3 class="manifesto-section reveal">{inline(meta["cards_title"])}</h3>')
    parts.append(f'<div class="{grid} manifesto-cards">')
    parts.extend(card_html(c) for c in cards)
    parts.append("</div></div>")
    parts.append(render_foot(meta, index, total, foot_note=foot_note).strip())
    return wrap_slide(indent_inner([p for p in parts if p]), "", first, meta)


RENDERERS = {
    "title": render_title,
    "section": render_section,
    "cards": render_cards,
    "split": render_split,
    "stack-split": render_stack_split,
    "table": render_table,
    "table-cards": render_table_cards,
}


WIDTH_AWARE_LAYOUTS = {"cards", "stack-split", "table", "table-cards"}


def render_page(path: Path, index: int, total: int) -> str:
    global _state
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    root = _deck_root()
    meta = config.cover_overrides(root, path, meta)
    owned = _state is None
    if owned:
        _state = _RenderState(root=root)
    previous = _state.slide
    _state.slide = path
    try:
        layout = meta.get("layout", "cards")
        renderer = RENDERERS.get(layout)
        if not renderer:
            sys.exit(f"{path.name}: 未知 layout {layout}")
        if meta.get("widths") and layout not in WIDTH_AWARE_LAYOUTS:
            warn(
                f"{path.name}: layout {layout} 不读 widths"
                f"（只有 {'、'.join(sorted(WIDTH_AWARE_LAYOUTS))} 读）"
            )
        return renderer(meta, body, index, total, index == 1)
    finally:
        if owned:
            _state = None
        else:
            _state.slide = previous


def build(output: Path | None = None) -> None:
    global _state
    root = config.deck_root()
    deck = config.load_deck(root)
    dest = config.output_paths(root).html if output is None else Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pages = ordered_pages(deck)
    total = len(pages)
    version = git_describe(root)
    _state = _RenderState(root=root, version=version, asset_prefix=_asset_prefix(root, dest))
    try:
        slides = "\n\n".join(render_page(path, i, total) for i, path in enumerate(pages, start=1))
        css = (deck.theme_dir / "deck.css").read_text(encoding="utf-8")
        js = (deck.theme_dir / "deck.js").read_text(encoding="utf-8")
        if _DECK_PLACEHOLDER not in js:
            sys.exit(
                f"{deck.theme_dir / 'deck.js'} is missing the " f"{_DECK_PLACEHOLDER} placeholder"
            )
        js = js.replace(_DECK_PLACEHOLDER, _js_string(deck.name))
        rev = html.escape(version, quote=True)
        title = html.escape(deck.title)
        icon = favicon_link(root)
        font_css = embedded_font_css(theme_font_href(deck.theme_dir))
        doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="revision" content="{rev}">
    <title>{title}</title>
{icon}    <script>
    (function () {{
      if (window.self !== window.top) return;
      var m = document.querySelector('meta[name="revision"]');
      var rev = m ? m.content : '';
      if (!rev) return;
      var key = '_v=' + encodeURIComponent(rev);
      if (location.search.indexOf(key) === -1) {{
        var url = location.origin + location.pathname + '?' + key + location.hash;
        location.replace(url);
      }}
    }})();
    </script>
    <!-- git describe: {rev} -->
    <style>
{font_css}
{css}
    </style>
</head>
<body>
    <div class="edit-hotzone" aria-hidden="true"></div>
    <button class="edit-toggle" id="editToggle" title="编辑模式 (E)">✎</button>
    <div class="progress-track"><div class="progress-bar" id="progressBar"></div></div>

    <div class="deck-viewport">
        <main class="deck-stage" id="deckStage">

{slides}

        </main>
    </div>

    <script>
{js}
    </script>
</body>
</html>
"""
        dest.write_text(doc, encoding="utf-8")
        try:
            shown = dest.relative_to(root)
        except ValueError:
            shown = dest
        print(f"wrote {shown} ({total} slides, {version})")
    finally:
        _state = None


if __name__ == "__main__":
    build()
