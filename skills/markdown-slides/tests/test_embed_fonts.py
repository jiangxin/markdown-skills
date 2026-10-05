"""Google Fonts CSS is cached for optional inline; builds never fetch."""

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


class TestEmbedFonts(unittest.TestCase):
    def test_inline_replaces_gstatic_urls(self):
        sheet = (
            "@font-face{font-family:'Demo';src:url(https://fonts.gstatic.com/s/demo.woff2) "
            "format('woff2')}"
        )
        payload = b"wOF2" + b"\x00" * 16

        def fetch(url: str) -> bytes:
            if "googleapis" in url:
                return sheet.encode("utf-8")
            if "gstatic" in url:
                return payload
            raise AssertionError(url)

        css = embed_fonts._inline("https://fonts.googleapis.com/css2?family=Demo", fetch=fetch)
        self.assertNotIn("fonts.gstatic.com", css)
        self.assertNotIn("fonts.googleapis.com", css)
        self.assertIn("data:font/woff2;base64,", css)

    def test_disabled_by_default_does_not_use_cache(self):
        with tempfile.TemporaryDirectory() as raw:
            skill = Path(raw)
            href = "https://fonts.googleapis.com/css2?family=X"
            cached = embed_fonts.cache_dir(href, skill)
            cached.mkdir(parents=True)
            (cached / "embedded.css").write_text("@font-face{font-family:X}", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("MARKDOWN_SLIDES_EMBED_FONTS", None)
                css = embed_fonts.embedded_font_css(href, skill=skill, enabled=False)
            self.assertIn("disabled", css)
            self.assertNotIn("@font-face", css)

    def test_enabled_reads_cache_only(self):
        with tempfile.TemporaryDirectory() as raw:
            skill = Path(raw)
            href = "https://fonts.googleapis.com/css2?family=Y"
            cached = embed_fonts.cache_dir(href, skill)
            cached.mkdir(parents=True)
            (cached / "embedded.css").write_text(
                "@font-face{font-family:Y;src:url(data:font/woff2;base64,AA==)}",
                encoding="utf-8",
            )
            css = embed_fonts.embedded_font_css(href, skill=skill, enabled=True)
            self.assertIn("@font-face", css)
            self.assertIn("data:font/woff2", css)

    def test_enabled_missing_cache_is_safe(self):
        with tempfile.TemporaryDirectory() as raw:
            skill = Path(raw)
            href = "https://fonts.googleapis.com/css2?family=Z"
            css = embed_fonts.embedded_font_css(href, skill=skill, enabled=True)
            self.assertIn("no local cache", css)
            self.assertNotIn("fonts.googleapis.com", css)

    def test_skip_env_does_not_fetch(self):
        os.environ["MARKDOWN_SLIDES_EMBED_FONTS"] = "0"
        try:
            css = embed_fonts.embedded_font_css(
                "https://fonts.googleapis.com/css2?family=X",
                enabled=True,
            )
        finally:
            os.environ.pop("MARKDOWN_SLIDES_EMBED_FONTS", None)
        self.assertIn("skipped", css)
        self.assertNotIn("fonts.googleapis.com", css)


if __name__ == "__main__":
    unittest.main()
