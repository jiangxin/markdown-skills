"""Default PPTX and PDF paths follow build/<slides>/ and meta.toml name."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import isolated_env
import config as config_module

SKILL = config_module.skill_root()
SCRIPTS = SKILL / "scripts"
BANNED = (
    "ai-era-programmer",
    "content/pages",
    "content/images",
    "frontend-slides",
    "code-split",
)


class TestOutputPaths(unittest.TestCase):
    def _deck(self, raw: str, name: str = "sample-deck") -> Path:
        deck = Path(raw).resolve()
        (deck / "slides").mkdir(parents=True, exist_ok=True)
        isolated_env.write_meta(deck / "slides", name, "Sample")
        return deck

    def test_default_paths_use_deck_name(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = self._deck(raw)
            paths = config_module.output_paths(deck)
            self.assertEqual(paths.pptx, deck / "build" / "slides" / "sample-deck.pptx")
            self.assertEqual(paths.pdf, deck / "build" / "slides" / "sample-deck.pdf")
            self.assertEqual(paths.html, deck / "build" / "slides" / "sample-deck.html")
            self.assertEqual(paths.slides_rel, "slides")
            self.assertEqual(paths.theme, "swiss-modern")
            self.assertEqual(
                paths.theme_dir,
                (SKILL / "templates" / "swiss-modern").resolve(),
            )
            self.assertEqual(paths.pptx.parent, deck / "build" / "slides")
            self.assertEqual(paths.pdf.parent, deck / "build" / "slides")
            self.assertFalse(paths.pptx.exists())
            self.assertFalse(paths.pdf.exists())

    def test_example_deck_names(self):
        paths = config_module.output_paths(SKILL)
        self.assertEqual(paths.name, "markdown-slides-examples")
        self.assertEqual(
            paths.pptx, SKILL / "build" / "examples" / "slides" / "markdown-slides-examples.pptx"
        )
        self.assertEqual(
            paths.pdf, SKILL / "build" / "examples" / "slides" / "markdown-slides-examples.pdf"
        )
        self.assertEqual(
            paths.html, SKILL / "build" / "examples" / "slides" / "markdown-slides-examples.html"
        )

    def test_print_output_flag(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = self._deck(raw, name="print-deck")
            env = os.environ.copy()
            env["DECK_ROOT"] = str(deck)
            env.pop("DOC", None)
            script = SCRIPTS / "config.py"
            for kind in ("pptx", "pdf"):
                result = subprocess.run(
                    [sys.executable, str(script), "--print-output", kind],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stdout.strip(),
                    str(deck / "build" / "slides" / f"print-deck.{kind}"),
                )
                self.assertFalse((deck / f"print-deck.{kind}").exists())

    def test_node_print_output_does_not_build(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = self._deck(raw, name="node-deck")
            env = os.environ.copy()
            env["DECK_ROOT"] = str(SKILL)
            env.pop("DOC", None)
            for script, suffix in (("build-pptx.js", ".pptx"), ("export-pdf.js", ".pdf")):
                result = subprocess.run(
                    [
                        "node",
                        str(SCRIPTS / script),
                        "--print-output",
                        "--deck-root",
                        str(deck),
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stdout.strip(),
                    str(deck / "build" / "slides" / f"node-deck{suffix}"),
                )
                self.assertFalse((deck / f"node-deck{suffix}").exists())
                lowered = (result.stderr or "").lower()
                self.assertNotIn("chromium", lowered)
                self.assertNotIn("playwright", lowered)
                self.assertNotIn("pptxgenjs", lowered)

    def test_scripts_omit_lecture_paths(self):
        files = [
            SCRIPTS / "build-pptx.js",
            SCRIPTS / "export-pdf.js",
            SCRIPTS / "serve.py",
            SCRIPTS / "compress-images.py",
            SCRIPTS / "deck-paths.js",
            SKILL / "templates" / "swiss-modern" / "pptx" / "layouts.js",
            SKILL / "templates" / "swiss-modern" / "pptx" / "chrome.js",
            SKILL / "templates" / "swiss-modern" / "pptx" / "theme.json",
        ]
        for path in files:
            text = path.read_text(encoding="utf-8")
            for banned in BANNED:
                self.assertNotIn(banned, text, f"{path.name} contains {banned}")


if __name__ == "__main__":
    unittest.main()
