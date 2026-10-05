---
name: markdown-slides
disable-model-invocation: true
description: Create or edit a Markdown slide deck that builds onto a named HTML theme (default Swiss Modern). Use for /markdown-slides with no args, or create, edit, and theme. Infer whether to scaffold a deck or edit copy. Confirm the slides directory and git before first write. On create, plan in <slides>/references/plan.md and wait for approval before seeding pages. After generate, write <slides>/AGENTS.md with skill links, format summary, and build commands. Do not re-initialize a deck or overwrite existing slides with the example template. Optional theme copies go in themes/. For deep generator customization, install this skill in the project (typically .agents/skills/markdown-slides).
argument-hint: "[create | edit | theme]"
---

# Markdown Slides

Build a deck from Markdown pages and the engine already in this skill. User project files are config.ini, Makefile, build.py, the slides directory, and build outputs. The engine stays in the skill. Deck root resolution is --deck-root, else DECK_ROOT, else the skill root. Visual is `meta.toml` `theme`: first `themes/<theme>/` in the deck, else `templates/<theme>/` in the skill (default `templates/swiss-modern`). Do not restyle by editing HTML. Looks are frontend-slides presets ported into this skill. Do not copy frontend-slides HTML into a deck.

## Python environment

No PyPI packages are required for `make html` / `ppt` / `pdf` / `serve`. The engine uses the stdlib only. Optional `scripts/compress-images.py` needs Pillow if you run that helper; it is not part of the default build. Do not create a skill `.venv` unless you add a `requirements.txt` for optional tools.

## Commands

Read the extra words after `/markdown-slides`, or the user intent. If there is no extra word, **infer**:

- Deck **not** initialized → **create**
- Deck **initialized** → **edit** (ask what to change if the prompt is empty)
- Deep customization of the generator → install this skill in the project (typically `.agents/skills/markdown-slides`). Edit that tree; point `SKILL` / `MARKDOWN_SLIDES_HOME` at it when the trampoline should use that checkout.

| Command | Intent |
|---------|--------|
| (none) | Infer create vs edit as above |
| `create` / `init` | Scaffold trampoline files, write `<slides>/references/plan.md`, wait for plan approval, then seed and customize |
| `edit` | Change Markdown copy or page order only |
| `theme` | Copy a chosen look into the deck `themes/` directory |

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

If trampoline files exist, the slides directory has `meta.toml` and `<slides>/references/plan.md`, but **no** `NNN-slug.md` yet, stay in the plan phase: refine the plan until the user says it is ready, then run **Generate after plan approval**. Do not seed pages before that approval.

If trampoline files exist but the slides directory has **no** `NNN-slug.md` and **no** `references/plan.md`, create may start the plan phase. If any `NNN-slug.md` exists, skip the template copy even when the user says create.

If a `type = "slides"` directory already exists, that path is the choice; do not ask again unless the user named another directory.

## create

Read this skill's `references/design.md` before creating slides. That file is the grammar: layouts, frontmatter, flags, card fields, and inline marks. Do not confuse it with the deck's own `references/plan.md`.

If the prompt does not name a directory, ask in English and offer slides/ as the default. Do not write slides until that choice is recorded. A path the prompt already names is the choice; do not ask again.

If the deck root is not a git work tree, ask in English before git init. If the user agrees, git init, ignore build/, node_modules/, and .cache/, then commit the slide markdown, config.ini, Makefile, and build.py. If the user refuses, do not write slides and do not git init.

Stop if the deck is already initialized (see above). Say that it is already a markdown-slides deck and switch to edit.

Otherwise write only what is missing:

1. `config.ini` if absent. Set `[serve] port` (default `8000`). Optional `[paths] skills_root` and `build_root` (default `build`). Do not write `[deck]`.
2. Copy `templates/Makefile.deck` to the deck root as `Makefile` and `templates/build.py` as `build.py` if they are absent. Those two files stay identical to the copies under `markdown-pages/templates/`; sync both skills after trampoline edits.
3. Write `meta.toml` in the slides directory with `type = "slides"`, `name` (output basename), optional `title`, `theme =` (default `swiss-modern`), and `[deck] order = auto`.
4. **Plan then generate.** Follow the SOP below. Do not seed pages before the user approves the plan.

### Plan (required; stop before pages)

1. Ask for the document topic plan in the **user's preferred language** (audience, goal, outline, page list). Prefer AskQuestion when available for short choices; accept free-form outline text for the rest. Directory and git prompts stay in English as above.
2. Create `<slides>/references/` if needed and write `<slides>/references/plan.md` in that language. Include at least: title, audience, goal, and an ordered page outline (proposed `NNN-slug.md` filenames with `layout:` intent and one-line purpose each).
3. **Stop.** Tell the user to edit `references/plan.md` until satisfied. Do **not** seed `examples/slides/`, do **not** write `NNN-slug.md` pages, and do **not** run customize yet.
4. Resume only when the user clearly says the plan is ready (or pastes a final plan and asks you to generate).

### Generate after plan approval

