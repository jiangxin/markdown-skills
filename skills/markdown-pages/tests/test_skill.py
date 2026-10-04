"""SKILL.md states the English book workflow an agent must follow."""

import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
DESIGN_MD = SKILL_ROOT / "references" / "design.md"
EXAMPLES = SKILL_ROOT / "examples" / "pages"

REQUIRED = (
    "user's preferred language",
    "AskQuestion",
    "pages/",
    "confirm before git init",
    "do not write pages",
    "do not git init",
    "from the deck root",
    "MARKDOWN_PAGES_HOME",
    "skills_root",
    "build_root",
    "templates/build.py",
    "templates/Makefile.deck",
    "Do not hand-edit HTML",
    "Read this skill's `references/design.md` before writing pages.",
    "The engine stays in the skill",
    "Skip git init when building it.",
    "order = auto",
    "sort = <file.md>",
    "do not re-initialize",
    "overwrite existing chapters",
    "more than one",
    "only initializes",
    "Deep customization of the generator",
    ".agents/skills/markdown-pages",
    "make html",
    "make pdf",
    "build/",
    "meta.toml",
    'type = "pages"',
    "Customize the seeded Markdown",
    "user's topic",
    "Rewrite **all visible copy**",
    "byte-identical copy of `examples/pages/`",
    "Plan then generate",
    "references/plan.md",
    "Plan (required; stop before chapters)",
    "Generate after plan approval",
    "Write `<book>/AGENTS.md`",
    "templates/AGENTS.md",
    "Python environment (required)",
    "requirements.txt",
    "ensure_venv.py",
    ".venv",
)

FORBIDDEN_LANG = ("ask in English",)

FORBIDDEN = (
    "| `create`",
    "| `edit`",
    "| `scripts`",
    'argument-hint: "[create | edit | scripts]"',
    "Infer create vs edit",
)


class SkillDocTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL_MD.read_text(encoding="utf-8")

    def test_required_phrases(self):
        for phrase in REQUIRED:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)

    def test_no_create_edit_scripts_commands(self):
        for phrase in FORBIDDEN:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.text)

    def test_no_force_english_prompts(self):
        for phrase in FORBIDDEN_LANG:
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.text)

    def test_english_body(self):
        self.assertNotIn("电子书", self.text)
        self.assertNotIn("幻灯片", self.text)

    def test_no_theme_command(self):
        self.assertNotIn("| `theme` |", self.text)

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\n"))
        self.assertIn("name: markdown-pages\n", self.text)
        self.assertIn("description:", self.text)
        self.assertIn('argument-hint: "[directory]"', self.text)

    def test_design_exists(self):
        self.assertTrue(DESIGN_MD.is_file())

    def test_agents_template_exists(self):
        path = SKILL_ROOT / "templates" / "AGENTS.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("markdown-pages", text)
        self.assertIn("references/design.md", text)
        self.assertIn("make html <dir>", text)

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
