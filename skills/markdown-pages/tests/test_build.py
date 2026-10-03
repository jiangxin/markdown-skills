"""HTML builder writes a multi-page site and a one-page ebook."""

import os
import subprocess
import sys
import tempfile
import unittest
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
    env["SLIDES"] = "pages"
    env["PAGES"] = ""
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
            {"SLIDES": "", "PAGES": "", "DECK_ROOT": ""},
            clear=False,
        )
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_example_book_titles(self):
        with patch.dict(
            os.environ,
            {"DECK_ROOT": str(SKILL_ROOT), "SLIDES": "examples/pages", "PAGES": ""},
        ):
            proc = subprocess.run(
                [sys.executable, str(BUILD_PAGES), "--clean"],
                cwd=str(SKILL_ROOT),
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = SKILL_ROOT / "build" / "examples" / "pages"
        index = (out / "index.html").read_text(encoding="utf-8")
        intro = (out / "01-intro.html").read_text(encoding="utf-8")
        ebook = (out / "markdown-pages-examples.html").read_text(encoding="utf-8")
        self.assertIn("Markdown Pages Examples", index)
        self.assertIn("Intro", index)
        self.assertIn("01-intro.html", index)
        self.assertNotIn("01-intro.md", index)
        self.assertIn("Intro", intro)
        self.assertIn("chapter-nav", intro)
        self.assertIn("Markdown Pages Examples", ebook)
        self.assertIn("Intro", ebook)
        self.assertIn("Next", ebook)
        self.assertIn("<style>", ebook)
        self.assertTrue(".chapter-nav" in ebook or "@media print" in ebook)
        self.assertNotIn('href="assets/book.css"', ebook)
        self.assertTrue((out / "assets" / "book.css").is_file())
        css = (out / "assets" / "book.css").read_text(encoding="utf-8")
        self.assertIn(".chapter-nav", css)
        self.assertIn("@media print", css)

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
                ["make", "html", f"DECK_ROOT={deck}", "SLIDES=pages"],
                cwd=str(SKILL_ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            out = deck / "build" / "pages"
            index = (out / "index.html").read_text(encoding="utf-8")
            intro = (out / "01-intro.html").read_text(encoding="utf-8")
            ebook = (out / "my-book.html").read_text(encoding="utf-8")
            self.assertIn("Home", index)
            self.assertIn("My Book", index)
            self.assertIn("Intro", index)
            self.assertIn('href="01-intro.html"', index)
            self.assertIn("Intro", intro)
            self.assertIn("Details", intro)
            self.assertIn("page-toc", intro)
            self.assertIn("Home", ebook)
            self.assertIn("Intro", ebook)
            self.assertIn('href="#ch-01-intro"', ebook)
            self.assertIn("<style>", ebook)
            self.assertTrue(".chapter-nav" in ebook or "@media print" in ebook)
            self.assertNotIn('href="assets/book.css"', ebook)

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
        self.assertIn("pip install markdown", proc.stderr)
        self.assertIn("Missing dependency: markdown", proc.stderr)

    def test_empty_book_exits(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_meta(deck / "pages", "empty-book")
            proc = _run_build(deck)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("README.md", proc.stderr)
            self.assertIn("numbered chapter", proc.stderr)

    def test_config_output_matches_written_ebook(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "notes", "note-book", "Notes")
            with patch.dict(os.environ, {"DECK_ROOT": str(deck), "SLIDES": "notes"}):
                paths = config_module.output_paths(deck)
                proc = subprocess.run(
                    [sys.executable, str(BUILD_PAGES)],
                    cwd=str(SKILL_ROOT),
                    env={**os.environ, "DECK_ROOT": str(deck), "SLIDES": "notes"},
                    capture_output=True,
                    text=True,
                )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(paths.html.is_file())
            self.assertIn("Notes", paths.html.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