1. Seed pages from `examples/slides/` `NNN-slug.md` into that directory **only when it has no `NNN-slug.md`**. Do not copy a template file over an existing page.
2. **Customize the seeded Markdown** using `<slides>/references/plan.md` as the outline source. Follow the customize SOP below before you treat create as done.
3. **Write `<slides>/AGENTS.md`** (required). Start from this skill `templates/AGENTS.md`. It must name **markdown-slides**, summarize the Markdown dialect, link this skill `SKILL.md` and `references/design.md` (fix relative paths for how the skill is installed), and list deck-root build commands for **this directory** (`make html <dir>`, `make ppt <dir>`, `make pdf <dir>`, `make serve`). Write it in the **user's preferred language**. `AGENTS.md` is not a slide. Do not skip this file.

### Customize seeded Markdown (required)

`examples/slides/` is the English engine self-test. Deployed decks must not ship that copy unchanged.

1. Keep the example **structure**: valid `NNN-slug.md` names, `layout:` values, frontmatter flags, and card/field shapes from this skill's `references/design.md`. Adjust the page set to match `references/plan.md` (add/remove/rename pages as the plan requires).
2. Rewrite **all visible copy** for the **user's topic** from `references/plan.md` (and any later user notes). Do not leave generic example marketing text.
3. Write that copy in the **user's preferred language** (conversation language, user rules, or locale). Directory and git prompts stay in English as above; `plan.md` and slide bodies must match the user's language. If the user asked for English, keep English.
4. Create is incomplete until every seeded page has been rewritten for topic and language. Do not stop after a byte-identical copy of `examples/slides/`.

## edit

Read references/design.md. Change Markdown under the recorded slides directory. Do not run create. Do not copy example pages onto existing files. Commit, then `make slides` from the deck root.

## theme

Use when the user wants a custom look, picked a bundled name, or finished `/frontend-slides`.

1. Resolve the source: a bundled directory under this skill `templates/<theme>/` (`swiss-modern`, `paper-ink`, `terminal-green`, `blue-professional`), or a new look the user just chose (add `deck.css`, `deck.js`, and `pptx/` there first; do not copy frontend-slides HTML).
2. Copy that directory to the deck `themes/<theme>/` (same folder names: `deck.css`, `deck.js`, `pptx/`). If `themes/<theme>/` already exists, ask before replacing it.
3. Set `theme =` in that directory's `meta.toml` to that name. The generator prefers the deck `themes/` copy over the skill `templates/` copy.
4. Restyle tokens in the deck copy. Do not restyle by editing HTML. Later `theme` commands must not clobber a customized `themes/<theme>/` without confirmation.

## Config and build

`config.ini` in the deck root holds `[serve]`, optional `[paths] skills_root` / `build_root`, and optional `[assets] webfont` (`off` by default). Each page directory has `meta.toml`: `type` must be `slides` for this skill (other types such as a future ebook are not built here), `name` is the output basename and the storage key `markdown-slides:<name>`, `title` is the HTML document title (defaults to `name`), and `theme =` names a look under deck `themes/` or skill `templates/`. Page order defaults to filename order of `NNN-slug.md` in that directory (`order = auto` in `meta.toml` `[deck]`). Set `sort = <file.md>` relative to that slides directory to a Markdown file whose `## Slides` links list the pages. Do not set `order` and `sort` together. Artifacts go under `[paths] build_root` (default `build/`).

The trampoline picks the engine from document `meta.toml` `type`, then `[paths] skills_root` / `markdown-slides`, else `.agents/skills/markdown-slides`, else `~/.agents/skills/markdown-slides`. `SKILL` / `MARKDOWN_SLIDES_HOME` overrides that lookup. For deep generator customization, install and edit the skill in the project (typically `.agents/skills/markdown-slides`). Optional `meta.toml` `[cover]` `presenter` and `presented_at` override those fields on `010-cover.md`.

Webfonts are off by default (system font stacks in theme CSS). Set `[assets] webfont = on` and run `make fonts` once to populate the skill `.cache/fonts/`; the HTML build then inlines that cache. Viewing never requests fonts.googleapis.com or fonts.gstatic.com. Missing cache with webfont on still builds with system fonts.

## Write, commit, then build

Write one Markdown file per slide under the recorded slides directory, named `NNN-slug.md`. Page order is that filename sort unless `meta.toml` `[deck] sort` points at an index file.

A project may hold more than one slides directory. Each has its own `meta.toml`. This skill builds only `type = "slides"`. Artifacts go under `build/<slides>/` as `<name>.html` / `.pptx` / `.pdf`. From the deck root, `make slides` builds HTML for `slides/`. PPTX and PDF need the directory: `make ppt slides` and `make pdf slides`. `make serve` serves `build/`. That Makefile runs `python3 build.py`, which finds the skill and forwards with `DECK_ROOT` set to the deck. Commit the slide markdown, `meta.toml`, `config.ini`, `Makefile`, `build.py`, and any vendored `themes/`. Leave `build/`, `node_modules/`, and `.cache/` untracked.

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
