#!/usr/bin/env python3
"""Compile a Markdown book to a multi-page HTML site and a one-page ebook.

Requires the skill ``.venv`` with ``requirements.txt`` (``markdown``).
Run ``python3 scripts/ensure_venv.py`` or ``make html`` from this skill.

The book root is the selected pages directory (flat, no docs/). The
multi-page site is ``build/<pages>/pages/``. Shared CSS and MathJax stay
in ``build/<pages>/assets/``. The one-file HTML and PDF are
``build/<pages>/<name>.html`` and ``.pdf``.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import markdown
    from markdown.extensions.toc import slugify as md_slugify
except ImportError:
    print(
        "Missing dependency: markdown\n"
        "  From the skill root: python3 scripts/ensure_venv.py\n"
        "  Then rebuild with make html (uses .venv/bin/python)",
        file=sys.stderr,
    )
    sys.exit(1)

import config
from embed_fonts import embedded_font_css, font_href

MD_LINK_RE = re.compile(
    r"\[([^\]]+)\]\(([^)]+\.md)(#[^)]*)?\)",
    re.IGNORECASE,
)
_END_NAV_LINE = re.compile(r"^(?:下一篇[:：].*|返回首页(?:[:：].*)?|\[返回首页\]\([^)]*\))$")
HEADING_RE = re.compile(
    r"<h([23])\s+[^>]*id=\"([^\"]+)\"[^>]*>(.*?)</h\1>",
    re.IGNORECASE | re.DOTALL,
)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
TAG_RE = re.compile(r"<[^>]+>")
STEM_CHAPTER_RE = re.compile(r"^(\d+)")
_STALE_CHAPTER_HTML = re.compile(r"^[0-9]{2,3}-[a-z0-9-]+\.html$")
_SITE_ASSET_PREFIX = "../"
H2_REL_NUM_RE = re.compile(r"^(##)\s+(?!\d+\.\d+)(\d+)\.\s+", re.MULTILINE)
H3_REL_NUM_RE = re.compile(
    r"^(###)\s+(?!\d+\.\d+\.\d+)(\d+)\.(\d+)\.?\s+",
    re.MULTILINE,
)
_ID_ATTR_RE = re.compile(
    r'(<h[23]\s+)([^>]*\bid=")([^"]+)(")',
    re.IGNORECASE,
)
_HREF_HASH_RE = re.compile(r'href="#([^"]+)"')
_QUOTE_MARK_RE = re.compile(r"^>[ \t]*\[!quote\][ \t]*\\?[ \t]*$")


@dataclass
class Chapter:
    path: Path
    stem: str
    title: str

    @property
    def html_name(self) -> str:
        return f"{self.stem}.html"


def templates_dir() -> Path:
    """Return the skill ``templates/`` directory next to this engine."""
    here = Path(__file__).resolve().parent
    if here.name == "markdown-pages":
        nested = here.parent.parent / "skills" / "markdown-pages" / "templates"
        if (nested / "book.css").is_file():
            return nested
        return here.parent.parent / "templates"
    return here.parent / "templates"


def book_css() -> str:
    path = templates_dir() / "book.css"
    if not path.is_file():
        sys.exit(f"missing stylesheet: {path}")
    return path.read_text(encoding="utf-8")


def slugify(value: str, separator: str = "-") -> str:
    return md_slugify(value, separator)


def extract_title(md_text: str, fallback: str) -> str:
    match = H1_RE.search(md_text)
    return match.group(1).strip() if match else fallback


def strip_tags(s: str) -> str:
    return TAG_RE.sub("", s)


def chapter_num_from_stem(stem: str) -> int | None:
    match = STEM_CHAPTER_RE.match(stem)
    return int(match.group(1)) if match else None


def _map_outside_fences(md_text: str, transform) -> str:
    parts = re.split(r"(^```.*?^```)", md_text, flags=re.M | re.S)
    return "".join(part if i % 2 else transform(part) for i, part in enumerate(parts))


def apply_chapter_section_numbers(md_text: str, chapter: int) -> str:
    """Prefix relative section numbers with the chapter index at build time."""

    def transform(chunk: str) -> str:
        chunk = H2_REL_NUM_RE.sub(rf"\1 {chapter}.\2. ", chunk)
        chunk = H3_REL_NUM_RE.sub(rf"\1 {chapter}.\2.\3 ", chunk)
        return chunk

    return _map_outside_fences(md_text, transform)


def prepare_chapter_md(
    md_text: str,
    pages_dir: Path,
    stem: str,
    *,
    one_page: bool = False,
) -> str:
    chapter = chapter_num_from_stem(stem)
    if chapter is not None:
        md_text = apply_chapter_section_numbers(md_text, chapter)
    if one_page:
        return rewrite_md_links_one_page(strip_one_page_end_nav(md_text), pages_dir)
    return rewrite_md_links(md_text, pages_dir)


def strip_one_page_end_nav(md_text: str) -> str:
    """Drop trailing next-chapter and home links from a one-file article.

    The one-file HTML and the PDF printed from it are one article. Lines at
    the end of a chapter that only say ``下一篇：`` or link back with
    ``返回首页`` stay in the multi-page site and are omitted here.
    """
    lines = md_text.splitlines()
    changed = False
    while lines and not lines[-1].strip():
        lines.pop()
        changed = True
    while lines and _END_NAV_LINE.fullmatch(lines[-1].strip()):
        lines.pop()
        changed = True
        while lines and not lines[-1].strip():
            lines.pop()
    if not changed:
        return md_text
    return "\n".join(lines) + ("\n" if lines else "")


def rewrite_md_links(md_text: str, pages_dir: Path) -> str:
    """Rewrite .md links to .html when the target is under the book directory."""

    def repl(match: re.Match[str]) -> str:
        label, target, frag = match.group(1), match.group(2), match.group(3) or ""
        if target.startswith(("http://", "https://", "mailto:")):
            return match.group(0)
        resolved = (pages_dir / target).resolve()
        try:
            resolved.relative_to(pages_dir.resolve())
        except ValueError:
            return match.group(0)
        stem = Path(target).name
        if stem.lower().endswith(".md"):
            stem = stem[:-3]
        return f"[{label}]({stem}.html{frag})"

    return MD_LINK_RE.sub(repl, md_text)


def rewrite_md_links_one_page(md_text: str, pages_dir: Path) -> str:
    """Rewrite .md links to in-page anchors for the one-page ebook."""

    def repl(match: re.Match[str]) -> str:
        label, target, frag = match.group(1), match.group(2), match.group(3) or ""
        if target.startswith(("http://", "https://", "mailto:")):
            return match.group(0)
        resolved = (pages_dir / target).resolve()
        try:
            resolved.relative_to(pages_dir.resolve())
        except ValueError:
            return match.group(0)
        stem = Path(target).name
        if stem.lower().endswith(".md"):
            stem = stem[:-3]
        if stem.lower() == "readme":
            stem = "readme"
        if frag:
            frag_id = frag[1:] if frag.startswith("#") else frag
            return f"[{label}](#{stem}--{frag_id})"
        return f"[{label}](#ch-{stem})"

    return MD_LINK_RE.sub(repl, md_text)


def prefix_heading_ids(body_html: str, stem: str) -> str:
    """Prefix h2/h3 ids with ``{stem}--`` and rewrite matching in-page hrefs."""
    old_ids: set[str] = set()

    def id_repl(match: re.Match[str]) -> str:
        old = match.group(3)
        old_ids.add(old)
        return f"{match.group(1)}{match.group(2)}{stem}--{old}{match.group(4)}"

    out = _ID_ATTR_RE.sub(id_repl, body_html)

    def href_repl(match: re.Match[str]) -> str:
        hid = match.group(1)
        if hid in old_ids and not hid.startswith(f"{stem}--"):
            return f'href="#{stem}--{hid}"'
        return match.group(0)

    return _HREF_HASH_RE.sub(href_repl, out)


def _strip_blockquote_prefix(line: str) -> str:
    if line.endswith("\r\n"):
        nl, core = "\r\n", line[:-2]
    elif line.endswith("\n"):
        nl, core = "\n", line[:-1]
    else:
        nl, core = "", line
    if core.startswith("> "):
        core = core[2:]
    elif core.startswith(">"):
        core = core[1:]
    return core + nl


def promote_statement_quotes(md_text: str) -> str:
    """Turn a leading `> [!quote]` into a statement blockquote."""
    lines = md_text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        stripped = lines[i].rstrip("\r\n")
        at_quote_start = i == 0 or lines[i - 1].strip() == ""
        if _QUOTE_MARK_RE.match(stripped) and at_quote_start:
            i += 1
            body: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                body.append(_strip_blockquote_prefix(lines[i]))
                i += 1
            inner = "".join(body).strip("\n")
            out.append('<blockquote class="quote" markdown="1">\n\n' f"{inner}\n\n</blockquote>\n")
            continue
        out.append(lines[i])
        i += 1
    return "".join(out)


def unescape_gfm_lt(md_text: str) -> str:
    """mdformat writes \\< for a literal less-than. Python-Markdown keeps the slash."""

    def fix_outside_fences(chunk: str) -> str:
        out: list[str] = []
        i = 0
        n = len(chunk)
        while i < n:
            if chunk[i] == "`":
                j = i + 1
                while j < n and chunk[j] == "`":
                    j += 1
                ticks = chunk[i:j]
                end = chunk.find(ticks, j)
                if end == -1:
                    out.append(chunk[i:])
                    break
                out.append(chunk[i : end + len(ticks)])
                i = end + len(ticks)
                continue
            if chunk.startswith("\\<", i) and (i == 0 or chunk[i - 1] != "\\"):
                out.append("<")
                i += 2
                continue
            out.append(chunk[i])
            i += 1
        return "".join(out)

    parts = re.split(r"(^```.*?^```)", md_text, flags=re.M | re.S)
    return "".join(part if i % 2 else fix_outside_fences(part) for i, part in enumerate(parts))


def md_to_html(md_text: str) -> str:
    return markdown.markdown(
        promote_statement_quotes(unescape_gfm_lt(md_text)),
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "nl2br",
            "sane_lists",
            "md_in_html",
        ],
        extension_configs={
            "toc": {
                "permalink": False,
                "slugify": slugify,
                "toc_depth": "2-3",
            }
        },
        output_format="html5",
    )


def page_toc_from_html(body_html: str) -> str:
    items: list[tuple[int, str, str]] = []
    for match in HEADING_RE.finditer(body_html):
        level = int(match.group(1))
        hid = match.group(2)
        title = html.unescape(strip_tags(match.group(3))).strip()
        if not title:
            continue
        items.append((level, hid, title))
    if not items:
        return ""
    lis = []
    for level, hid, title in items:
        depth = "depth-2" if level == 2 else "depth-3"
        lis.append(
            f'<li class="{depth}"><a href="#{html.escape(hid)}">' f"{html.escape(title)}</a></li>"
        )
    return (
        '<nav class="page-toc" aria-label="本页目录">\n'
        "<h2>本页目录</h2>\n"
        f"<ul>\n{''.join(lis)}\n</ul>\n"
        "</nav>\n"
    )


def book_toc_html(chapters: list[Chapter], current: str | None) -> str:
    items = []
    for chapter in chapters:
        cls = ' class="active"' if chapter.stem == current else ""
        items.append(
            f'<li><a href="{html.escape(chapter.html_name)}"{cls}>'
            f"{html.escape(chapter.title)}</a></li>"
        )
    return (
        '<nav class="sidebar" aria-label="全书目录">\n'
        "<h2>全书目录</h2>\n"
        f'<ul class="book-toc">\n{"".join(items)}\n</ul>\n'
        "</nav>\n"
    )


def nav_links(
    chapters: list[Chapter],
    index: int | None,
    *,
    for_index: bool = False,
) -> str:
    prev_a = '<span class="disabled">上一章</span>'
    next_a = '<span class="disabled">下一章</span>'
    if for_index:
        if chapters:
            next_a = f'<a href="{html.escape(chapters[0].html_name)}">下一章 →</a>'
    elif index is not None:
        if index > 0:
            prev_ch = chapters[index - 1]
            prev_a = (
                f'<a href="{html.escape(prev_ch.html_name)}">' f"← {html.escape(prev_ch.title)}</a>"
            )
        if index + 1 < len(chapters):
            next_ch = chapters[index + 1]
            next_a = (
                f'<a href="{html.escape(next_ch.html_name)}">' f"{html.escape(next_ch.title)} →</a>"
            )
    home = '<a href="index.html">首页</a>'
    return f'<div class="nav-links">{prev_a}{home}{next_a}</div>'


def mathjax_script_tag(asset_prefix: str = "") -> str:
    """Return MathJax config + local script tags, or empty if vendor missing."""
    vendor = config.skill_root() / "vendor" / "mathjax" / "tex-chtml.js"
    if not vendor.is_file():
        sys.stderr.write("markdown-pages: vendor/mathjax missing; math will not render\n")
        return ""
    src = f"{asset_prefix}assets/mathjax/tex-chtml.js"
    return f"""  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['\\\\(', '\\\\)'], ['$', '$']],
        displayMath: [['\\\\[', '\\\\]'], ['$$', '$$']]
      }}
    }};
  </script>
  <script defer src="{src}"></script>
