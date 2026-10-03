"""Bundled themes besides swiss-modern are complete and selectable."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
TEMPLATES = SKILL / "templates"
BUILD = SCRIPTS / "build-slides.py"

EXTRA = ("paper-ink", "terminal-green", "blue-professional")
MARKERS = (Path("deck.css"), Path("deck.js"), Path("pptx") / "theme.json")

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import config as config_module


class TestBundledThemes(unittest.TestCase):
    def test_extra_themes_have_engine_files(self):
        for name in EXTRA:
            theme = TEMPLATES / name
            with self.subTest(name=name):
                self.assertTrue(theme.is_dir(), name)
                for marker in MARKERS:
                    self.assertTrue((theme / marker).is_file(), f"{name}/{marker}")
                self.assertTrue((theme / "fonts.url").is_file(), name)
                css = (theme / "deck.css").read_text(encoding="utf-8")
                self.assertNotIn("THEME — Swiss Modern", css)
                self.assertIn("frontend-slides", css)

    def test_font_href_follows_fonts_url(self):
        fonts = (TEMPLATES / "terminal-green" / "fonts.url").read_text(encoding="utf-8")
        self.assertIn("JetBrains+Mono", fonts)
        fonts = (TEMPLATES / "paper-ink" / "fonts.url").read_text(encoding="utf-8")
        self.assertIn("Cormorant", fonts)
        fonts = (TEMPLATES / "blue-professional" / "fonts.url").read_text(encoding="utf-8")
        self.assertIn("Manrope", fonts)

    def test_config_loads_paper_ink(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            (deck / "slides").mkdir()
            (deck / "slides" / "010-cover.md").write_text(
                "---\nlayout: title\ntitle: Hi\n---\n",
                encoding="utf-8",
            )
            (deck / "config.ini").write_text(
                "[deck]\nname = theme-deck\nslides = slides\n[build]\ntheme = paper-ink\n",
                encoding="utf-8",
            )
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.theme, "paper-ink")
            self.assertEqual(loaded.theme_dir, (TEMPLATES / "paper-ink").resolve())

    def test_html_build_embeds_theme_font_and_css(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            (deck / "slides").mkdir()
            (deck / "slides" / "010-cover.md").write_text(
                "---\nlayout: title\ntitle: Hi\n---\n",
                encoding="utf-8",
            )
            (deck / "config.ini").write_text(
                "[deck]\nname = theme-deck\nslides = slides\n" "[build]\ntheme = terminal-green\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["DECK_ROOT"] = str(deck)
            env["MARKDOWN_SLIDES_EMBED_FONTS"] = "0"
            result = subprocess.run(
                [sys.executable, str(BUILD)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            html = (deck / "build" / "slides" / "theme-deck.html").read_text(encoding="utf-8")
            self.assertNotIn("fonts.googleapis.com", html)
            self.assertNotIn("fonts.gstatic.com", html)
            self.assertIn("JetBrains Mono", html)
            self.assertIn("THEME — Terminal Green", html)
            self.assertIn("#0d1117", html)


if __name__ == "__main__":
    unittest.main()
