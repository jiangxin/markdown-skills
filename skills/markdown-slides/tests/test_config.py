"""Tests for scripts/config.py."""

import contextlib
import io
import os
import shutil
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
            self.assertEqual(loaded.order, "auto")
            self.assertIsNone(loaded.sort)
            self.assertEqual(loaded.sort_rel, "")
            self.assertEqual(loaded.theme, "swiss-modern")
            self.assertEqual(
                loaded.theme_dir,
                (config_module.skill_root() / "templates" / "swiss-modern").resolve(),
            )

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
            self.assertEqual(loaded.order, "auto")
            self.assertIsNone(loaded.sort)

    def test_slides_env_selects_other_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nname = main-deck\nslides = slides\n")
            with patch.dict(os.environ, {"SLIDES": "talk"}, clear=False):
                loaded = config_module.load_deck(deck)
                paths = config_module.output_paths(deck)
            self.assertEqual(loaded.slides_rel, "talk")
            self.assertEqual(loaded.name, "talk")
            self.assertEqual(loaded.title, "talk")
            self.assertEqual(loaded.slides, (deck / "talk").resolve())
            self.assertEqual(paths.html, deck.resolve() / "build" / "talk" / "talk.html")

    def test_slides_env_matching_config_keeps_name(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nname = main-deck\ntitle = Main\nslides = slides\n")
            with patch.dict(os.environ, {"SLIDES": "slides"}, clear=False):
                loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.name, "main-deck")
            self.assertEqual(loaded.title, "Main")
            self.assertEqual(loaded.slides_rel, "slides")

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
            other = config_module.cover_overrides(deck, Path("slides/020-section.md"), meta)
            self.assertEqual(other, meta)
            self.assertIsNot(other, meta)
            cover = config_module.cover_overrides(deck, Path("slides/010-cover.md"), meta)
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
            result = config_module.cover_overrides(deck, Path("010-cover.md"), meta)
            self.assertEqual(result["presenter"], "A")
            self.assertEqual(result["presented_at"], "2026-10-03")

    def test_blank_cover_values_do_not_override(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[cover]\npresenter =   \npresented_at =\n")
            meta = {"presenter": "A", "presented_at": "B"}
            result = config_module.cover_overrides(deck, Path("010-cover.md"), meta)
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
        self.assertEqual(loaded.order, "auto")
        self.assertIsNone(loaded.sort)
        self.assertEqual(loaded.sort_rel, "")
        self.assertEqual(loaded.theme, "swiss-modern")
        self.assertEqual(
            loaded.theme_dir,
            (config_module.skill_root() / "templates" / "swiss-modern").resolve(),
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
                        config_module.deck_root(argv=["prog", "--deck-root", str(chosen)]),
                        chosen,
                    )
            with self.assertRaises(SystemExit):
                config_module.deck_root(argv=["prog", "--deck-root", str(deck / "missing")])

    def test_sort_path_is_relative_to_deck_root(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(
                deck,
                "[deck]\nslides = custom/pages\nsort = custom/pages/index.md\n",
            )
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.order, "")
            self.assertEqual(loaded.sort_rel, "custom/pages/index.md")
            self.assertEqual(
                loaded.sort,
                (deck / "custom" / "pages" / "index.md").resolve(),
            )

    def test_order_and_sort_together_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(
                deck,
                "[deck]\norder = auto\nsort = slides/index.md\n",
            )
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("order and sort", str(caught.exception))

    def test_invalid_order_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\norder = name\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("order", str(caught.exception))

    def test_absolute_sort_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            absolute = deck / "slides" / "index.md"
            self._write(deck, f"[deck]\nsort = {absolute}\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("sort", str(caught.exception))

    def test_sort_parent_escape_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[deck]\nsort = ../outside.md\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("escapes", str(caught.exception))

    def test_default_theme_is_swiss_modern(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.theme, "swiss-modern")
            self.assertTrue((loaded.theme_dir / "deck.css").is_file())

    def test_explicit_theme_must_exist_under_templates(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[build]\ntheme = missing-look\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("theme", str(caught.exception))

    def test_deck_themes_override_bundled_templates(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            source = config_module.skill_root() / "templates" / "paper-ink"
            dest = deck / "themes" / "paper-ink"
            shutil.copytree(source, dest)
            self._write(deck, "[build]\ntheme = paper-ink\n")
            loaded = config_module.load_deck(deck)
            self.assertEqual(loaded.theme, "paper-ink")
            self.assertEqual(loaded.theme_dir, dest.resolve())

    def test_incomplete_local_theme_falls_back_to_bundled(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            (deck / "themes" / "swiss-modern").mkdir(parents=True)
            (deck / "themes" / "swiss-modern" / "deck.css").write_text("/* incomplete */\n")
            loaded = config_module.load_deck(deck)
            self.assertEqual(
                loaded.theme_dir,
                (config_module.skill_root() / "templates" / "swiss-modern").resolve(),
            )

    def test_build_scripts_relative_inside_deck(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            scripts = deck / "scripts"
            scripts.mkdir()
            (scripts / "build-slides.py").write_text("# marker\n")
            self._write(deck, "[build]\nscripts = scripts\n")
            loaded = config_module.load_build_scripts(deck)
            self.assertEqual(loaded, scripts.resolve())

    def test_build_scripts_escape_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[build]\nscripts = ../outside\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_build_scripts(deck)
            self.assertIn("escapes", str(caught.exception))

    def test_build_scripts_missing_marker_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            (deck / "scripts").mkdir()
            self._write(deck, "[build]\nscripts = scripts\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_build_scripts(deck)
            self.assertIn("build-slides.py", str(caught.exception))

    def test_theme_rejects_path_separators(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[build]\ntheme = ../swiss-modern\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_deck(deck)
            self.assertIn("theme", str(caught.exception))

    def test_bundled_example_has_no_build_skill(self):
        skill = config_module.skill_root()
        loaded = config_module.load_build_skill(skill, environ={})
        self.assertIsNone(loaded)

    def test_build_skill_relative_may_leave_deck(self):
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            engine = parent / "engine"
            (engine / "scripts").mkdir(parents=True)
            (engine / "scripts" / "build-slides.py").write_text("# marker\n")
            deck = parent / "deck"
            deck.mkdir()
            self._write(deck, "[build]\nskill = ../engine\n")
            loaded = config_module.load_build_skill(deck, environ={})
            self.assertEqual(loaded, engine.resolve())

    def test_build_skill_absolute_path(self):
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            engine = parent / "engine"
            (engine / "scripts").mkdir(parents=True)
            (engine / "scripts" / "build-slides.py").write_text("# marker\n")
            deck = parent / "deck"
            deck.mkdir()
            self._write(deck, f"[build]\nskill = {engine.resolve()}\n")
            loaded = config_module.load_build_skill(deck, environ={})
            self.assertEqual(loaded, engine.resolve())

    def test_build_skill_tilde_expands(self):
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw) / "home"
            engine = home / "slides-engine"
            (engine / "scripts").mkdir(parents=True)
            (engine / "scripts" / "build-slides.py").write_text("# marker\n")
            deck = Path(raw) / "deck"
            deck.mkdir()
            self._write(deck, "[build]\nskill = ~/slides-engine\n")
            with patch.dict(os.environ, {"HOME": str(home)}, clear=False):
                loaded = config_module.load_build_skill(deck, environ={})
            self.assertEqual(loaded, engine.resolve())

    def test_build_skill_env_overrides_ini(self):
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            ini_engine = parent / "ini-engine"
            (ini_engine / "scripts").mkdir(parents=True)
            (ini_engine / "scripts" / "build-slides.py").write_text("#\n")
            env_engine = parent / "env-engine"
            (env_engine / "scripts").mkdir(parents=True)
            (env_engine / "scripts" / "build-slides.py").write_text("#\n")
            deck = parent / "deck"
            deck.mkdir()
            self._write(deck, "[build]\nskill = ../ini-engine\n")
            loaded = config_module.load_build_skill(deck, environ={"SKILL": str(env_engine)})
            self.assertEqual(loaded, env_engine.resolve())
            loaded = config_module.load_build_skill(
                deck, environ={"MARKDOWN_SLIDES_HOME": str(env_engine)}
            )
            self.assertEqual(loaded, env_engine.resolve())

    def test_build_skill_missing_marker_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            fake = parent / "not-engine"
            fake.mkdir()
            deck = parent / "deck"
            deck.mkdir()
            self._write(deck, "[build]\nskill = ../not-engine\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_build_skill(deck, environ={})
            self.assertIn("build-slides.py", str(caught.exception))

    def test_build_skill_missing_directory_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._write(deck, "[build]\nskill = ../gone\n")
            with self.assertRaises(SystemExit) as caught:
                config_module.load_build_skill(deck, environ={})
            self.assertIn("not a directory", str(caught.exception))

    def test_print_skill_cli(self):
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            engine = parent / "engine"
            (engine / "scripts").mkdir(parents=True)
            (engine / "scripts" / "build-slides.py").write_text("#\n")
            deck = parent / "deck"
            deck.mkdir()
            self._write(deck, "[build]\nskill = ../engine\n")
            saved = sys.argv
            buf = io.StringIO()
            try:
                sys.argv = ["config.py", "--print-skill", "--deck-root", str(deck)]
                with patch.dict(os.environ, {"SKILL": "", "MARKDOWN_SLIDES_HOME": ""}, clear=False):
                    with contextlib.redirect_stdout(buf):
                        config_module.main()
            finally:
                sys.argv = saved
            self.assertEqual(buf.getvalue().strip(), str(engine.resolve()))


if __name__ == "__main__":
    unittest.main()
