"""Deck-root trampoline dispatches by meta.toml type."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_config import write_book, write_meta

PAGES_SKILL = Path(__file__).resolve().parent.parent
SLIDES_SKILL = PAGES_SKILL.parent / "markdown-slides"
TEMPLATE_MAKE = SLIDES_SKILL / "templates" / "Makefile.deck"
TEMPLATE_BUILD = SLIDES_SKILL / "templates" / "build.py"

SLIDE_PAGE = """---
layout: title
title: Hello
---
"""

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
    if extra:
        env.update(extra)
    return env


def _copy_trampoline(deck: Path) -> None:
    shutil.copy(TEMPLATE_MAKE, deck / "Makefile")
    shutil.copy(TEMPLATE_BUILD, deck / "build.py")


def _link_skills(deck: Path) -> None:
    skills = deck / "skills"
    skills.mkdir()
    os.symlink(SLIDES_SKILL, skills / "markdown-slides")
    os.symlink(PAGES_SKILL, skills / "markdown-pages")


def _write_slides(deck: Path) -> None:
    slides = deck / "slides"
    slides.mkdir()
    write_meta(slides, "demo-deck", "Demo Slides", kind="slides")
    (slides / "010-hello.md").write_text(SLIDE_PAGE, encoding="utf-8")


class TestTrampolineDispatch(unittest.TestCase):
    def setUp(self):
        if not TEMPLATE_BUILD.is_file() or not TEMPLATE_MAKE.is_file():
            self.skipTest("markdown-slides trampoline templates are missing")
        if not (SLIDES_SKILL / "scripts" / "build-slides.py").is_file():
            self.skipTest("markdown-slides skill is not a sibling")

    def test_help_mentions_slides_and_pages(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            _copy_trampoline(deck)
            result = subprocess.run(
                ["make", "-C", str(deck), "help"],
                env=isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            text = result.stdout
            self.assertIn("slides", text)
            self.assertIn("pages", text)
            self.assertIn("MARKDOWN_PAGES_HOME", text)
            self.assertIn("MARKDOWN_SLIDES_HOME", text)
            self.assertIn("type=slides", text)
            self.assertIn("scripts/markdown-pages/", text)
            self.assertIn("scripts/markdown-slides/", text)

    def test_html_pages_does_not_clobber_slides_build(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            _write_slides(deck)
            write_book(deck / "pages", "demo-book", "Demo Book")
            _copy_trampoline(deck)
            _link_skills(deck)
            marker = deck / "build" / "slides" / "keep.html"
            marker.parent.mkdir(parents=True)
            marker.write_text("sentinel\n", encoding="utf-8")
            slides_build = subprocess.run(
                ["make", "-C", str(deck), "html", "slides"],
                env=isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                slides_build.returncode,
                0,
                slides_build.stderr + slides_build.stdout,
            )
            result = subprocess.run(
                ["make", "-C", str(deck), "html", "pages"],
                env=isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(marker.read_text(encoding="utf-8"), "sentinel\n")
            slides_html = deck / "build" / "slides" / "demo-deck.html"
            self.assertTrue(slides_html.is_file())
            self.assertIn("Demo Slides", slides_html.read_text(encoding="utf-8"))
            index = deck / "build" / "pages" / "index.html"
            ebook = deck / "build" / "pages" / "demo-book.html"
            self.assertTrue(index.is_file(), result.stdout)
            self.assertTrue(ebook.is_file(), result.stdout)
            html = index.read_text(encoding="utf-8")
            self.assertIn("Demo Book", html)
            self.assertIn("Intro", html)

    def test_html_without_dir_requires_choice_when_both_types(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            _write_slides(deck)
            write_book(deck / "pages", "demo-book", "Demo Book")
            _copy_trampoline(deck)
            _link_skills(deck)
            result = subprocess.run(
                ["make", "-C", str(deck), "html"],
                env=isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            combined = result.stderr + result.stdout
            self.assertIn("pass a directory", combined)
            self.assertIn("pages", combined)
            self.assertFalse((deck / "build" / "pages" / "index.html").exists())
            self.assertFalse((deck / "build" / "slides" / "demo-deck.html").exists())

    def test_ppt_pages_is_nonzero(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "demo-book", "Demo Book")
            _copy_trampoline(deck)
            _link_skills(deck)
            result = subprocess.run(
                ["make", "-C", str(deck), "ppt", "pages"],
                env=isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            combined = result.stderr + result.stdout
            self.assertIn("ppt", combined)
            self.assertIn("slides", combined)

    def test_local_markdown_pages_scripts_run_html(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "local-book", "Local Book")
            _copy_trampoline(deck)
            local = deck / "scripts" / "markdown-pages"
            local.mkdir(parents=True)
            (local / "build-pages.py").write_text(
                "#!/usr/bin/env python3\n"
                "import os\n"
                "from pathlib import Path\n"
                "out = Path(os.environ['DECK_ROOT']) / 'build' / 'pages'\n"
                "out.mkdir(parents=True)\n"
                "(out / 'local.txt').write_text('from-local\\n')\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["make", "-C", str(deck), "html", "pages"],
                env=isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            marker = deck / "build" / "pages" / "local.txt"
            self.assertTrue(marker.is_file())
            self.assertEqual(marker.read_text(encoding="utf-8"), "from-local\n")
            self.assertFalse((deck / "build" / "pages" / "local-book.html").exists())

    def test_pages_home_env_selects_engine(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "env-book", "Env Book")
            _copy_trampoline(deck)
            result = subprocess.run(
                ["make", "-C", str(deck), "html", "pages"],
                env=isolated({"MARKDOWN_PAGES_HOME": str(PAGES_SKILL)}),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((deck / "build" / "pages" / "env-book.html").is_file())

    def test_missing_pages_skill_mentions_home(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "no-engine", "No Engine")
            _copy_trampoline(deck)
            result = subprocess.run(
                ["make", "-C", str(deck), "html", "pages"],
                env=isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            combined = result.stderr + result.stdout
            self.assertIn("MARKDOWN_PAGES_HOME", combined)
            self.assertFalse((deck / "build" / "pages" / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