"""


def shell_page(
    *,
    title: str,
    book_title: str,
    body_main: str,
    book_toc: str,
    page_toc: str,
    top_nav: str,
    footer_nav: str,
    is_index: bool = False,
    inline_css: bool = False,
    brand_href: str = "index.html",
    asset_prefix: str = "",
) -> str:
    wrap_cls = "content-wrap index-wrap" if is_index else "content-wrap"
    page_toc_block = "" if is_index else page_toc
    font_css = embedded_font_css(
        font_href(templates_dir()),
        enabled=config.webfont_enabled(config.deck_root()),
    )
    if inline_css:
        style_block = f"<style>\n{font_css}\n{book_css()}\n</style>"
    else:
        style_block = (
            f"<style>\n{font_css}</style>\n"
            f'<link rel="stylesheet" href="{asset_prefix}assets/book.css" />'
        )
    mathjax = mathjax_script_tag(asset_prefix)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  {style_block}
{mathjax}</head>
<body>
  <header class="site-header">
    <a class="brand" href="{html.escape(brand_href)}">{html.escape(book_title)}</a>
    {top_nav}
  </header>
  <div class="layout">
    {book_toc}
    <div class="{wrap_cls}">
      {body_main}
      {page_toc_block}
    </div>
  </div>
  <footer class="site-footer">
    {footer_nav}
    <p>由 <code>scripts/build-pages.py</code> 从 Markdown 编译</p>
  </footer>
</body>
</html>
"""


