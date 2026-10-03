"""SKILL.md states the English book workflow an agent must follow."""

import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
DESIGN_MD = SKILL_ROOT / "references" / "design.md"
EXAMPLES = SKILL_ROOT / "examples" / "pages"

REQUIRED = (
    "ask in English",
    "pages/",
    "ask in English before git init",
    "do not write pages",
    "do not git init",
    "from the deck root",
    "MARKDOWN_PAGES_HOME",
    "Do not hand-edit HTML",
    "Read references/design.md before creating pages.",
    "The engine stays in the skill",
    "Skip git init when building it.",
    "order = auto",
    "sort = <file.md>",
    "do not re-initialize",
    "overwrite existing chapters",
    "Ask the user to confirm before copying scripts.",
    "make html",
    "make pdf",
    "build/",
    "meta.toml",
    'type = "pages"',
    "scripts/markdown-pages/",
    "PPTX is not this skill",
)


class SkillDocTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL_MD.read_text(encoding="utf-8")

    def test_required_phrases(self):
        for phrase in REQUIRED:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_english_body(self):
        self.assertNotIn("电子书", self.text)
        self.assertNotIn("幻灯片", self.text)

    def test_no_theme_command(self):
        self.assertNotIn("| `theme` |", self.text)

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\n"))
        self.assertIn("name: markdown-pages\n", self.text)
        self.assertIn("description:", self.text)

    def test_design_exists(self):
        self.assertTrue(DESIGN_MD.is_file())

    def test_example_pages(self):
        self.assertTrue(EXAMPLES.is_dir())
        self.assertTrue((EXAMPLES / "meta.toml").is_file())
        self.assertTrue((EXAMPLES / "README.md").is_file())
        meta = (EXAMPLES / "meta.toml").read_text(encoding="utf-8")
        self.assertIn('type = "pages"', meta)
        numbered = sorted(p.name for p in EXAMPLES.glob("[0-9][0-9]-*.md"))
        self.assertEqual(len(numbered), 2)
        for name in numbered:
            self.assertRegex(name, r"^[0-9]{2}-[a-z0-9-]+\.md$")
            self.assertTrue((EXAMPLES / name).is_file())
