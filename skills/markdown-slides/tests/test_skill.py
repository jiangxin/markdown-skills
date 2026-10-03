"""SKILL.md states the English deck-creation workflow."""

import unittest
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"

REQUIRED = (
    "ask in English",
    "slides/",
    "[deck] slides",
    "ask in English before git init",
    "do not write slides",
    "do not git init",
    "make html DECK_ROOT=",
    "examples/slides/010-cover.md",
    "Do not hand-edit HTML",
)


class SkillDocTests(unittest.TestCase):
    def setUp(self):
        self.text = SKILL_MD.read_text(encoding="utf-8")

    def test_required_phrases(self):
        for phrase in REQUIRED:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_english_body(self):
        self.assertNotIn("幻灯片", self.text)


if __name__ == "__main__":
    unittest.main()
