#!/usr/bin/env python3
"""Minimal Markdown → HTML for included survey docs (no third-party deps)."""

from __future__ import annotations

import html
import re

_LINK = re.compile(r"\[([^\]]+?)\]\(([^)]+?)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_HR = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
_TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


def inline_md(text: str) -> str:
    """Escape then apply bold / code / links (order matches slide inline())."""
    escaped = html.escape(text)
    escaped = _BOLD.sub(r"<strong>\1</strong>", escaped)
    escaped = _CODE.sub(r'<span class="code">\1</span>', escaped)
    escaped = _LINK.sub(
        lambda m: f'<a href="{html.escape(m.group(2))}" target="_blank">{m.group(1)}</a>',
        escaped,
    )
    return escaped


def _split_row(line: str) -> list[str]:
    body = line.strip().strip("|")
    return [c.strip() for c in body.split("|")]


def render_markdown(text: str) -> str:
    """Render a GFM-ish subset: headings, quotes, hr, tables, paragraphs, lists."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    def flush_para(buf: list[str]) -> None:
        if not buf:
            return
        out.append(f"<p>{inline_md(' '.join(buf))}</p>")
        buf.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            i += 1
            continue

        hm = _HEADING.match(stripped)
        if hm:
            level = len(hm.group(1))
            out.append(f"<h{level}>{inline_md(hm.group(2))}</h{level}>")
            i += 1
            continue

        if _HR.match(stripped):
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            quote: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f'<blockquote><p>{inline_md(" ".join(quote))}</p></blockquote>')
            continue

        if stripped.startswith("|") and i + 1 < n and _TABLE_SEP.match(lines[i + 1].strip()):
            headers = _split_row(stripped)
            i += 2
            rows: list[list[str]] = []
            while i < n and lines[i].strip().startswith("|"):
                if _TABLE_SEP.match(lines[i].strip()):
                    i += 1
                    continue
                rows.append(_split_row(lines[i].strip()))
                i += 1
            thead = "".join(f"<th>{inline_md(h)}</th>" for h in headers)
            body_rows = []
            for row in rows:
                cells = list(row) + [""] * max(0, len(headers) - len(row))
                body_rows.append(
                    "<tr>"
                    + "".join(f"<td>{inline_md(c)}</td>" for c in cells[: len(headers)])
                    + "</tr>"
                )
            out.append(
                f'<table class="md-table"><thead><tr>{thead}</tr></thead>'
                f'<tbody>{"".join(body_rows)}</tbody></table>'
            )
            continue

        if stripped.startswith(("- ", "* ")):
            items: list[str] = []
            while i < n and lines[i].strip().startswith(("- ", "* ")):
                items.append(lines[i].strip()[2:].strip())
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline_md(it)}</li>" for it in items) + "</ul>")
            continue

        para: list[str] = []
        while i < n:
            s = lines[i].strip()
            if (
                s == ""
                or _HEADING.match(s)
                or _HR.match(s)
                or s.startswith(">")
                or s.startswith("|")
                or s.startswith(("- ", "* "))
            ):
                break
            para.append(s)
            i += 1
        flush_para(para)

    return "\n".join(out)
