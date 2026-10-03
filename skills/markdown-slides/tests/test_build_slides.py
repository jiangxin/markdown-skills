"""HTML build writes <name>.html into the deck root from config.ini."""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "build-slides.py"
DECK_JS = SKILL / "templates" / "deck.js"
DECK_CSS = SKILL / "templates" / "deck.css"

PAGE = """---
layout: title
title: Hello
---
"""

INDEX = """# Deck

## Slides

- [Hello](010-hello.md)
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
            "[deck]\n"
            f"name = {name}\n"
            f"title = {title}\n"
            "slides = pages\n",
            encoding="utf-8",
        )
        (slides / "010-hello.md").write_text(page, encoding="utf-8")
        (slides / "index.md").write_text(INDEX, encoding="utf-8")
        if favicon is not None:
            (deck / "favicon.svg").write_text(favicon, encoding="utf-8")

    def _run(self, deck: Path, *, use_flag: bool = False) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
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


if __name__ == "__main__":
    unittest.main()
