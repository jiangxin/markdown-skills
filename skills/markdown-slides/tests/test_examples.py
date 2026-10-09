"""The English example deck builds the layout tour, usage pages, and a git describe cover stamp."""

import html
import re
import subprocess
import sys
import unittest
from pathlib import Path

import isolated_env

SKILL = Path(__file__).resolve().parent.parent
SLIDES = SKILL / "examples" / "slides"
HTML_PATH = SKILL / "build" / "examples" / "slides" / "markdown-slides-examples.html"
SCRIPTS = SKILL / "scripts"

SIZE_FIELD = re.compile(r"^(?:text_size|note_size|size):\s*(s|l|xl|xxl)\s*$")
CARD_OPEN = re.compile(r"^:::card\b(.*)$")
SIZE_STEPS = ("s", "l", "xl", "xxl")
STAMP_SUFFIX = " · 01 / 13"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import slide_model


def git_describe(root: Path, doc_rel: str) -> str:
    slide_model._GIT_DESCRIBE.clear()
    return slide_model.git_describe(root, doc_rel)


def size_tokens() -> list[str]:
    found: list[str] = []
    for path in sorted(SLIDES.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            field = SIZE_FIELD.match(stripped)
            if field:
                found.append(field.group(1))
                continue
            opened = CARD_OPEN.match(stripped)
            if opened:
                for word in opened.group(1).split():
                    if word in SIZE_STEPS:
                        found.append(word)
    return found


class TestExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            ["make", "html"],
            cwd=SKILL,
            env=isolated_env.isolated(),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"make html failed ({result.returncode})\n" f"{result.stdout}\n{result.stderr}"
            )
        if not HTML_PATH.is_file():
            raise AssertionError(f"missing {HTML_PATH}")
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        slide_model._GIT_DESCRIBE.clear()
        cls.deck = slide_model.load_deck(SKILL)

    def test_cover_stamp_matches_git_describe(self):
        version = git_describe(SKILL, "examples/slides")
        expected = f"{version}{STAMP_SUFFIX}"
        stamps = re.findall(r'<span class="stamp">(.*?)</span>', self.html)
        self.assertTrue(stamps, "built HTML has no footer stamp")
        self.assertEqual(stamps[0], html.escape(expected))
        self.assertIn("addEventListener('load', go)", self.html)
        self.assertTrue(expected.endswith(STAMP_SUFFIX))
        self.assertEqual(self.deck["slides"][0]["stamp"], expected)

    def test_layout_tour_and_usage_pages(self):
        layouts = [slide["layout"] for slide in self.deck["slides"]]
        self.assertEqual(
            layouts,
            [
                "title",
                "section",
                "cards",
                "split",
                "stack-split",
                "stack-split",
                "table",
                "table-cards",
                "section",
                "table",
                "table",
                "cards",
                "title",
            ],
        )
        self.assertEqual(layouts.count("title"), 2)
        self.assertEqual(layouts.count("section"), 2)
        self.assertEqual(layouts.count("cards"), 2)
        self.assertEqual(layouts.count("split"), 1)
        self.assertEqual(layouts.count("table"), 3)
        self.assertEqual(layouts.count("table-cards"), 1)
        self.assertEqual(layouts.count("stack-split"), 2)
        self.assertEqual(self.html.count('class="slide title-slide'), 2)
        self.assertEqual(self.html.count('class="slide section-slide'), 2)
        self.assertIn('class="grid-23"', self.html)
        self.assertIn(
            "grid-template-columns:minmax(0, 35fr) minmax(0, 35fr) minmax(0, 30fr)",
            self.html,
        )

    def test_highlight_band_note_and_cover_foot(self):
        table = next(slide for slide in self.deck["slides"] if slide["layout"] == "table")
        highlighted = [cell for row in table["table"]["rows"] for cell in row if cell["hl"]]
        self.assertTrue(highlighted)
        self.assertIn('class="hl"', self.html)
        self.assertIn(">Highlighted<", self.html)

        cards = next(slide for slide in self.deck["slides"] if slide["file"] == "030-cards.md")
        self.assertEqual(cards["note_slot"], "")
        self.assertIn("full width", cards["note"])
        self.assertIn("card note text-xxl", self.html)
        self.assertIn("This band runs the full width under the cards.", self.html)

        cover = self.deck["slides"][0]
        self.assertEqual(cover["file"], "010-cover.md")
        self.assertEqual(cover["note_slot"], "foot")
        self.assertIn("written by the generator", cover["note"])
        self.assertIn('class="foot-note"', self.html)
        self.assertIn("The stamp on the right is written by the generator.", self.html)
        self.assertIn("This line can be edited with E", self.html)
        self.assertIn('<span class="en">DEMO</span>', self.html)
        self.assertIn('<span class="en long">Questions</span>', self.html)

    def test_storage_key_and_lecture_names_absent(self):
        self.assertIn(
            'this.storageKey = "markdown-slides:markdown-slides-examples"',
            self.html,
        )
        self.assertNotIn("ai-era-programmer", self.html)
        self.assertNotIn("frontend-slides:", self.html)

    def test_size_steps_each_once(self):
        self.assertEqual(sorted(size_tokens()), sorted(SIZE_STEPS))
        self.assertEqual(len(size_tokens()), len(set(size_tokens())))


if __name__ == "__main__":
    unittest.main()
