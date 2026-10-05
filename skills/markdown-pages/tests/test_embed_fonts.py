"""Pages webfont helper: cache-only when enabled."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import embed_fonts  # noqa: E402


class TestEmbedFontsPages(unittest.TestCase):
    def test_font_href_from_templates(self):
        href = embed_fonts.font_href(SKILL / "templates")
        self.assertIn("fonts.googleapis.com", href)
        self.assertIn("IBM+Plex", href)

    def test_enabled_missing_cache_is_safe(self):
        with tempfile.TemporaryDirectory() as raw:
            skill = Path(raw)
            css = embed_fonts.embedded_font_css(
                "https://fonts.googleapis.com/css2?family=Z",
                skill=skill,
                enabled=True,
            )
            self.assertIn("no local cache", css)
            self.assertNotIn("fonts.gstatic.com", css)

    def test_env_off_wins(self):
        with patch.dict(os.environ, {"MARKDOWN_PAGES_EMBED_FONTS": "0"}):
            css = embed_fonts.embedded_font_css(
                "https://fonts.googleapis.com/css2?family=X",
                enabled=True,
            )
        self.assertIn("skipped", css)


if __name__ == "__main__":
    unittest.main()
