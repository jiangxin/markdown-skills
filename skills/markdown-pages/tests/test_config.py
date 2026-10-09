"""Tests for scripts/config.py."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import config as config_module

SKILL_ROOT = Path(__file__).resolve().parent.parent


def _quoted(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_meta(
    directory: Path,
    name: str,
    title: str = "",
    kind: str = "pages",
    *,
    order: str = "",
    sort: str = "",
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    lines = [f"type = {_quoted(kind)}", f"name = {_quoted(name)}"]
    if title:
        lines.append(f"title = {_quoted(title)}")
    book_lines = []
    if order:
        book_lines.append(f"order = {_quoted(order)}")
    if sort:
        book_lines.append(f"sort = {_quoted(sort)}")
    if book_lines:
        lines.extend(("", "[book]", *book_lines))
    (directory / "meta.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_book(directory: Path, name: str, title: str = "", kind: str = "pages") -> None:
    write_meta(directory, name, title, kind)
    (directory / "README.md").write_text("# Home\n", encoding="utf-8")
    (directory / "01-intro.md").write_text("# Intro\n", encoding="utf-8")
    (directory / "02-next.md").write_text("# Next\n", encoding="utf-8")


class TestConfig(unittest.TestCase):
    def setUp(self):
        self._env = patch.dict(
            os.environ,
            {"DOC": "", "DECK_ROOT": ""},
            clear=False,
        )
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_skill_root_is_markdown_pages(self):
        skill = config_module.skill_root()
        self.assertEqual(skill, SKILL_ROOT)
        self.assertEqual(skill.name, "markdown-pages")
        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertTrue((skill / "scripts" / "config.py").is_file())

    def test_scan_selects_single_type_pages_dir(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "my-book", "My Book")
            write_meta(deck / "slides", "talk", "Talk", kind="slides")
            for skipped in ("scripts", "skills", "build", "themes"):
                write_book(deck / skipped / "hidden", "hidden-book")
            loaded = config_module.load_book(deck)
            self.assertEqual(loaded.name, "my-book")
            self.assertEqual(loaded.title, "My Book")
            self.assertEqual(loaded.kind, "pages")
            self.assertEqual(loaded.pages_rel, "pages")
            self.assertEqual(loaded.pages, (deck / "pages").resolve())
            self.assertEqual(loaded.order, "auto")
            self.assertIsNone(loaded.sort)
            chapters = config_module.list_chapters(loaded.pages)
            self.assertEqual(
                [path.name for path in chapters],
                ["01-intro.md", "02-next.md"],
            )

    def test_nested_pages_dir_is_selected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "docs" / "guide", "guide-book", "Guide")
            loaded = config_module.load_book(deck)
            self.assertEqual(loaded.pages_rel, "docs/guide")
            self.assertEqual(loaded.name, "guide-book")

    def test_doc_env_selects_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "main-book", "Main")
            write_book(deck / "notes", "notes-book")
            with patch.dict(os.environ, {"DOC": "notes"}, clear=False):
                loaded = config_module.load_book(deck)
            self.assertEqual(loaded.pages_rel, "notes")
            self.assertEqual(loaded.name, "notes-book")

    def test_type_slides_is_rejected_when_loading_as_pages(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_meta(deck / "talk", "talk-deck", "Talk", kind="slides")
            with patch.dict(os.environ, {"DOC": "talk"}, clear=False):
                with self.assertRaises(SystemExit) as caught:
                    config_module.load_book(deck)
            message = str(caught.exception)
            self.assertIn("slides", message)
            self.assertIn("pages", message)

    def test_scan_ignores_type_slides(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_meta(deck / "talk", "talk-deck", kind="slides")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_book(deck)
            self.assertIn("pages directory", str(caught.exception))

    def test_output_paths_use_rel_and_name(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "custom" / "pages", "my-book", "My Title")
            paths = config_module.output_paths(deck)
            resolved = deck.resolve()
            self.assertEqual(paths.name, "my-book")
            self.assertEqual(paths.title, "My Title")
            self.assertEqual(paths.kind, "pages")
            self.assertEqual(paths.pages_rel, "custom/pages")
            self.assertEqual(paths.html, resolved / "build" / "custom" / "pages" / "my-book.html")
            self.assertEqual(paths.pdf, resolved / "build" / "custom" / "pages" / "my-book.pdf")
            self.assertEqual(paths.site, resolved / "build" / "custom" / "pages" / "pages")
            self.assertEqual(paths.build_root, resolved / "build")
            self.assertFalse(hasattr(paths, "pptx"))

    def test_paths_build_root_overrides_artifact_dir(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_book(deck / "pages", "alt-book", "Alt")
            (deck / "config.ini").write_text(
                "[serve]\nport = 8000\n\n[paths]\nbuild_root = out/site\n",
                encoding="utf-8",
            )
            paths = config_module.output_paths(deck)
            self.assertEqual(paths.build_root, (deck / "out" / "site").resolve())
            self.assertEqual(
                paths.html,
                (deck / "out" / "site" / "pages" / "alt-book.html").resolve(),
            )

    def test_bundled_example_config(self):
        loaded = config_module.load_book(config_module.skill_root())
        self.assertEqual(loaded.name, "markdown-pages-examples")
        self.assertEqual(loaded.title, "Markdown Pages Examples")
        self.assertEqual(loaded.kind, "pages")
        self.assertEqual(loaded.pages_rel, "examples/pages")
        self.assertEqual(
            loaded.pages,
            (config_module.skill_root() / "examples" / "pages").resolve(),
        )
        self.assertEqual(
            [path.name for path in config_module.list_chapters(loaded.pages)],
            ["01-intro.md", "02-next.md"],
        )

    def test_deck_root_resolution(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw).resolve()
            with patch.dict(os.environ, {"DECK_ROOT": ""}, clear=False):
                self.assertEqual(
                    config_module.deck_root(argv=["prog"]),
                    config_module.skill_root(),
                )
            with patch.dict(os.environ, {"DECK_ROOT": str(deck)}):
                self.assertEqual(config_module.deck_root(argv=["prog"]), deck)
            with tempfile.TemporaryDirectory() as raw_argv:
                chosen = Path(raw_argv).resolve()
                with patch.dict(os.environ, {"DECK_ROOT": str(deck)}):
                    self.assertEqual(
                        config_module.deck_root(argv=["prog", "--deck-root", str(chosen)]),
                        chosen,
                    )

    def test_sort_path_is_relative_to_pages_dir(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_meta(deck / "pages", "pages", sort="README.md")
            loaded = config_module.load_book(deck)
            self.assertEqual(loaded.order, "")
            self.assertEqual(loaded.sort_rel, "README.md")
            self.assertEqual(loaded.sort, (deck / "pages" / "README.md").resolve())

    def test_order_and_sort_together_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            write_meta(deck / "pages", "pages", order="auto", sort="README.md")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_book(deck)
            self.assertIn("order and sort", str(caught.exception))

    def test_list_chapters_skips_unnumbered_and_meta(self):
        with tempfile.TemporaryDirectory() as raw:
            pages = Path(raw) / "pages"
            write_book(pages, "pages")
            (pages / "notes.md").write_text("# Notes\n", encoding="utf-8")
            (pages / "AGENTS.md").write_text("# Agent only\n", encoding="utf-8")
            (pages / "010-appendix.md").write_text("# Appendix\n", encoding="utf-8")
            names = [path.name for path in config_module.list_chapters(pages)]
            self.assertEqual(names, ["01-intro.md", "010-appendix.md", "02-next.md"])
            self.assertNotIn("notes.md", names)
            self.assertNotIn("README.md", names)
            self.assertNotIn("AGENTS.md", names)
            self.assertNotIn("meta.toml", names)

    def test_webfont_default_and_toggle(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self.assertFalse(config_module.webfont_enabled(deck))
            (deck / "config.ini").write_text("[assets]\nwebfont = yes\n", encoding="utf-8")
            self.assertTrue(config_module.webfont_enabled(deck))
            (deck / "config.ini").write_text("[assets]\nwebfont = no\n", encoding="utf-8")
            self.assertFalse(config_module.webfont_enabled(deck))
            (deck / "config.ini").write_text("[assets]\nwebfont = maybe\n", encoding="utf-8")
            with self.assertRaises(SystemExit) as caught:
                config_module.webfont_enabled(deck)
            self.assertIn("webfont", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