def book_toc_one_page(
    *,
    chapters: list[Chapter],
    include_readme: bool,
    readme_title: str,
) -> str:
    items: list[str] = []
    if include_readme:
        items.append(f'<li><a href="#ch-readme">{html.escape(readme_title)}</a></li>')
    for chapter in chapters:
        items.append(
            f'<li><a href="#ch-{html.escape(chapter.stem)}">'
            f"{html.escape(chapter.title)}</a></li>"
        )
    return (
        '<nav class="sidebar" aria-label="全书目录">\n'
        "<h2>全书目录</h2>\n"
        f'<ul class="book-toc">\n{"".join(items)}\n</ul>\n'
        "</nav>\n"
    )


def _render_one_page_section(
    *,
    stem: str,
    raw_md: str,
    pages_dir: Path,
) -> str:
    body = md_to_html(prepare_chapter_md(raw_md, pages_dir, stem, one_page=True))
    body = prefix_heading_ids(body, stem)
    return f'<article id="ch-{html.escape(stem)}" class="chapter">\n' f"{body}\n" "</article>\n"


def load_chapters(pages_dir: Path) -> list[Chapter]:
    chapters: list[Chapter] = []
    for path in config.list_chapters(pages_dir):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        title = extract_title(text, path.stem)
        chapters.append(Chapter(path=path, stem=path.stem, title=title))
    return chapters


