---
name: markdown-slides
description: Create or edit a Markdown slide deck that builds onto a named HTML theme (default Swiss Modern). Use when the user wants a new deck, wants to keep this Markdown page dialect, or wants to change copy and slide order. Confirm the slides directory and git before writing pages, then commit sources before the HTML build.
---

# Markdown Slides

Build a deck from Markdown pages and the engine already in this skill. User project files are config.ini, Makefile, the slides directory, and build outputs. The engine stays in the skill. Do not copy scripts/ or templates/. Deck root resolution is --deck-root, else DECK_ROOT, else the skill root. Visual is `[build] theme` under `templates/` (default `templates/swiss-modern`). Do not restyle by editing HTML. Looks are frontend-slides presets ported into this skill. After the user picks a style with `/frontend-slides`, add `templates/<theme>` with `deck.css`, `deck.js`, and `pptx/`, then set `[build] theme`. Do not copy frontend-slides HTML into a deck.

## Before any page

Read references/design.md before creating slides. That file is the grammar: layouts, frontmatter, flags, card fields, and inline marks. Copy structure from the example pages when a new deck needs a starting set, then replace the copy.

If the prompt does not name a directory, ask in English and offer slides/ as the default. Store the choice in [deck] slides. Do not write slides until that choice is recorded. A path the prompt already names is the choice; record that path and do not ask again.

If the deck root is not a git work tree, ask in English before git init. If the user agrees, git init, ignore <name>.html, <name>.pptx, <name>.pdf, node_modules/, and .cache/, then commit the slide markdown, config.ini, and Makefile. If the user refuses, do not write slides and do not git init.

The bundled example already lives in this repository. Skip git init when building it. Its `[deck] slides` value is `examples/slides`. Build that example from the skill directory with `make html`. Do not write `[build] skill` for it.

`config.ini` in the deck root holds `[deck] name`, `[deck] title`, `[deck] slides`, the page-order keys, `[build] skill`, and `[build] theme`. `name` is the output basename and the storage key `markdown-slides:<name>`. `title` is the HTML document title. `slides` is the page directory relative to the deck root. Page order defaults to filename order of `NNN-slug.md` in that directory (`order = auto`). Set `sort = <file.md>` to a Markdown file whose `## Slides` links list the pages. Do not set `order` and `sort` together.

`[build] skill` is the markdown-slides directory (the one that contains `scripts/build-slides.py`). If the deck and the skill share a git tree, store a path relative to the deck root. Otherwise store the absolute path of this skill. `SKILL` or `MARKDOWN_SLIDES_HOME` overrides the ini value. Copy `templates/Makefile.deck` to the deck root as `Makefile`.

`[build] theme` selects a directory under `templates/` (default `templates/swiss-modern`). That directory holds `deck.css`, `deck.js`, and `pptx/`. The generator inlines Google Fonts into the HTML at build time (cache under `.cache/fonts/`). Viewing the deck does not request fonts.googleapis.com or fonts.gstatic.com. Do not restyle by editing HTML. To add a later look, add another directory there (from a frontend-slides pick) and point `theme` at it.

## Write, commit, then build

Write one Markdown file per slide under the recorded slides directory, named `NNN-slug.md`. Page order is that filename sort unless `[deck] sort` points at an index file.

Commit the sources before the build. Then run `make html` from the deck root so the cover stamp is not unknown. That Makefile forwards to the skill with `DECK_ROOT` set to the deck. The same targets are `make ppt` and `make pdf`. Commit the slide markdown, `config.ini`, and `Makefile`. Leave `<name>.html`, `<name>.pptx`, `<name>.pdf`, `node_modules/`, and `.cache/` untracked.

Later edits change Markdown, then commit, then rebuild. Do not hand-edit HTML. Do not rerun frontend-slides to change copy.

## Hotkeys

The stage script already implements these keys. Hotkeys: arrows change slides, F fullscreen, = / + and - zoom, 0 resets zoom and pan, #N opens slide N, E inline edit, Ctrl/Cmd+S saves.

| Key | Action |
|-----|--------|
| Arrow keys, Page Down, Space | Next slide |
| Arrow keys (left, up), Page Up | Previous slide |
| Home / End | First slide / last slide |
| `0`–`9` then Enter | Open that slide number (from 1) |
| Esc | Cancel a partial slide number; reset zoom when already zoomed |
| F | Fullscreen |
| `=` / `+` and `-` | Zoom in and out (about 1×–3×, on top of fit) |
| `0` while zoomed | Reset zoom and pan |
| Wheel | Change slides when fitted; pan when zoomed |
| Trackpad pinch / Ctrl+wheel | Zoom |
| Drag while zoomed | Pan |
| `#N` | Open slide N and keep the address bar in sync |
| E, or the hover pencil | Inline edit |
| Ctrl/Cmd+S | Save to localStorage and download the HTML |

## Cover version stamp

Point at examples/slides/010-cover.md as the version-stamp example (git describe --always --dirty written into the cover footer). The generator writes that stamp into every footer. Do not put the revision in the page Markdown. A build before the sources are committed prints `unknown`.
