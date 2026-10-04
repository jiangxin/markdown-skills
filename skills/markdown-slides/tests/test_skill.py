"""SKILL.md states the English deck workflow an agent must follow."""

import unittest
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"

REQUIRED = (
    "ask in English",
    "slides/",
    "ask in English before git init",
    "do not write slides",
    "do not git init",
    "from the deck root",
    "SKILL",
    "theme =",
    "templates/swiss-modern",
    "templates/Makefile.deck",
    "templates/build.py",
    "frontend-slides",
    "examples/slides/010-cover.md",
    "Do not hand-edit HTML",
    "Read this skill's `references/design.md` before creating slides.",
    "The engine stays in the skill",
    "Skip git init when building it.",
    "order = auto",
    "sort = <file.md>",
    "do not re-initialize",
    "overwrite existing slides",
    "themes/",
    "Deep customization of the generator",
    ".agents/skills/markdown-slides",
    "skills_root",
    "build_root",
    "make slides",
    "build/",
    "meta.toml",
    'type = "slides"',
    "Customize the seeded Markdown",
    "user's preferred language",
    "user's topic",
    "Rewrite **all visible copy**",
    "byte-identical copy of `examples/slides/`",
    "Plan then generate",
    "references/plan.md",
    "Plan (required; stop before pages)",
    "Generate after plan approval",
)

FORBIDDEN = (
    "| `scripts`",
    'argument-hint: "[create | edit | theme | scripts]"',
    "## scripts",
    "Ask the user to confirm before copying scripts.",
)


class SkillDocTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL_MD.read_text(encoding="utf-8")

    def test_required_phrases(self):
        for phrase in REQUIRED:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_no_scripts_command(self):
        for phrase in FORBIDDEN:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.text)

    def test_english_body(self):
        self.assertNotIn("幻灯片", self.text)

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\n"))
        self.assertIn("name: markdown-slides\n", self.text)
        self.assertIn("description:", self.text)
        self.assertIn('argument-hint: "[create | edit | theme]"', self.text)
