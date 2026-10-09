"""HTML builder writes a multi-page site and a one-page ebook."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import config as config_module
from test_config import write_book, write_meta

SKILL_ROOT = Path(__file__).resolve().parent.parent
BUILD_PAGES = SKILL_ROOT / "scripts" / "build-pages.py"


def _run_build(deck: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DECK_ROOT"] = str(deck)
    env["DOC"] = "pages"
    return subprocess.run(
        [sys.executable, str(BUILD_PAGES), *extra],
        cwd=str(SKILL_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )


class TestBuildPages(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict(
            os.environ,
            {"DOC": "", "DECK_ROOT": ""},
            clear=False,
        )
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_example_book_titles(self):
        with patch.dict(
            os.environ,
            {"DECK_ROOT": str(SKILL_ROOT), "DOC": "examples/pages"},
        ):
            proc = subprocess.run(
                [sys.executable, str(BUILD_PAGES), "--clean"],
                cwd=str(SKILL_ROOT),
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = SKILL_ROOT / "build" / "examples" / "pages"
        site = out / "pages"
        index = (site / "index.html").read_text(encoding="utf-8")
        intro = (site / "01-intro.html").read_text(encoding="utf-8")
        ebook = (out / "markdown-pages-examples.html").read_text(encoding="utf-8")
        self.assertIn("Markdown Pages Examples", index)
        self.assertIn("Intro", index)
        self.assertIn("01-intro.html", index)
        self.assertNotIn("01-intro.md", index)
        self.assertNotIn("English self-test", index)
        self.assertNotIn("English self-test", ebook)
        self.assertIn("Intro", intro)
        self.assertIn("chapter-nav", intro)
        self.assertIn("Markdown Pages Examples", ebook)
        self.assertIn("Intro", ebook)
        self.assertIn("Next", ebook)
        self.assertIn("<style>", ebook)
        self.assertTrue(".chapter-nav" in ebook or "@media print" in ebook)
        self.assertNotIn('href="assets/book.css"', ebook)
        self.assertIn('href="../assets/book.css"', index)
        self.assertIn('href="../assets/book.css"', intro)
        self.assertFalse((out / "index.html").is_file())
        self.assertTrue((out / "assets" / "book.css").is_file())
        css = (out / "assets" / "book.css").read_text(encoding="utf-8")
        self.assertIn(".chapter-nav", css)
        self.assertIn("@media print", css)
        for html in (index, intro, ebook):
            self.assertNotIn("fonts.googleapis.com", html)
            self.assertNotIn("fonts.gstatic.com", html)
            self.assertNotIn("cdn.jsdelivr.net", html)
            self.assertIn("assets/mathjax/tex-chtml.js", html)
            self.assertIn('name="revision"', html)
            self.assertIn('location.protocol === "file:"', html)
            self.assertIn("location.replace(url)", html)
            self.assertIn('"_v="', html)
        self.assertTrue((out / "assets" / "mathjax" / "tex-chtml.js").is_file())

    def test_temp_deck_via_make_html(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "my-book", "My Book")
            (deck / "pages" / "README.md").write_text(
                "# Home\n\nSee [Intro](01-intro.md).\n",
                encoding="utf-8",
            )
            (deck / "pages" / "01-intro.md").write_text(
                "# Intro\n\n## Details\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["make", "html", f"DECK_ROOT={deck}", "DOC=pages"],
                cwd=str(SKILL_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            out = deck / "build" / "pages"
            site = out / "pages"
            index = (site / "index.html").read_text(encoding="utf-8")
            intro = (site / "01-intro.html").read_text(encoding="utf-8")
            ebook = (out / "my-book.html").read_text(encoding="utf-8")
            self.assertNotIn("Home", index)
            self.assertIn("My Book", index)
            self.assertIn("Intro", index)
            self.assertIn('href="01-intro.html"', index)
            self.assertIn("Intro", intro)
            self.assertIn("Details", intro)
            self.assertIn("page-toc", intro)
            self.assertNotIn("Home", ebook)
            self.assertIn("Intro", ebook)
            self.assertIn('href="#ch-01-intro"', ebook)
            self.assertIn("<style>", ebook)
            self.assertTrue(".chapter-nav" in ebook or "@media print" in ebook)
            self.assertNotIn('href="assets/book.css"', ebook)
            self.assertIn('content="unknown"', index)
            self.assertIn('location.protocol === "file:"', ebook)

    def test_one_page_omits_trailing_chapter_nav(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "nav-book", "Nav Book")
            (deck / "pages" / "01-intro.md").write_text(
                "# Intro\n\nSee [Next](02-next.md) in the body.\n\n" "下一篇：[Next](02-next.md)\n",
                encoding="utf-8",
            )
            (deck / "pages" / "02-next.md").write_text(
                "# Next\n\nDone.\n\n返回首页：[Home](README.md)\n",
                encoding="utf-8",
            )
            proc = _run_build(deck)
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            site = deck / "build" / "pages" / "pages"
            intro = (site / "01-intro.html").read_text(encoding="utf-8")
            nxt = (site / "02-next.html").read_text(encoding="utf-8")
            ebook = (deck / "build" / "pages" / "nav-book.html").read_text(encoding="utf-8")
            self.assertIn("See", intro)
            self.assertIn("02-next.html", intro)
            self.assertIn('class="chapter-nav"', intro)
            self.assertNotIn("下一篇", intro)
            self.assertIn("首页", nxt)
            self.assertNotIn("返回首页", nxt)
            self.assertNotIn("下一篇", ebook)
            self.assertNotIn("返回首页", ebook)
            self.assertIn('href="#ch-02-next"', ebook)
            self.assertIn("Done.", ebook)

    def test_readme_and_agents_are_not_compiled(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "skip-book", "Skip Book")
            (deck / "pages" / "README.md").write_text(
                "# Repo summary\n\nUNIQUE_README_SENTENCE\n",
                encoding="utf-8",
            )
            (deck / "pages" / "AGENTS.md").write_text(
                "# For agents\n\nUNIQUE_AGENTS_SENTENCE\n",
                encoding="utf-8",
            )
            (deck / "pages" / "01-intro.md").write_text(
                "# Intro\n\nSee [home](README.md) and [agents](AGENTS.md).\n",
                encoding="utf-8",
            )
            proc = _run_build(deck)
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            site = deck / "build" / "pages" / "pages"
            built = "\n".join(path.read_text(encoding="utf-8") for path in site.glob("*.html"))
            ebook = (deck / "build" / "pages" / "skip-book.html").read_text(encoding="utf-8")
            intro = (site / "01-intro.html").read_text(encoding="utf-8")
            self.assertNotIn("UNIQUE_README_SENTENCE", built)
            self.assertNotIn("UNIQUE_AGENTS_SENTENCE", built)
            self.assertNotIn("UNIQUE_README_SENTENCE", ebook)
            self.assertNotIn("UNIQUE_AGENTS_SENTENCE", ebook)
            self.assertNotIn("ch-readme", ebook)
            self.assertIn('href="index.html"', intro)
            self.assertIn("AGENTS.md", intro)
            self.assertNotIn("AGENTS.html", intro)
            self.assertFalse((site / "README.html").exists())
            self.assertFalse((site / "AGENTS.html").exists())

    def test_home_toc_follows_index_marker(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "toc-book", "TOC Book")
            (deck / "pages" / "index.md").write_text(
                "# Welcome\n\nBefore the list.\n\n[TOC]\n\nAfter the list.\n\n" "```\n[TOC]\n```\n",
                encoding="utf-8",
            )
            (deck / "pages" / "01-intro.md").write_text(
                "# Intro\n\n[TOC]\n\n## Details\n\n### More\n",
                encoding="utf-8",
            )
            proc = _run_build(deck)
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            site = deck / "build" / "pages" / "pages"
            index = (site / "index.html").read_text(encoding="utf-8")
            intro = (site / "01-intro.html").read_text(encoding="utf-8")
            ebook = (deck / "build" / "pages" / "toc-book.html").read_text(encoding="utf-8")
            self.assertLess(index.index("Before the list."), index.index('class="home-toc"'))
            self.assertLess(index.index('class="home-toc"'), index.index("After the list."))
            self.assertIn('href="01-intro.html"', index)
            self.assertIn('href="01-intro.html#details"', index)
            self.assertIn('class="depth-2"', index)
            self.assertIn('class="depth-3"', index)
            self.assertIn(">More</a>", index)
            self.assertLess(index.index(">Details</a>"), index.index(">More</a>"))
            self.assertIn("<code>[TOC]\n</code>", index)
            self.assertNotIn('class="home-toc"', intro)
            self.assertIn("[TOC]", intro)
            self.assertLess(ebook.index("Before the list."), ebook.index('class="home-toc"'))
            self.assertLess(ebook.index('class="home-toc"'), ebook.index("After the list."))
            self.assertIn('href="#ch-01-intro"', ebook)
            self.assertIn('href="#01-intro--details"', ebook)
            self.assertIn('href="#01-intro--more"', ebook)
            self.assertEqual(ebook.count('class="home-toc"'), 1)

    def test_missing_markdown_matches_source(self):
        code = r"""
