"""HTML build writes <name>.html into the deck root from config.ini."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import isolated_env

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "build-slides.py"
DECK_JS = SKILL / "templates" / "swiss-modern" / "deck.js"
DECK_CSS = SKILL / "templates" / "swiss-modern" / "deck.css"

PAGE = """---
layout: title
title: Hello
---
"""


class TestBuildSlides(unittest.TestCase):
    def _write_deck(
        self,
        deck: Path,
        *,
        name: str,
        title: str,
        page: str = PAGE,
        favicon: str | None = None,
    ) -> None:
        slides = deck / "pages"
        slides.mkdir(parents=True)
        (deck / "config.ini").write_text(
            "[deck]\n" f"name = {name}\n" f"title = {title}\n" "slides = pages\n",
            encoding="utf-8",
        )
        (slides / "010-hello.md").write_text(page, encoding="utf-8")
        if favicon is not None:
            (deck / "favicon.svg").write_text(favicon, encoding="utf-8")

    def _run(self, deck: Path, *, use_flag: bool = False) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["MARKDOWN_SLIDES_EMBED_FONTS"] = "0"
        command = [sys.executable, str(SCRIPT)]
        if use_flag:
            env.pop("DECK_ROOT", None)
            command.extend(["--deck-root", str(deck)])
        else:
            env["DECK_ROOT"] = str(deck)
        return subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_fixture_html_follows_config(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write_deck(deck, name="fixture-deck", title="Fixture Title")
            result = self._run(deck)
            self.assertEqual(result.returncode, 0, result.stderr)
            html_path = deck / "fixture-deck.html"
            self.assertTrue(html_path.is_file())
            self.assertEqual(html_path.parent.resolve(), deck.resolve())
            html = html_path.read_text(encoding="utf-8")
            self.assertNotIn("fonts.googleapis.com", html)
            self.assertNotIn("fonts.gstatic.com", html)
            self.assertIn("<title>Fixture Title</title>", html)
            self.assertIn('this.storageKey = "markdown-slides:fixture-deck"', html)
            self.assertIn('a.download = "fixture-deck.html"', html)
            self.assertNotIn("__DECK_NAME__", html)
            self.assertNotIn("ai-era-programmer", html)
            self.assertNotIn("frontend-slides:", html)
            self.assertNotIn('rel="icon"', html)
            self.assertIn('class="slide title-slide grid-bg active visible"', html)

    def test_favicon_link_when_file_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write_deck(
                deck,
                name="with-icon",
                title="With Icon",
                favicon='<svg xmlns="http://www.w3.org/2000/svg"></svg>\n',
            )
            result = self._run(deck, use_flag=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            html = (deck / "with-icon.html").read_text(encoding="utf-8")
            self.assertIn(
                '<link rel="icon" href="favicon.svg" type="image/svg+xml">',
                html,
            )
            self.assertNotIn("ai-era-programmer", html)
            self.assertNotIn("frontend-slides:", html)

    def test_unknown_layout_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write_deck(
                deck,
                name="bad-layout",
                title="Bad Layout",
                page="---\nlayout: code-split\ntitle: Nope\n---\n",
            )
            result = self._run(deck)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("010-hello.md", result.stderr)
            self.assertFalse((deck / "bad-layout.html").exists())

    def test_deck_js_keeps_navigation_zoom_and_edit(self):
        js = DECK_JS.read_text(encoding="utf-8")
        for needle in (
            "ArrowRight",
            "ArrowLeft",
            "ArrowDown",
            "ArrowUp",
            "PageDown",
            "PageUp",
            'e.key === "f" || e.key === "F"',
            "requestFullscreen",
            "userZoom",
            "setUserZoom",
            "resetZoom",
            'e.key === "=" || e.key === "+"',
            'e.key === "-" || e.key === "_"',
            "slideFromHash",
            "hashchange",
            "location.hash",
            'e.key === "e" || e.key === "E"',
            '(e.metaKey || e.ctrlKey) && e.key === "s"',
            "localStorage.setItem(this.storageKey, html)",
            'slide.classList.toggle("active"',
            'slide.classList.toggle("visible"',
            "markdown-slides:__DECK_NAME__",
            'a.download = "__DECK_NAME__.html"',
        ):
            self.assertIn(needle, js)
        self.assertNotIn("ai-era-programmer", js)
        self.assertNotIn("frontend-slides:", js)

    def test_slides_toggle_with_active_and_visible(self):
        css = DECK_CSS.read_text(encoding="utf-8")
        slide = re.search(r"\.slide \{[^}]+\}", css)
        self.assertIsNotNone(slide)
        block = slide.group(0)
        self.assertIn("display: block", block)
        self.assertIn("visibility: hidden", block)
        self.assertNotIn("display: none", block)
        shown = re.search(r"\.slide\.active,\s*\.slide\.visible \{[^}]+\}", css)
        self.assertIsNotNone(shown)
        self.assertIn("visibility: visible", shown.group(0))
        self.assertIn("opacity: 1", shown.group(0))
        self.assertNotIn("display: none", shown.group(0))

    def test_makefile_html_passes_deck_root(self):
        text = (SKILL / "Makefile").read_text(encoding="utf-8")
        self.assertIn(
            'html:\n\tDECK_ROOT="$(DECK_ROOT)" python3 scripts/build-slides.py\n',
            text,
        )

    def test_deck_makefile_builds_html_via_skill(self):
        template = SKILL / "templates" / "Makefile.deck"
        self.assertTrue(template.is_file())
        text = template.read_text(encoding="utf-8")
        self.assertIn('$(MAKE) -C "$(SKILL)" $@ DECK_ROOT="$(DECK_ROOT)"', text)
        self.assertIn("html ppt pdf serve lint fmt test fonts:", text)
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write_deck(deck, name="tramp-deck", title="Trampoline Title")
            (deck / "config.ini").write_text(
                "[deck]\n"
                "name = tramp-deck\n"
                "title = Trampoline Title\n"
                "slides = pages\n"
                f"[build]\nskill = {SKILL}\n",
                encoding="utf-8",
            )
            shutil.copy(template, deck / "Makefile")
            result = subprocess.run(
                ["make", "-C", str(deck), "html"],
                env=isolated_env.isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            html_path = deck / "tramp-deck.html"
            self.assertTrue(html_path.is_file())
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("<title>Trampoline Title</title>", html)
            self.assertIn('this.storageKey = "markdown-slides:tramp-deck"', html)
            js = DECK_JS.read_text(encoding="utf-8")
            self.assertIn("userZoom", js)
            self.assertIn("userZoom", html)

    def test_deck_makefile_requires_skill(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write_deck(deck, name="no-skill", title="No Skill")
            shutil.copy(SKILL / "templates" / "Makefile.deck", deck / "Makefile")
            result = subprocess.run(
                ["make", "-C", str(deck), "html"],
                env=isolated_env.isolated(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((deck / "no-skill.html").exists())
            combined = result.stderr + result.stdout
            self.assertTrue(
                "[build] skill" in combined or "SKILL" in combined,
                combined,
            )


if __name__ == "__main__":
    unittest.main()
