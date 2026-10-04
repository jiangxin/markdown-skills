---
name: markdown-pages
disable-model-invocation: true
description: Initialize a Markdown ebook directory that builds to a multi-page site, a one-file HTML ebook, and PDF. Use for /markdown-pages. Confirm the book directory (default pages/) and git before first write. A project may hold several type=pages books. Do not re-initialize or overwrite an existing book directory with the example template. For deep generator customization, install this skill in the project (typically .agents/skills/markdown-pages).
argument-hint: "[directory]"
---

# Markdown Pages

Initialize a book directory of Markdown chapters. The engine already in this skill builds a multi-page HTML site, a one-file HTML ebook, and PDF under `build/<name>/`. User project files are config.ini, Makefile, build.py, one or more book directories, and build outputs. The engine stays in the skill. Deck root resolution is --deck-root, else DECK_ROOT, else the skill root. Do not restyle by editing HTML.

## What this skill does

This skill **only initializes** an ebook directory. Later chapter edits are ordinary Markdown work outside this skill. This skill does not copy the engine into the deck.

Read the extra words after `/markdown-pages`, or the user intent:

- A path the prompt already names is the book directory.
- If the prompt does not name a directory, confirm in the user's preferred language before writing. Prefer AskQuestion when available: accept **`pages/`** as the default, or let the user name another directory. Do not write until that choice is recorded.
- A project may hold **more than one** ebook. Each book is its own directory with its own `meta.toml` (`type = "pages"`). Naming a new directory initializes another book; do not treat an existing book elsewhere as a reason to skip.
- Deep customization of the generator → install this skill in the project (typically `.agents/skills/markdown-pages`). Edit that tree; point `MARKDOWN_PAGES_HOME` at it when the trampoline should use that checkout.

The bundled example already lives in this repository. Skip git init when building it. Its chapters are `examples/pages` (`type = "pages"`). Build that example from the skill directory with `make html` (it selects the only `type = "pages"` directory).

## When to stop

If the chosen directory already has `meta.toml` with `type = "pages"` and a home `README.md` or at least one `NN-slug.md` / `NNN-slug.md`:

- do not re-initialize that directory
- do not overwrite existing chapters with `examples/pages/`
- say the book already exists and stop (or only add trampoline / `config.ini` at the deck root if those are still missing)

Do not recopy `Makefile`, `build.py`, or `config.ini` unless the user asked to refresh those files.

## Initialize

Read references/design.md before writing pages. That file is the grammar: chapter names, home `README.md`, `meta.toml` keys, and link rewriting. Copy structure from the example chapters when a new book needs a starting set, then replace the copy with the user's topic.

If the deck root is not a git work tree, confirm before git init in the user's preferred language (prefer AskQuestion when available). If the user agrees, git init, ignore build/, node_modules/, and .cache/, then commit the chapter markdown, config.ini, Makefile, and build.py. If the user refuses, do not write pages and do not git init.

Otherwise write only what is missing for this initialization:

1. `config.ini` if absent. Set `[serve] port` (default `8000`). Optional `[paths] skills_root`. Do not write `[book]` in that file.
2. Copy this skill `templates/Makefile.deck` to the deck root as `Makefile` and `templates/build.py` as `build.py` if they are absent. Those two files stay identical to the copies under `markdown-slides/templates/`; sync both skills after trampoline edits. This skill `templates/book.css` is engine CSS; do not copy it into the deck on init.
3. Create the chosen book directory if needed. Write `meta.toml` with `type = "pages"`, `name` (output basename), optional `title`, and `[book] order = auto`. Seed chapters from `examples/pages/` into that directory **only when it has no `README.md` and no `NN-slug.md` / `NNN-slug.md`**. Do not copy a template file over an existing chapter. Then replace the example copy with the user's topic.

## Config and build

`config.ini` in the deck root holds `[serve]` and optional `[paths] skills_root`. Each book directory has `meta.toml`: `type` must be `pages` for this skill (other types such as slides are not built here), `name` is the output basename, `title` is the HTML document title (defaults to `name`). Chapter order defaults to filename order of `NN-slug.md` / `NNN-slug.md` in that directory (`order = auto` in `meta.toml` `[book]`). Set `sort = <file.md>` relative to that pages directory to a Markdown file whose heading links list the chapters. Do not set `order` and `sort` together.

The trampoline picks the engine from document `meta.toml` `type`, then `[paths] skills_root` / `markdown-pages`, else `.agents/skills/markdown-pages`, else `~/.agents/skills/markdown-pages`. `MARKDOWN_PAGES_HOME` overrides that lookup. For deep generator customization, install and edit the skill in the project (typically `.agents/skills/markdown-pages`). PDF still uses skill-bundled browser tooling.

## After initialize

Write `README.md` as the home page and one Markdown file per chapter under the book directory, named `NN-slug.md` or `NNN-slug.md`. Page order is that filename sort unless `meta.toml` `[book] sort` points at an index file.

A project may hold more than one pages directory. Each has its own `meta.toml`. This skill builds only `type = "pages"`. Artifacts go under `build/<name>/` as a multi-page site (`index.html` and chapter pages), a one-file ebook `<name>.html`, and `<name>.pdf`. Build from the deck root: `make html <name>` builds HTML for that directory. `make pdf <name>` writes the PDF. `make serve` serves `build/`. That Makefile runs `python3 build.py`, which finds the skill and forwards with `DECK_ROOT` set to the deck. Commit the chapter markdown, `meta.toml`, `config.ini`, `Makefile`, and `build.py`. Leave `build/`, `node_modules/`, and `.cache/` untracked.

Later chapter edits change Markdown, then commit, then rebuild. Do not hand-edit HTML. Do not re-run this skill to change copy in an existing book.

## Cover version stamp

The generator may write a git describe stamp into the built HTML. Do not put the revision in the chapter Markdown. A build before the sources are committed prints `unknown`.