import importlib.abc
import importlib.machinery
import runpy
import sys

class FailLoader(importlib.abc.Loader):
    def create_module(self, spec):
        raise ModuleNotFoundError("No module named 'markdown'")

    def exec_module(self, module):
        raise ModuleNotFoundError("No module named 'markdown'")

class FailFinder:
    def find_spec(self, fullname, path, target=None):
        if fullname.split(".")[0] == "markdown":
            return importlib.machinery.ModuleSpec(fullname, FailLoader())
        return None

sys.meta_path.insert(0, FailFinder())
for name in list(sys.modules):
    if name == "markdown" or name.startswith("markdown."):
        del sys.modules[name]
runpy.run_path(sys.argv[1], run_name="__main__")
"""
        proc = subprocess.run(
            [sys.executable, "-c", code, str(BUILD_PAGES)],
            cwd=str(SKILL_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ensure_venv.py", proc.stderr)
        self.assertIn("Missing dependency: markdown", proc.stderr)

    def test_empty_book_exits(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_meta(deck / "pages", "empty-book")
            proc = _run_build(deck)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("numbered chapter", proc.stderr)
            self.assertIn("not compiled", proc.stderr)

    def test_config_output_matches_written_ebook(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "notes", "note-book", "Notes")
            with patch.dict(os.environ, {"DECK_ROOT": str(deck), "DOC": "notes"}):
                paths = config_module.output_paths(deck)
                proc = subprocess.run(
                    [sys.executable, str(BUILD_PAGES)],
                    cwd=str(SKILL_ROOT),
                    env={**os.environ, "DECK_ROOT": str(deck), "DOC": "notes"},
                    capture_output=True,
                    text=True,
                )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(paths.html.is_file())
            self.assertIn("Notes", paths.html.read_text(encoding="utf-8"))


def _load_builder():
    name = "build_pages"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, BUILD_PAGES)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestPdfExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = _load_builder()

    def test_missing_browser_exits_with_message(self):
        with tempfile.TemporaryDirectory() as raw:
            html = Path(raw) / "book.html"
            html.write_text("<html><body><p>hi</p></body></html>", encoding="utf-8")
            pdf = Path(raw) / "book.pdf"
            real_import = __import__

            def no_playwright(name, *args, **kwargs):
                if name == "playwright" or name.startswith("playwright."):
                    raise ImportError("No module named 'playwright'")
                return real_import(name, *args, **kwargs)

            with (
                patch.object(self.builder, "_chrome_candidates", return_value=[]),
                patch("builtins.__import__", side_effect=no_playwright),
                patch.object(self.builder.sys, "stderr", new=StringIO()) as err,
                self.assertRaises(SystemExit) as ctx,
            ):
                self.builder.html_to_pdf(html, pdf)
            self.assertEqual(ctx.exception.code, 1)
            message = err.getvalue()
            self.assertIn("Playwright", message)
            self.assertIn("Chrome", message)
            self.assertFalse(pdf.is_file())

    def test_make_pdf_writes_nonempty_file(self):
        if not self.builder.pdf_browser_available():
            self.skipTest("no Playwright Chromium or system Chrome")
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "my-book", "My Book")
            proc = subprocess.run(
                ["make", "pdf", f"DECK_ROOT={deck}", "DOC=pages"],
                cwd=str(SKILL_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            out = deck / "build" / "pages"
            ebook = out / "my-book.html"
            pdf = out / "my-book.pdf"
            self.assertTrue(ebook.is_file())
            self.assertTrue(pdf.is_file())
            self.assertGreater(pdf.stat().st_size, 0)
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