def chapter_list_html(chapters: list[Chapter]) -> str:
    items = []
    for i, chapter in enumerate(chapters, 1):
        items.append(
            f'<li><span class="num">{i:02d}</span>'
            f'<a href="{html.escape(chapter.html_name)}">'
            f"{html.escape(chapter.title)}</a></li>"
        )
    return f'<ol class="chapter-list">\n{"".join(items)}\n</ol>\n'


def ensure_assets(html_dir: Path, *, refresh: bool) -> None:
    assets_dir = html_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css_path = assets_dir / "book.css"
    if refresh or not css_path.is_file():
        css_path.write_text(book_css(), encoding="utf-8")
    mathjax_src = config.skill_root() / "vendor" / "mathjax"
    mathjax_dst = assets_dir / "mathjax"
    marker = mathjax_dst / "tex-chtml.js"
    if mathjax_src.is_dir() and (mathjax_src / "tex-chtml.js").is_file():
        if refresh or not marker.is_file():
            if mathjax_dst.exists():
                shutil.rmtree(mathjax_dst)
            shutil.copytree(mathjax_src, mathjax_dst)


def _prev_next_plain(chapters: list[Chapter], index: int) -> str:
    prev = (
        f'<a href="{html.escape(chapters[index - 1].html_name)}">'
        f"← {html.escape(chapters[index - 1].title)}</a>"
        if index > 0
        else '<span class="disabled">← 上一章</span>'
    )
    nxt = (
        f'<a href="{html.escape(chapters[index + 1].html_name)}">'
        f"{html.escape(chapters[index + 1].title)} →</a>"
        if index + 1 < len(chapters)
        else '<span class="disabled">下一章 →</span>'
    )
    return f'{prev}<a href="index.html">首页</a>{nxt}'


