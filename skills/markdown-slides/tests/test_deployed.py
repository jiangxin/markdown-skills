"""The publisher repo's deck files stay aligned with this skill."""

import configparser
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parent.parent
LAYOUT = re.compile(r"^layout:\s*(\S+)\s*$", re.M)


def _publisher_deck() -> bool:
    ini = REPO / "config.ini"
    makefile = REPO / "Makefile"
    if not ini.is_file() or not makefile.is_file():
        return False
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(ini, encoding="utf-8")
    return parser.get("build", "skill", fallback="").strip() == "skills/markdown-slides"


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

    def test_root_slides_match_example_names_and_layouts(self):
        examples = _page_layouts(SKILL / "examples" / "slides")
        demo = _page_layouts(REPO / "slides")
        self.assertEqual(examples, demo)
