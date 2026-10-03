"""Google Fonts CSS is inlined so viewing HTML does not hit the network."""

import os
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import embed_fonts


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

    def test_skip_env_does_not_fetch(self):
        os.environ["MARKDOWN_SLIDES_EMBED_FONTS"] = "0"
        try:
            css = embed_fonts.embedded_font_css("https://fonts.googleapis.com/css2?family=X")
        finally:
            os.environ.pop("MARKDOWN_SLIDES_EMBED_FONTS", None)
        self.assertIn("skipped", css)
        self.assertNotIn("fonts.googleapis.com", css)


if __name__ == "__main__":
    unittest.main()
