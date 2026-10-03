"""The publisher repo's deck files stay aligned with this skill."""

import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent
LAYOUT = re.compile(r"^layout:\s*(\S+)\s*$", re.M)


def _publisher_deck() -> bool:
    makefile = REPO / "Makefile"
    builder = REPO / "build.py"
    return (
        makefile.is_file() and builder.is_file() and (REPO / "skills" / "markdown-slides").is_dir()
    )


def _page_layouts(directory: Path) -> dict[str, str]:
    layouts: dict[str, str] = {}
    for path in sorted(directory.glob("*.md")):
        if path.name == "index.md":
            continue
        match = LAYOUT.search(path.read_text(encoding="utf-8"))
        if match is None:
            raise AssertionError(f"missing layout in {path}")
        layouts[path.name] = match.group(1)
    return layouts


class TestPublisherDeck(unittest.TestCase):
    def setUp(self):
        if not _publisher_deck():
            self.skipTest("skill is not nested in the markdown-publisher deck")

    def test_root_makefile_matches_template(self):
        template = SKILL / "templates" / "Makefile.deck"
        deployed = REPO / "Makefile"
        self.assertEqual(
            deployed.read_text(encoding="utf-8"),
            template.read_text(encoding="utf-8"),
        )

    def test_root_build_py_matches_template(self):
        template = SKILL / "templates" / "build.py"
        deployed = REPO / "build.py"
        self.assertEqual(
            deployed.read_text(encoding="utf-8"),
            template.read_text(encoding="utf-8"),
        )

    def test_example_and_demo_meta_are_slides(self):
        for directory, name in (
            (SKILL / "examples" / "slides", "markdown-slides-examples"),
            (REPO / "slides", "markdown-publisher"),
        ):
            text = (directory / "meta.toml").read_text(encoding="utf-8")
            self.assertIn('type = "slides"', text)
            self.assertIn(f'name = "{name}"', text)

    def test_root_slides_match_example_names_and_layouts(self):
        examples = _page_layouts(SKILL / "examples" / "slides")
        demo = _page_layouts(REPO / "slides")
        self.assertEqual(examples, demo)
