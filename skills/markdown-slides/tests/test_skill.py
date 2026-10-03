"""SKILL.md states the English deck workflow an agent must follow."""

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
    "from the deck root",
    "[build] skill",
    "[build] theme",
    "templates/swiss-modern",
    "templates/Makefile.deck",
    "examples/slides/010-cover.md",
    "Do not hand-edit HTML",
    "Read references/design.md before creating slides.",
    "The engine stays in the skill.",
    "Skip git init when building it.",
    "order = auto",
    "sort = <file.md>",
)


class SkillDocTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL_MD.read_text(encoding="utf-8")

    def test_required_phrases(self):
        for phrase in REQUIRED:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_english_body(self):
        self.assertNotIn("幻灯片", self.text)

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\n"))
        self.assertIn("name: markdown-slides\n", self.text)
        self.assertIn("description:", self.text)