def write_chapter_page(
    *,
    chapter: Chapter,
    chapters: list[Chapter],
    index: int,
    pages_dir: Path,
    html_dir: Path,
    book_title: str,
) -> None:
    raw = chapter.path.read_text(encoding="utf-8")
    body = md_to_html(prepare_chapter_md(raw, pages_dir, chapter.stem))
    page_toc = page_toc_from_html(body)
    top = nav_links(chapters, index)
    footer = (
        f'<nav class="chapter-nav" aria-label="章节导航">'
        f"{_prev_next_plain(chapters, index)}</nav>"
    )
    article = f'<article class="chapter">\n{body}\n{footer}\n</article>\n'
    page = shell_page(
        title=f"{chapter.title} · {book_title}",
        book_title=book_title,
        body_main=article,
        book_toc=book_toc_html(chapters, chapter.stem),
        page_toc=page_toc,
        top_nav=top,
        footer_nav=top,
        is_index=False,
        asset_prefix=_SITE_ASSET_PREFIX,
    )
    (html_dir / chapter.html_name).write_text(page, encoding="utf-8")


def write_index_page(
    *,
    chapters: list[Chapter],
    pages_dir: Path,
    html_dir: Path,
    book_title: str,
) -> None:
    readme_path = pages_dir / "README.md"
    if readme_path.is_file():
        readme_md = rewrite_md_links(readme_path.read_text(encoding="utf-8"), pages_dir)
        readme_body = md_to_html(readme_md)
    else:
        readme_body = f"<h1>{html.escape(book_title)}</h1>\n"

    index_article = (
        f'<article class="index">\n{readme_body}\n'
        f"<h2>章节</h2>\n{chapter_list_html(chapters)}</article>\n"
    )
    index_nav = nav_links(chapters, None, for_index=True)
    index_html = shell_page(
        title=book_title,
        book_title=book_title,
        body_main=index_article,
        book_toc=book_toc_html(chapters, None),
        page_toc="",
        top_nav=index_nav,
        footer_nav=index_nav,
        is_index=True,
        asset_prefix=_SITE_ASSET_PREFIX,
    )
    (html_dir / "index.html").write_text(index_html, encoding="utf-8")


