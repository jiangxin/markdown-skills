"""The English design note lists the same layouts the HTML renderer builds."""

import importlib.util
import re
import sys
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DESIGN = SKILL / "references" / "design.md"
BUILD_SLIDES = SKILL / "scripts" / "build-slides.py"

# Lecture page names that must not leak into the shared grammar.
ABSENT = (
    "junio-interview",
    "rebase-history",
    "rebase-split",
    "code-split",
)

SIZE_STEPS = ("s", "l", "xl", "xxl")

_LAYOUTS_SECTION = re.compile(r"^## Layouts\n(.*?)(?=^## |\Z)", re.M | re.S)
_RULE = re.compile(r"^:?-{3,}:?$")


def documented_layouts(text: str) -> set[str]:
    """Read layout names from the first column of the ## Layouts table."""
    section = _LAYOUTS_SECTION.search(text)
    if section is None:
        raise AssertionError("design.md is missing a ## Layouts section")
    names: list[str] = []
    for line in section.group(1).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        first = stripped.strip("|").split("|", 1)[0].strip().strip("`").strip()
        if not first or first == "layout" or _RULE.fullmatch(first):
            continue
        names.append(first)
    if not names:
        raise AssertionError("## Layouts table has no layout names")
    if len(names) != len(set(names)):
        raise AssertionError(f"duplicate layouts in design.md: {names}")
    return set(names)


def renderer_layouts() -> set[str]:
    """Load RENDERERS from build-slides.py (the filename is not an import name)."""
    scripts = str(BUILD_SLIDES.parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location("markdown_slides_build", BUILD_SLIDES)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {BUILD_SLIDES}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass can see the module during class creation.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return set(module.RENDERERS)


class TestDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DESIGN.read_text(encoding="utf-8")
        cls.documented = documented_layouts(cls.text)
        cls.renderers = renderer_layouts()

    def test_documented_layouts_match_renderers(self):
        self.assertEqual(self.documented, self.renderers)

    def test_lecture_page_names_absent(self):
        for name in ABSENT:
            self.assertNotIn(name, self.text)

    def test_size_steps_mentioned(self):
        for step in SIZE_STEPS:
            self.assertRegex(self.text, rf"(?<![A-Za-z]){step}(?![A-Za-z])")
