"""Tests for slide order: filename auto, or meta.toml [deck] sort index."""

import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import isolated_env
import config as config_module
import slide_model

PAGE = "---\nlayout: cards\n---\n"


class TestSlideIndex(unittest.TestCase):
    def _deck(
        self,
        root: Path,
        slides_rel: str,
        pages: dict[str, str | bytes],
        index: str | None = None,
        config_text: str | None = None,
    ) -> Path:
        deck = Path(root)
        slides = deck / slides_rel
        slides.mkdir(parents=True, exist_ok=True)
        if index is not None:
            (slides / "index.md").write_text(index, encoding="utf-8")
            if config_text is None:
                config_text = f"[deck]\nslides = {slides_rel}\n"
        if "meta.toml" not in pages:
            name = Path(slides_rel).name
            title = name
            if config_text:
                found_name = re.search(r"(?m)^name\s*=\s*(\S+)\s*$", config_text)
                if found_name:
                    name = found_name.group(1)
                found_title = re.search(r"(?m)^title\s*=\s*(.+)$", config_text)
                if found_title:
                    title = found_title.group(1).strip()
            isolated_env.write_meta(
                slides,
                name,
                title,
                sort="index.md" if index is not None else "",
            )
        if config_text is not None:
            (deck / "config.ini").write_text(config_text, encoding="utf-8")
        for name, text in pages.items():
            target = slides / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(text, bytes):
                target.write_bytes(text)
            else:
                target.write_text(text, encoding="utf-8")
        return slides

    def _expect_fail(self, deck: Path, *needles: str) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit) as caught:
                slide_model.load_deck(deck)
        self.assertEqual(caught.exception.code, 1)
        err = buf.getvalue()
        for needle in needles:
            self.assertIn(needle, err)
        return err

    def _document_revision(self, root: Path, rel: str) -> str:
        def run(args: list[str]) -> subprocess.CompletedProcess[str] | None:
            try:
                return subprocess.run(
                    ["git", *args],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError:
                return None

        probe = run(["rev-parse", "--is-inside-work-tree"])
        if probe is None or probe.returncode != 0 or probe.stdout.strip() != "true":
            return "unknown"
        logged = run(["log", "-1", "--format=%H", "--", rel])
        commit = ""
        if logged is not None and logged.returncode == 0:
            commit = (logged.stdout or "").strip()
        if not commit:
            base = "unknown"
        else:
            described = run(["describe", "--always", commit])
            text = ""
            if described is not None and described.returncode == 0:
                text = (described.stdout or "").strip()
            base = text or "unknown"
        status = run(["status", "--porcelain", "--", rel])
        dirty = bool(
            status is not None and status.returncode == 0 and (status.stdout or "").strip()
        )
        if dirty and not base.endswith("-dirty"):
            base = f"{base}-dirty"
        return f"{rel}@{base}"

    def test_pages_load_in_filename_order_by_default(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {
                    "020-beta.md": PAGE,
                    "010-alpha.md": "---\nlayout: title\n---\n",
                    "index.md": "## Slides\n\n- [Beta](020-beta.md)\n",
                },
            )
            loaded = slide_model.load_deck(deck)
            self.assertEqual(
                [slide["file"] for slide in loaded["slides"]],
                ["010-alpha.md", "020-beta.md"],
            )
            self.assertEqual(loaded["total"], 2)

    def test_order_auto_matches_filename_sort(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {
                    "030-gamma.md": PAGE,
                    "010-alpha.md": PAGE,
                    "020-beta.md": PAGE,
                },
                config_text="[deck]\nslides = slides\n",
            )
            loaded = slide_model.load_deck(deck)
            self.assertEqual(
                [slide["slug"] for slide in loaded["slides"]],
                ["alpha", "beta", "gamma"],
            )

    def test_pages_load_in_listed_order(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "custom/pages",
                {
                    "010-alpha.md": "---\nlayout: title\n---\n",
                    "020-beta.md": PAGE,
                },
                (
                    "# Index\n\n"
                    "## Slides\n\n"
                    "- [Beta](020-beta.md)\n"
                    "- [Alpha](010-alpha.md)\n\n"
                    "## Notes\n\n"
                    "- [Ignored](999-nope.md)\n"
                ),
                "[deck]\nname = sample-deck\ntitle = Sample Title\nslides = custom/pages\n",
            )
            slide_model._GIT_DESCRIBE.clear()
            loaded = slide_model.load_deck(deck)
            self.assertEqual(loaded["name"], "sample-deck")
            self.assertEqual(loaded["title"], "Sample Title")
            self.assertEqual([slide["slug"] for slide in loaded["slides"]], ["beta", "alpha"])
            self.assertEqual(
                [slide["file"] for slide in loaded["slides"]],
                ["020-beta.md", "010-alpha.md"],
            )
            self.assertEqual(loaded["total"], 2)
            version = self._document_revision(deck, "custom/pages")
            self.assertEqual(loaded["version"], version)
            self.assertEqual(loaded["slides"][0]["stamp"], f"{version} · 01 / 02")
            self.assertEqual(loaded["slides"][1]["stamp"], f"{version} · 02 / 02")
            self.assertEqual(loaded["slides"][0]["index"], 1)
            self.assertEqual(loaded["slides"][1]["index"], 2)

    def test_slug_link_finds_numbered_file(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {
                    "010-cover.md": "---\nlayout: title\n---\n",
                    "020-body.md": PAGE,
                },
                "## Slides\n\n- [Cover](cover.md)\n- [Body](body.md)\n",
            )
            loaded = slide_model.load_deck(deck)
            self.assertEqual(loaded["slides"][0]["file"], "010-cover.md")
            self.assertEqual(loaded["slides"][0]["slug"], "cover")
            self.assertEqual(loaded["slides"][1]["file"], "020-body.md")
            self.assertEqual(loaded["slides"][1]["slug"], "body")
            slides = config_module.load_deck(deck).slides
            self.assertEqual(
                slide_model.resolve_page("cover", slides),
                slides / "010-cover.md",
            )

    def test_missing_link_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {"010-cover.md": PAGE},
                "## Slides\n\n- [Cover](010-cover.md)\n- [Gone](missing.md)\n",
            )
            index = config_module.load_deck(deck).slides / "index.md"
            self._expect_fail(deck, str(index), "missing.md")

    def test_duplicate_slug_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {"010-cover.md": PAGE, "020-cover.md": PAGE},
                "## Slides\n\n- [Cover](cover.md)\n",
            )
            slides = config_module.load_deck(deck).slides
            self._expect_fail(
                deck,
                str(slides),
                str(slides / "010-cover.md"),
                str(slides / "020-cover.md"),
            )

    def test_repeated_slug_in_index_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {"010-cover.md": PAGE},
                "## Slides\n\n- [Cover](cover.md)\n- [Again](010-cover.md)\n",
            )
            index = config_module.load_deck(deck).slides / "index.md"
            cover = config_module.load_deck(deck).slides / "010-cover.md"
            self._expect_fail(deck, str(index), str(cover))

    def test_missing_slides_heading_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {"010-cover.md": PAGE},
                "# Deck\n\n## 幻灯片\n\n- [Cover](010-cover.md)\n",
            )
            index = config_module.load_deck(deck).slides / "index.md"
            self._expect_fail(deck, str(index), "## Slides")

    def test_empty_slides_list_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(deck, "slides", {"010-cover.md": PAGE}, "## Slides\n\nNo pages yet.\n")
            index = config_module.load_deck(deck).slides / "index.md"
            self._expect_fail(deck, str(index), "empty")

    def test_git_failure_version_is_unknown(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(
                deck,
                "slides",
                {"010-cover.md": PAGE},
                "## Slides\n\n- [Cover](010-cover.md)\n",
            )
            slide_model._GIT_DESCRIBE.clear()

            def fake_run(cmd, **kwargs):
                self.assertEqual(cmd[0], "git")
                self.assertEqual(Path(kwargs["cwd"]).resolve(), deck.resolve())
                return subprocess.CompletedProcess(cmd, 128, "", "fatal: not a git repository")

            with patch("slide_model.subprocess.run", side_effect=fake_run):
                loaded = slide_model.load_deck(deck)
            self.assertEqual(loaded["version"], "unknown")
            self.assertEqual(loaded["slides"][0]["stamp"], "unknown · 01 / 01")

    def test_two_directories_get_different_revisions(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            self._deck(deck, "slides", {"010-cover.md": PAGE})
            self._deck(deck, "talk", {"010-cover.md": PAGE})
            env = os.environ.copy()
            env.update(
                {
                    "GIT_AUTHOR_NAME": "Test",
                    "GIT_AUTHOR_EMAIL": "test@example.com",
                    "GIT_COMMITTER_NAME": "Test",
                    "GIT_COMMITTER_EMAIL": "test@example.com",
                }
            )
            init = subprocess.run(
                ["git", "init"],
                cwd=deck,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            add = subprocess.run(
                ["git", "add", "slides", "talk"],
                cwd=deck,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(add.returncode, 0, add.stderr)
            commit = subprocess.run(
                ["git", "-c", "commit.gpgsign=false", "commit", "-m", "init"],
                cwd=deck,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(commit.returncode, 0, commit.stderr)
            slide_model._GIT_DESCRIBE.clear()
            slides = slide_model.git_describe(deck, "slides")
            talk = slide_model.git_describe(deck, "talk")
            self.assertTrue(slides.startswith("slides@"), slides)
            self.assertTrue(talk.startswith("talk@"), talk)
            self.assertNotEqual(slides, talk)

    def test_include_and_image_search_slide_dir_then_deck_root(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            body = (
                "---\nlayout: cards\n---\n\n"
                ":::card\n"
                "include: note.md\n"
                "image: pic.png\n"
                ":::\n\n"
                ":::card\n"
                "include: shared.md\n"
                "image: banner.png\n"
                ":::\n"
            )
            self._deck(
                deck,
                "slides",
                {
                    "010-cards.md": body,
                    "note.md": "FROM_SLIDE\n",
                    "pic.png": b"slide-png",
                },
                "## Slides\n\n- [Cards](010-cards.md)\n",
            )
            (deck / "note.md").write_text("FROM_ROOT\n", encoding="utf-8")
            (deck / "shared.md").write_text("FROM_DECK\n", encoding="utf-8")
            (deck / "banner.png").write_bytes(b"deck-png")
            legacy_includes = deck / "content" / "includes"
            legacy_includes.mkdir(parents=True)
            (legacy_includes / "note.md").write_text("FROM_LEGACY\n", encoding="utf-8")
            legacy_pages = deck / "content" / "pages"
            legacy_pages.mkdir(parents=True)
            (legacy_pages / "pic.png").write_bytes(b"legacy-png")

            loaded = slide_model.load_deck(deck)
            cards = loaded["slides"][0]["cards"]
            self.assertEqual(cards[0]["markdown"], "FROM_SLIDE\n")
            self.assertEqual(cards[0]["include"], "slides/note.md")
            self.assertEqual(cards[0]["image"]["src"], "slides/pic.png")
            self.assertEqual(cards[1]["markdown"], "FROM_DECK\n")
            self.assertEqual(cards[1]["include"], "shared.md")
            self.assertEqual(cards[1]["image"]["src"], "banner.png")

    def test_include_ignores_content_includes(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            body = "---\nlayout: cards\n---\n\n:::card\ninclude: note.md\n:::\n"
            slides = self._deck(
                deck,
                "slides",
                {"010-cards.md": body},
                "## Slides\n\n- [Cards](010-cards.md)\n",
            )
            legacy = deck / "content" / "includes"
            legacy.mkdir(parents=True)
            (legacy / "note.md").write_text("FROM_LEGACY\n", encoding="utf-8")
            self._expect_fail(deck, "note.md", str(slides))

    def test_include_parent_inside_deck_loads(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            body = "---\nlayout: cards\n---\n\n:::card\ninclude: ../note.md\n:::\n"
            self._deck(
                deck,
                "slides",
                {"010-cards.md": body},
                "## Slides\n\n- [Cards](010-cards.md)\n",
            )
            (deck / "note.md").write_text("FROM_PARENT\n", encoding="utf-8")
            loaded = slide_model.load_deck(deck)
            card = loaded["slides"][0]["cards"][0]
            self.assertEqual(card["markdown"], "FROM_PARENT\n")
            self.assertEqual(card["include"], "note.md")

    def test_include_parent_outside_deck_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            deck = parent / "deck"
            leaked = parent / "leaked-note.md"
            leaked.write_text("SECRET\n", encoding="utf-8")
            secret = parent / "secret.md"
            secret.write_text("ABSOLUTE\n", encoding="utf-8")
            outside = "---\nlayout: cards\n---\n\n:::card\ninclude: ../leaked-note.md\n:::\n"
            self._deck(
                deck,
                "slides",
                {"010-cards.md": outside},
                "## Slides\n\n- [Cards](010-cards.md)\n",
            )
            err = self._expect_fail(deck, "../leaked-note.md", str(leaked.resolve()))
            self.assertNotIn("SECRET", err)

            absolute = secret.resolve().as_posix()
            body = f"---\nlayout: cards\n---\n\n:::card\ninclude: {absolute}\n:::\n"
            (deck / "slides" / "010-cards.md").write_text(body, encoding="utf-8")
            err = self._expect_fail(deck, absolute, str(secret.resolve()))
            self.assertNotIn("ABSOLUTE", err)

    def test_empty_slides_dir_fails_in_auto(self):
        with tempfile.TemporaryDirectory() as raw:
            deck = Path(raw)
            slides = self._deck(deck, "slides", {})
            self._expect_fail(deck, str(slides), "no numbered slide")


class TestParseFrontmatter(unittest.TestCase):
    def test_strips_one_matching_quote_pair(self):
        text = '---\ntitle: "engineers\'"\nquote: "\'hello\'"\n---\n'
        meta, _body = slide_model.parse_frontmatter(text)
        self.assertEqual(meta["title"], "engineers'")
        self.assertEqual(meta["quote"], "'hello'")


if __name__ == "__main__":
    unittest.main()