def require_sources(pages_dir: Path, chapters: list[Chapter]) -> None:
    readme = pages_dir / "README.md"
    if not chapters and not readme.is_file():
        print(
            f"no README.md or numbered chapter markdown in {pages_dir}",
            file=sys.stderr,
        )
        sys.exit(1)


def build_one_page_book(
    pages_dir: Path,
    *,
    output: Path,
    title: str,
    chapters: list[Chapter] | None = None,
) -> Path:
    """Compile README + numbered chapters into one self-contained HTML file."""
    if chapters is None:
        chapters = load_chapters(pages_dir)
    require_sources(pages_dir, chapters)

    readme_path = pages_dir / "README.md"
    include_readme = readme_path.is_file()
    readme_title = title
    sections: list[str] = []

    if include_readme:
        readme_raw = readme_path.read_text(encoding="utf-8")
        readme_title = extract_title(readme_raw, title)
        sections.append(
            _render_one_page_section(
                stem="readme",
                raw_md=readme_raw,
                pages_dir=pages_dir,
            )
        )

    for chapter in chapters:
        sections.append(
            _render_one_page_section(
                stem=chapter.stem,
                raw_md=chapter.path.read_text(encoding="utf-8"),
                pages_dir=pages_dir,
            )
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    body_main = "\n".join(sections)
    sidebar = book_toc_one_page(
        chapters=chapters,
        include_readme=include_readme,
        readme_title=readme_title,
    )
    if include_readme:
        top_nav = (
            '<div class="nav-links">'
            '<a href="#ch-readme">顶部</a>'
            '<span class="disabled">单页全书</span>'
            "</div>"
        )
        brand = "#ch-readme"
    else:
        top_nav = (
            '<div class="nav-links">'
            f'<a href="#ch-{html.escape(chapters[0].stem)}">顶部</a>'
            '<span class="disabled">单页全书</span>'
            "</div>"
        )
        brand = f"#ch-{chapters[0].stem}"

    page = shell_page(
        title=f"{title} · 单页",
        book_title=title,
        body_main=body_main,
        book_toc=sidebar,
        page_toc="",
        top_nav=top_nav,
        footer_nav=top_nav,
        is_index=True,
        inline_css=True,
        brand_href=brand,
    )
    output.write_text(page, encoding="utf-8")
    print(f"Built one-page → {output}")
    return output


def _chrome_candidates() -> list[Path]:
    return [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/google-chrome-stable"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
    ]


def pdf_browser_available() -> bool:
    """True when Playwright Chromium or a system Chrome binary can print PDF."""
    if any(path.is_file() for path in _chrome_candidates()):
        return True
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            exe = playwright.chromium.executable_path
            return bool(exe and Path(exe).is_file())
    except Exception:  # noqa: BLE001 — probe only
        return False


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """Render a local HTML file to PDF via Playwright or Chrome headless."""
    html_path = html_path.resolve()
    pdf_path = pdf_path.resolve()
    if not html_path.is_file():
        print(f"HTML not found: {html_path}", file=sys.stderr)
        sys.exit(1)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    uri = html_path.as_uri()

    # Prefer Playwright when Chromium is available (waits for fonts/CDN).
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(uri, wait_until="networkidle", timeout=120_000)
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "16mm",
                    "bottom": "16mm",
                    "left": "14mm",
                    "right": "14mm",
                },
            )
            browser.close()
        return
    except Exception as exc:  # noqa: BLE001 — fall back to Chrome CLI
        playwright_err = exc

    chrome = next((candidate for candidate in _chrome_candidates() if candidate.is_file()), None)
    if chrome is not None:
        cmd = [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            uri,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not pdf_path.is_file():
            print(proc.stderr or proc.stdout or "chrome print failed", file=sys.stderr)
            sys.exit(1)
        return

    print(
        "PDF export needs Playwright (chromium) or Chrome/Chromium.\n"
        f"  Playwright error: {playwright_err}\n"
        "  pip install playwright && python3 -m playwright install chromium\n"
        "  or install Google Chrome",
        file=sys.stderr,
    )
    sys.exit(1)


def build_book_pdf(
    pages_dir: Path,
    *,
    html_path: Path,
    pdf_path: Path,
    title: str,
    chapters: list[Chapter] | None = None,
) -> Path:
    """Build one-page HTML then PDF under ``build/<rel>/``."""
    build_one_page_book(pages_dir, output=html_path, title=title, chapters=chapters)
    html_to_pdf(html_path, pdf_path)
    print(f"Built PDF → {pdf_path}")
    return pdf_path


def build_single_page(
    md_path: Path,
    *,
    output: Path,
    title: str | None = None,
) -> Path:
    """Compile one Markdown file to a standalone HTML page (page TOC only)."""
    md_path = md_path.resolve()
    if not md_path.is_file():
        print(f"file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    pages_dir = md_path.parent
    raw = md_path.read_text(encoding="utf-8")
    page_title = title or extract_title(raw, md_path.stem)
    body = md_to_html(prepare_chapter_md(raw, pages_dir, md_path.stem))
    page_toc = page_toc_from_html(body)
    out_dir = output.parent
    ensure_assets(out_dir, refresh=True)

    article = f'<article class="chapter">\n{body}\n</article>\n'
    empty_book = (
        '<nav class="sidebar" aria-label="全书目录">\n'
        "<h2>单页</h2>\n"
        f'<ul class="book-toc"><li><a class="active" href="{html.escape(output.name)}">'
        f"{html.escape(page_title)}</a></li></ul>\n</nav>\n"
    )
    top = (
        f'<div class="nav-links"><span class="disabled">上一章</span>'
        f'<a href="{html.escape(output.name)}">本页</a>'
        f'<span class="disabled">下一章</span></div>'
    )
    page = shell_page(
        title=page_title,
        book_title=page_title,
        body_main=article,
        book_toc=empty_book,
        page_toc=page_toc,
        top_nav=top,
        footer_nav=top,
        is_index=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"Built 1 page → {output}")
    return output


def remove_legacy_site_html(artifact_dir: Path, ebook_name: str) -> None:
    """Drop multi-page HTML left beside the one-file ebook by older builds."""
    if not artifact_dir.is_dir():
        return
    for path in artifact_dir.iterdir():
        if not path.is_file() or path.name == ebook_name:
            continue
        if path.name == "index.html" or _STALE_CHAPTER_HTML.fullmatch(path.name):
            path.unlink()


def build_site(
    *,
    pages_dir: Path,
    artifact_dir: Path,
    book_title: str,
    clean: bool,
    only: str | None,
    one_page_path: Path | None,
) -> None:
    chapters = load_chapters(pages_dir)
    require_sources(pages_dir, chapters)
    site_dir = artifact_dir / "pages"

    if clean and artifact_dir.exists():
        shutil.rmtree(artifact_dir)
    if one_page_path is not None:
        remove_legacy_site_html(artifact_dir, one_page_path.name)
    site_dir.mkdir(parents=True, exist_ok=True)
    ensure_assets(artifact_dir, refresh=only is None)

    if only:
        key = only.removesuffix(".md").removesuffix(".html")
        match = next(
            (chapter for chapter in chapters if chapter.stem == key or chapter.path.name == only),
            None,
        )
        if match is None:
            print(f"chapter not found: {only}", file=sys.stderr)
            print(
                "available: " + ", ".join(chapter.stem for chapter in chapters),
                file=sys.stderr,
            )
            sys.exit(1)
        idx = chapters.index(match)
        write_chapter_page(
            chapter=match,
            chapters=chapters,
            index=idx,
            pages_dir=pages_dir,
            html_dir=site_dir,
            book_title=book_title,
        )
        if not (site_dir / "index.html").is_file():
            write_index_page(
                chapters=chapters,
                pages_dir=pages_dir,
                html_dir=site_dir,
                book_title=book_title,
            )
        print(f"Built 1 page → {site_dir / match.html_name}")
        return

    write_index_page(
        chapters=chapters,
        pages_dir=pages_dir,
        html_dir=site_dir,
        book_title=book_title,
    )
    for index, chapter in enumerate(chapters):
        write_chapter_page(
            chapter=chapter,
            chapters=chapters,
            index=index,
            pages_dir=pages_dir,
            html_dir=site_dir,
            book_title=book_title,
        )
    print(f"Built {len(chapters)} chapters → {site_dir}")
    if one_page_path is not None:
        build_one_page_book(
            pages_dir,
            output=one_page_path,
            title=book_title,
            chapters=chapters,
        )


def build() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a Markdown book to build/<pages>/pages/ plus "
            "build/<pages>/<name>.html. Requires skill .venv "
            "(python3 scripts/ensure_venv.py)"
        )
    )
    parser.add_argument(
        "--deck-root",
        type=Path,
        help="deck root (default: DECK_ROOT or this skill)",
    )
    parser.add_argument(
        "--doc",
        help="book directory relative to the deck root (DOC)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="remove existing build/<pages>/ before writing",
    )
    parser.add_argument(
        "--only",
        metavar="STEM",
        help="rebuild one numbered chapter (stem or filename)",
    )
    parser.add_argument(
        "--page",
        type=Path,
        metavar="MARKDOWN",
        help="build a single Markdown file to standalone HTML",
    )
    parser.add_argument(
        "--one-page",
        action="store_true",
        help="write only the one-page ebook (skip the multi-page site)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="build one-page HTML then PDF (Playwright Chromium or Chrome)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output path for --page / --one-page / --pdf",
    )
    parser.add_argument(
        "--title",
        help="override book/page title",
    )
    args = parser.parse_args()

    modes = sum(
        [
            args.page is not None,
            bool(args.one_page),
            bool(args.pdf),
            args.only is not None,
        ]
    )
    if modes > 1:
        print(
            "use only one of --page, --one-page, --pdf, or --only",
            file=sys.stderr,
        )
        sys.exit(2)

    root = config.deck_root()
    book = config.load_book(root)
    paths = config.output_paths(root)
    artifact_dir = paths.html.parent
    book_title = args.title or book.title

    if args.page is not None:
        page = args.page if args.page.is_absolute() else (root / args.page)
        dest = args.output
        if dest is None:
            dest = artifact_dir / f"{page.stem}.html"
        elif not dest.is_absolute():
            dest = root / dest
        build_single_page(page, output=dest.resolve(), title=args.title)
        return

    if args.one_page:
        dest = args.output
        if dest is None:
            dest = paths.html
        elif not dest.is_absolute():
            dest = root / dest
        build_one_page_book(
            book.pages,
            output=dest.resolve(),
            title=book_title,
        )
        return

    if args.pdf:
        dest = args.output
        if dest is None:
            dest = paths.pdf
        elif not dest.is_absolute():
            dest = root / dest
        build_book_pdf(
            book.pages,
            html_path=paths.html,
            pdf_path=dest.resolve(),
            title=book_title,
        )
        return

    build_site(
        pages_dir=book.pages,
        artifact_dir=artifact_dir,
        book_title=book_title,
        clean=args.clean,
        only=args.only,
        one_page_path=None if args.only else paths.html,
    )


if __name__ == "__main__":
    build()
