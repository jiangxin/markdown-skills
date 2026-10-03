"""Tests for scripts/config.py."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import config as config_module


class TestConfig(unittest.TestCase):
    def _write(self, deck: Path, text: str) -> None:
        (deck / "config.ini").write_text(text, encoding="utf-8")

    def test_missing_config_defaults(self):
        with tempfile.TemporaryDirectory(prefix="deck-") as raw:
            deck = Path(raw)
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.name, deck.resolve().name)
            self.assertEqual(loaded.title, loaded.name)
            self.assertEqual(loaded.slides_rel, "slides")
            self.assertEqual(loaded.slides, (deck / "slides").resolve())
            self.assertTrue(loaded.slides.is_absolute())

    def test_empty_fields_use_defaults(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nname =\ntitle =\nslides =\n")
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.name, deck.resolve().name)
            self.assertEqual(loaded.title, loaded.name)
            self.assertEqual(loaded.slides_rel, "slides")

    def test_explicit_name_title_slides(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(
                deck,
                "[deck]\nname = my-deck\ntitle = My Title\nslides = custom/pages\n",
            )
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.name, "my-deck")
            self.assertEqual(loaded.title, "My Title")
            self.assertEqual(loaded.slides_rel, "custom/pages")
            self.assertEqual(loaded.slides, (deck / "custom" / "pages").resolve())

    def test_empty_title_defaults_to_name(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nname = my-deck\ntitle =\n")
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.title, "my-deck")

    def test_invalid_name_exits(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nname = my_deck\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("name", str(caught.exception))

    def test_directory_name_may_be_used_when_name_missing(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw) / "my.deck"
            deck.mkdir()
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.name, "my.deck")

    def test_absolute_slides_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            absolute = deck / "inside"
            self._write(deck, f"[deck]\nslides = {absolute}\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("slides", str(caught.exception))

    def test_slides_parent_escape_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nslides = ../outside\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("escapes", str(caught.exception))

    def test_dots_that_stay_inside_are_allowed(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nslides = custom/../custom/pages\n")
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.slides, (deck / "custom" / "pages").resolve())

    def test_cover_overrides_only_010_cover(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(
                deck,
                "[cover]\npresenter = Ada\npresented_at = 2026-10-03\n",
            )
            meta = {"presenter": "A", "presented_at": "B", "title": "T"}
            other = config_module.cover_overrides(
                deck, Path("slides/020-section.md"), meta
            )
            self.assertEqual(other, meta)
            self.assertIsNot(other, meta)
            cover = config_module.cover_overrides(
                deck, Path("slides/010-cover.md"), meta
            )
            self.assertEqual(cover["presenter"], "Ada")
            self.assertEqual(cover["presented_at"], "2026-10-03")
            self.assertEqual(cover["title"], "T")
            self.assertEqual(meta["presenter"], "A")

    def test_empty_cover_values_do_not_override(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(
                deck,
                "[cover]\npresenter =\npresented_at = 2026-10-03\n",
            )
            meta = {"presenter": "A", "presented_at": "B"}
            result = config_module.cover_overrides(
                deck, Path("010-cover.md"), meta
            )
            self.assertEqual(result["presenter"], "A")
            self.assertEqual(result["presented_at"], "2026-10-03")

    def test_blank_cover_values_do_not_override(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[cover]\npresenter =   \npresented_at =\n")
            meta = {"presenter": "A", "presented_at": "B"}
            result = config_module.cover_overrides(
                deck, Path("010-cover.md"), meta
            )
            self.assertEqual(result, meta)

    def test_serve_port_default(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self.assertEqual(config_module.serve_port(deck), 8000)
            self._write(deck, "[deck]\nname = my-deck\n")
            self.assertEqual(config_module.serve_port(deck), 8000)

    def test_serve_port_configured_and_invalid(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[serve]\nport = 9000\n")
            self.assertEqual(config_module.serve_port(deck), 9000)
            self._write(deck, "[serve]\nport = abc\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.serve_port(deck)
            self.assertIn("integer", str(caught.exception))
            self._write(deck, "[serve]\nport = 70000\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.serve_port(deck)
            self.assertIn("65535", str(caught.exception))
            self._write(deck, "[serve]\nport = 0\n")
            with self.assertRaises(SystemExit):
                config_module.serve_port(deck)

    def test_bundled_example_config(self):
        loaded = config_module.load_deck(config_module.skill_root())
        self.assertEqual(loaded.name, "markdown-slides-examples")
        self.assertEqual(loaded.title, "Markdown Slides Examples")
        self.assertEqual(loaded.slides_rel, "examples/slides")
        self.assertEqual(
            loaded.slides,
            (config_module.skill_root() / "examples" / "slides").resolve(),
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
                self.assertEqual(
                    config_module.deck_root(argv=["prog"]),
                    deck,
                )
                other = deck
            with tempfile.TemporaryDirectory() as raw_argv:
                chosen = Path(raw_argv).resolve()
                with patch.dict(os.environ, {"DECK_ROOT": str(other)}):
                    self.assertEqual(
                        config_module.deck_root(
                            argv=["prog", "--deck-root", str(chosen)]
                        ),
                        chosen,
                    )
            with self.assertRaises(SystemExit):
                config_module.deck_root(
                    argv=["prog", "--deck-root", str(deck / "missing")]
                )


if __name__ == "__main__":
    unittest.main()
