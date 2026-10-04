---
name: markdown-slides
disable-model-invocation: true
description: Create or edit a Markdown slide deck that builds onto a named HTML theme (default Swiss Modern). Use for /markdown-slides with no args, or create, edit, theme, and scripts. Infer whether to scaffold a deck or edit copy. Confirm the slides directory and git before first write. Do not re-initialize a deck or overwrite existing slides with the example template. Optional theme copies go in themes/. Copy scripts/markdown-slides/ only after the user confirms.
argument-hint: "[create | edit | theme | scripts]"
---

# Markdown Slides

Build a deck from Markdown pages and the engine already in this skill. User project files are config.ini, Makefile, build.py, the slides directory, and build outputs. The engine stays in the skill unless the user later vendors scripts. Deck root resolution is --deck-root, else DECK_ROOT, else the skill root. Visual is `meta.toml` `theme`: first `themes/<theme>/` in the deck, else `templates/<theme>/` in the skill (default `templates/swiss-modern`). Do not restyle by editing HTML. Looks are frontend-slides presets ported into this skill. Do not copy frontend-slides HTML into a deck.

## Commands

Read the extra words after `/markdown-slides`, or the user intent. If there is no extra word, **infer**:

- Deck **not** initialized → **create**
- Deck **initialized** → **edit** (ask what to change if the prompt is empty)

| Command | Intent |
|---------|--------|
| (none) | Infer create vs edit as above |
| `create` / `init` | Scaffold trampoline files and, if the slides dir has no pages, copy the example template |
| `edit` | Change Markdown copy or page order only |
| `theme` | Copy a chosen look into the deck `themes/` directory |
| `scripts` | Copy the engine into the deck `scripts/markdown-slides/` so the user can patch it. **Ask the user to confirm before copying scripts.** |

The bundled example already lives in this repository. Skip git init when building it. Its pages are `examples/slides` (`type = "slides"`). Build that example from the skill directory with `make html` (it selects the only `type = "slides"` directory). Do not write a skill path into `config.ini`.

## Initialized or not

Treat the current project (workspace / deck root) as **initialized** when all of these exist:

- `config.ini` with `[serve]` (optional; port defaults to 8000)
- `Makefile` and `build.py` (the trampoline copied from `templates/Makefile.deck` and `templates/build.py`)
- A page directory contains `meta.toml` with `type = "slides"` and at least one `NNN-slug.md`

If it is initialized:

- do not re-initialize. Do not recopy `Makefile`, `build.py`, or `config.ini` unless the user asked to refresh those files.
- Do not overwrite existing slides with the example template. Never replace an existing `NNN-slug.md` with `examples/slides/`.
- Empty `/markdown-slides` is **edit**, not create.

If trampoline files exist but the slides directory has **no** `NNN-slug.md`, create may seed the template. If any `NNN-slug.md` exists, skip the template copy even when the user says create.

If a `type = "slides"` directory already exists, that path is the choice; do not ask again unless the user named another directory.

## create

Read references/design.md before creating slides. That file is the grammar: layouts, frontmatter, flags, card fields, and inline marks. Copy structure from the example pages when a new deck needs a starting set, then replace the copy.

If the prompt does not name a directory, ask in English and offer slides/ as the default. Do not write slides until that choice is recorded. A path the prompt already names is the choice; do not ask again.

If the deck root is not a git work tree, ask in English before git init. If the user agrees, git init, ignore build/, node_modules/, and .cache/, then commit the slide markdown, config.ini, Makefile, and build.py. If the user refuses, do not write slides and do not git init.

Stop if the deck is already initialized (see above). Say that it is already a markdown-slides deck and switch to edit.

Otherwise write only what is missing:

1. `config.ini` if absent. Set `[serve] port` (default `8000`). Do not write `[deck]` or `[build]`.
2. Copy `templates/Makefile.deck` to the deck root as `Makefile` and `templates/build.py` as `build.py` if they are absent.
3. Write `meta.toml` in the slides directory with `type = "slides"`, `name` (output basename), optional `title`, `theme =` (default `swiss-modern`), and `[deck] order = auto`. Seed pages from `examples/slides/` `NNN-slug.md` into that directory **only when it has no `NNN-slug.md`**. Do not copy a template file over an existing page. Then replace the example copy with the user's topic.

