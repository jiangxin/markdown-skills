#!/usr/bin/env python3
"""Vendor Google Fonts CSS and woff2 files into data URIs.

A render-blocking <link> to fonts.googleapis.com waits until the CSS
returns. Offline, that stalls first paint until the browser times out.
The HTML build inlines the stylesheet and font files instead.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

import config

_URL = re.compile(r"""url\((['"]?)(https://fonts\.gstatic\.com[^)'"]+)\1\)""")
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_TIMEOUT = 20
_UNVERIFIED_SSL = False
_UNVERIFIED_WARNED = False


def cache_dir(href: str, root: Path | None = None) -> Path:
    digest = hashlib.sha256(href.encode("utf-8")).hexdigest()[:16]
    base = (root or config.skill_root()) / ".cache" / "fonts" / digest
    return base


def embedded_font_css(href: str, *, skill: Path | None = None) -> str:
    """Return @font-face CSS with data URIs, or a skip comment.

    Set MARKDOWN_SLIDES_EMBED_FONTS=0 to skip the download (tests).
    A failed fetch uses a previous cache, then system fonts.
    """
    href = (href or "").strip()
    if not href:
        return "/* webfonts: no fonts.url */\n"
    if os.environ.get("MARKDOWN_SLIDES_EMBED_FONTS", "1").strip() in {"0", "false", "no"}:
        return "/* webfonts: skipped (MARKDOWN_SLIDES_EMBED_FONTS=0) */\n"
    cached = cache_dir(href, skill) / "embedded.css"
    if cached.is_file():
        return cached.read_text(encoding="utf-8")
    try:
        css = _inline(href, fetch=_http_get)
    except (OSError, urllib.error.URLError, TimeoutError, ValueError) as err:
        sys.stderr.write(
            f"markdown-slides: could not vendor Google Fonts ({err}); using system fonts\n"
        )
        return "/* webfonts: vendor failed; system fonts */\n"
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(css, encoding="utf-8")
    (cached.parent / "source.url").write_text(href + "\n", encoding="utf-8")
    return css


def _inline(href: str, fetch) -> str:
    sheet = fetch(href).decode("utf-8")
    if "fonts.gstatic.com" not in sheet and "@font-face" not in sheet:
        raise ValueError("Google Fonts CSS did not contain @font-face rules")

    def repl(match: re.Match[str]) -> str:
        url = match.group(2)
        payload = fetch(url)
        mime = _mime(url, payload)
        encoded = base64.b64encode(payload).decode("ascii")
        return f"url(data:{mime};base64,{encoded})"

    inlined = _URL.sub(repl, sheet)
    if "fonts.gstatic.com" in inlined or "fonts.googleapis.com" in inlined:
        raise ValueError("could not inline every Google Fonts url()")
    return inlined


def _mime(url: str, payload: bytes) -> str:
    lower = url.lower()
    if lower.endswith(".woff2") or payload[:4] == b"wOF2":
        return "font/woff2"
    if lower.endswith(".woff") or payload[:4] == b"wOFF":
        return "font/woff"
    if lower.endswith(".ttf"):
        return "font/ttf"
    return "application/octet-stream"


def _http_get(url: str) -> bytes:
    global _UNVERIFIED_SSL, _UNVERIFIED_WARNED
    request = urllib.request.Request(url, headers={"User-Agent": _UA})

    def open_url(unverified: bool):
        kwargs: dict = {"timeout": _TIMEOUT}
        if unverified:
            kwargs["context"] = ssl._create_unverified_context()
        return urllib.request.urlopen(request, **kwargs)

    try:
        with open_url(_UNVERIFIED_SSL) as response:
            return response.read()
    except urllib.error.URLError as err:
        reason = str(err.reason) if getattr(err, "reason", None) else str(err)
        if _UNVERIFIED_SSL or ("CERTIFICATE_VERIFY_FAILED" not in reason and "SSL" not in reason):
            raise
        _UNVERIFIED_SSL = True
        if not _UNVERIFIED_WARNED:
            sys.stderr.write("markdown-slides: font download using unverified TLS\n")
            _UNVERIFIED_WARNED = True
        with open_url(True) as response:
            return response.read()


def main() -> None:
    """Pre-warm the font cache for every templates/*/fonts.url."""
    skill = config.skill_root()
    templates = skill / "templates"
    os.environ.pop("MARKDOWN_SLIDES_EMBED_FONTS", None)
    for fonts in sorted(templates.glob("*/fonts.url")):
        href = fonts.read_text(encoding="utf-8").strip()
        sys.stderr.write("vendor %s\n" % fonts.parent.name)
        css = embedded_font_css(href, skill=skill)
        sys.stderr.write("  %s bytes\n" % format(len(css), ","))


if __name__ == "__main__":
    main()
