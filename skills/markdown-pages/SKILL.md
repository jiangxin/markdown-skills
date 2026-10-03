---
name: markdown-pages
description: Create or edit a Markdown book that builds to a multi-page site, a one-file HTML ebook, and PDF. Use for /markdown-pages with no args, or create, edit, and scripts. Infer whether to scaffold a book or edit copy. Confirm the pages directory and git before first write. Do not re-initialize a book or overwrite existing chapters with the example template. Copy scripts/markdown-pages/ only after the user confirms.
argument-hint: "[create | edit | scripts]"
---

# Markdown Pages

Build a book from Markdown chapters and the engine already in this skill. User project files are config.ini, Makefile, build.py, the pages directory, and build outputs. The engine stays in the skill unless the user later vendors scripts. Deck root resolution is --deck-root, else DECK_ROOT, else the skill root. Do not restyle by editing HTML. PPTX is not this skill; `make ppt` belongs to markdown-slides.

## Commands

Read the extra words after `/markdown-pages`, or the user intent. If there is no extra word, **infer**:

- Book **not** initialized → **create**
- Book **initialized** → **edit** (ask what to change if the prompt is empty)

There is no `theme` command in v1. One built-in book look lives with the engine.

| Command | Intent |
|---------|--------|
| (none) | Infer create vs edit as above |
| `create` / `init` | Scaffold trampoline files and, if the pages dir has no chapters, copy the example template |
| `edit` | Change Markdown copy or chapter order only |
| `scripts` | Copy the engine into the deck `scripts/markdown-pages/` so the user can patch it. **Ask the user to confirm before copying scripts.** |

The bundled example already lives in this repository. Skip git init when building it. Its chapters are `examples/pages` (`type = "pages"`). Build that example from the skill directory with `make html` (it selects the only `type = "pages"` directory). Do not write a skill path into `config.ini`.

## Initialized or not

Treat the current project (workspace / deck root) as **initialized** for this skill when all of these exist:

- `config.ini` with `[serve]` (optional; port defaults to 8000)
- `Makefile` and `build.py` (the trampoline copied from `skills/markdown-slides/templates/Makefile.deck` and `skills/markdown-slides/templates/build.py`)
- A page directory contains `meta.toml` with `type = "pages"` and a home `README.md` or at least one `NN-slug.md` / `NNN-slug.md`

If it is initialized:

- do not re-initialize. Do not recopy `Makefile`, `build.py`, or `config.ini` unless the user asked to refresh those files.
- Do not overwrite existing chapters with the example template. Never replace an existing `NN-slug.md` or `NNN-slug.md` with `examples/pages/`.
- Empty `/markdown-pages` is **edit**, not create.

If trampoline files exist but the pages directory has **no** chapter Markdown, create may seed the template. If any `NN-slug.md` or `NNN-slug.md` or `README.md` exists, skip the template copy even when the user says create.

If a `type = "pages"` directory already exists, that path is the choice; do not ask again unless the user named another directory.

## create

Read references/design.md before creating pages. That file is the grammar: chapter names, frontmatter-free Markdown, `meta.toml` keys, and link rewriting. Copy structure from the example chapters when a new book needs a starting set, then replace the copy.

If the prompt does not name a directory, ask in English and offer pages/ as the default. Do not write pages until that choice is recorded. A path the prompt already names is the choice; do not ask again.

If the deck root is not a git work tree, ask in English before git init. If the user agrees, git init, ignore build/, node_modules/, and .cache/, then commit the chapter markdown, config.ini, Makefile, and build.py. If the user refuses, do not write pages and do not git init.

Stop if the deck is already initialized (see above). Say that it is already a markdown-pages book and switch to edit.

Otherwise write only what is missing:

1. `config.ini` if absent. Set `[serve] port` (default `8000`). Do not write `[book]` or `[build]` in that file.
2. Copy `skills/markdown-slides/templates/Makefile.deck` to the deck root as `Makefile` and `skills/markdown-slides/templates/build.py` as `build.py` if they are absent. This skill `templates/book.css` is engine CSS; do not copy it on create.
3. Write `meta.toml` in the pages directory with `type = "pages"`, `name` (output basename), optional `title`, and `[book] order = auto`. Seed chapters from `examples/pages/` into that directory **only when it has no `README.md` and no `NN-slug.md` / `NNN-slug.md`**. Do not copy a template file over an existing chapter. Then replace the example copy with the user's topic.

`MARKDOWN_PAGES_HOME` selects an engine outside `skills/`. A nested `skills/markdown-pages` is discovered automatically.

## edit

Read references/design.md. Change Markdown under the recorded pages directory. Do not run create. Do not copy example chapters onto existing files. Commit, then `make html <name>` from the deck root (and `make pdf <name>` when a PDF is needed).

## scripts

By default do not copy `scripts/`. Use this command only when the user wants to patch the generator in the project.

1. State what will be copied (`scripts/` from this skill into the deck `scripts/markdown-pages/`). That nested path leaves `scripts/` free for other tools, including `scripts/markdown-slides/`. Keep the skill on `MARKDOWN_PAGES_HOME` or under `skills/` so PDF resources and tests still resolve bundled templates and `node_modules`.
2. Ask the user to confirm before copying scripts. If they refuse, stop. Do not copy.
3. If the deck already has `scripts/markdown-pages/build-pages.py`, ask before replacing those files.
4. After a yes: copy. The trampoline runs local html from that copy. Do not copy `tests/` or `templates/` unless the user asked for those too.

## Config and build

`config.ini` in the deck root holds `[serve]`. Each book directory has `meta.toml`: `type` must be `pages` for this skill (other types such as slides are not built here), `name` is the output basename and the storage key `markdown-pages:<name>`, `title` is the HTML document title (defaults to `name`). Chapter order defaults to filename order of `NN-slug.md` / `NNN-slug.md` in that directory (`order = auto` in `meta.toml` `[book]`). Set `sort = <file.md>` relative to that pages directory to a Markdown file whose heading links list the chapters. Do not set `order` and `sort` together.

The engine is this skill directory, a nested `skills/markdown-pages`, or `MARKDOWN_PAGES_HOME`. A deck-local `scripts/markdown-pages/` copy (must contain `build-pages.py`) runs html when present. PDF still uses skill-bundled browser tooling.

## Write, commit, then build

Write `README.md` as the home page and one Markdown file per chapter under the recorded pages directory, named `NN-slug.md` or `NNN-slug.md`. Page order is that filename sort unless `meta.toml` `[book] sort` points at an index file.

A project may hold more than one pages directory. Each has its own `meta.toml`. This skill builds only `type = "pages"`. Artifacts go under `build/<name>/` as a multi-page site (`index.html` and chapter pages), a one-file ebook `<name>.html`, and `<name>.pdf`. From the deck root, `make html <name>` builds HTML for that directory. `make pdf <name>` writes the PDF. `make serve` serves `build/`. That Makefile runs `python3 build.py`, which finds the skill and forwards with `DECK_ROOT` set to the deck. Commit the chapter markdown, `meta.toml`, `config.ini`, `Makefile`, `build.py`, and any vendored `scripts/markdown-pages/`. Leave `build/`, `node_modules/`, and `.cache/` untracked.

Later edits change Markdown, then commit, then rebuild. Do not hand-edit HTML.

## Cover version stamp

The generator may write a git describe stamp into the built HTML. Do not put the revision in the chapter Markdown. A build before the sources are committed prints `unknown`.