`SKILL` or `MARKDOWN_SLIDES_HOME` selects an engine outside `skills/`. A nested `skills/markdown-slides` is discovered automatically.

## edit

Read references/design.md. Change Markdown under the recorded slides directory. Do not run create. Do not copy example pages onto existing files. Commit, then `make slides` from the deck root.

## theme

Use when the user wants a custom look, picked a bundled name, or finished `/frontend-slides`.

1. Resolve the source: a bundled directory under this skill `templates/<theme>/` (`swiss-modern`, `paper-ink`, `terminal-green`, `blue-professional`), or a new look the user just chose (add `deck.css`, `deck.js`, and `pptx/` there first; do not copy frontend-slides HTML).
2. Copy that directory to the deck `themes/<theme>/` (same folder names: `deck.css`, `deck.js`, `pptx/`). If `themes/<theme>/` already exists, ask before replacing it.
3. Set `theme =` in that directory's `meta.toml` to that name. The generator prefers the deck `themes/` copy over the skill `templates/` copy.
4. Restyle tokens in the deck copy. Do not restyle by editing HTML. Later `theme` commands must not clobber a customized `themes/<theme>/` without confirmation.

## scripts

By default do not copy `scripts/`. Use this command only when the user wants to patch the generator in the project.

1. State what will be copied (`scripts/` from this skill into the deck `scripts/markdown-slides/`). That nested path leaves `scripts/` free for other tools. Keep the skill on `SKILL` / `MARKDOWN_SLIDES_HOME` or under `skills/` so PPTX, PDF, fonts, and tests still resolve bundled templates and `node_modules`.
2. Ask the user to confirm before copying scripts. If they refuse, stop. Do not copy.
3. If the deck already has `scripts/markdown-slides/build-slides.py`, ask before replacing those files.
4. After a yes: copy. The trampoline runs local html and serve from that copy. Do not copy `tests/` or `templates/` unless a `theme` command also ran.

## Config and build

`config.ini` in the deck root holds `[serve]`. Each page directory has `meta.toml`: `type` must be `slides` for this skill (other types such as a future ebook are not built here), `name` is the output basename and the storage key `markdown-slides:<name>`, `title` is the HTML document title (defaults to `name`), and `theme =` names a look under deck `themes/` or skill `templates/`. Page order defaults to filename order of `NNN-slug.md` in that directory (`order = auto` in `meta.toml` `[deck]`). Set `sort = <file.md>` relative to that slides directory to a Markdown file whose `## Slides` links list the pages. Do not set `order` and `sort` together.

The engine is this skill directory, a nested `skills/markdown-slides`, or `SKILL` / `MARKDOWN_SLIDES_HOME`. A deck-local `scripts/markdown-slides/` copy (must contain `build-slides.py`) runs html and serve when present. Optional `meta.toml` `[cover]` `presenter` and `presented_at` override those fields on `010-cover.md`.

The generator inlines Google Fonts into the HTML at build time (cache under the engine `.cache/fonts/`). Viewing the deck does not request fonts.googleapis.com or fonts.gstatic.com.

## Write, commit, then build

Write one Markdown file per slide under the recorded slides directory, named `NNN-slug.md`. Page order is that filename sort unless `meta.toml` `[deck] sort` points at an index file.

A project may hold more than one slides directory. Each has its own `meta.toml`. This skill builds only `type = "slides"`. Artifacts go under `build/<slides>/` as `<name>.html` / `.pptx` / `.pdf`. From the deck root, `make slides` builds HTML for `slides/`. PPTX and PDF need the directory: `make ppt slides` and `make pdf slides`. `make serve` serves `build/`. That Makefile runs `python3 build.py`, which finds the skill and forwards with `DECK_ROOT` set to the deck. Commit the slide markdown, `meta.toml`, `config.ini`, `Makefile`, `build.py`, and any vendored `themes/` or `scripts/markdown-slides/`. Leave `build/`, `node_modules/`, and `.cache/` untracked.

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
