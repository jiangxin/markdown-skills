---
name: markdown-pages
disable-model-invocation: true
description: Initialize a Markdown ebook directory that builds to a multi-page site, a one-file HTML ebook, and PDF. Use for /markdown-pages. Confirm the book directory (default pages/) and git before first write. Plan in <book>/references/plan.md and wait for approval before seeding chapters. After generate, write <book>/AGENTS.md with skill links, format summary, and build commands. A project may hold several type=pages books. Do not re-initialize or overwrite an existing book directory with the example template. For deep generator customization, install this skill in the project (typically .agents/skills/markdown-pages).
argument-hint: "[directory]"
---

# Markdown Pages

Initialize a book directory of Markdown chapters. The engine already in this skill builds a multi-page HTML site under `build/<name>/pages/`, plus a one-file HTML ebook and PDF at `build/<name>/<name>.html` and `build/<name>/<name>.pdf`. User project files are config.ini, Makefile, build.py, one or more book directories, and build outputs. The engine stays in the skill. Deck root resolution is --deck-root, else DECK_ROOT, else the skill root. Do not restyle by editing HTML.

## What this skill does

This skill **only initializes** an ebook directory. Later chapter edits are ordinary Markdown work outside this skill. This skill does not copy the engine into the deck.

## Python environment (required)

The engine needs the PyPI package `markdown` (`requirements.txt`). Before initialize/generate work that will build, and before relying on `make html` / `make pdf`:

1. Resolve this skill root (`.agents/skills/markdown-pages`, `<deck>/skills/markdown-pages`, `MARKDOWN_PAGES_HOME`, or this checkout).
2. If `<skill>/.venv` is missing, create it: `python3 -m venv .venv` (or run `python3 scripts/ensure_venv.py` from the skill root).
3. Install deps into that venv from `requirements.txt` (`scripts/ensure_venv.py` does this and stamps `.venv/.requirements.sha256`).
4. Builds must use that interpreter. The skill `Makefile` runs `ensure-venv` then `.venv/bin/python scripts/build-pages.py`. Do not call `build-pages.py` with a bare system `python3` unless that environment already has `markdown`.

Leave `.venv/` untracked. Playwright Chromium remains optional for PDF when system Chrome is unavailable.

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

If the directory has `meta.toml` and `<book>/references/plan.md` but **no** home `README.md` and **no** numbered chapters yet:

- do **not** seed or customize chapters yet
- stay in the plan phase: refine `references/plan.md` with the user until they say the plan is ready
- only then run **Generate after plan approval**

Do not recopy `Makefile`, `build.py`, or `config.ini` unless the user asked to refresh those files.

## Initialize

Read this skill's `references/design.md` before writing pages. That file is the grammar: chapter names, home `README.md`, `meta.toml` keys, and link rewriting. Do not confuse it with the book's own `references/plan.md`.

If the deck root is not a git work tree, confirm before git init in the user's preferred language (prefer AskQuestion when available). If the user agrees, git init, ignore build/, node_modules/, and .cache/, then commit the chapter markdown, config.ini, Makefile, and build.py. If the user refuses, do not write pages and do not git init.

Otherwise write only what is missing for this initialization:

1. Ensure this skill's Python venv (see **Python environment** above): from the skill root run `python3 scripts/ensure_venv.py`.
2. `config.ini` if absent. Set `[serve] port` (default `8000`). Optional `[paths] skills_root` and `build_root` (default `build`). Do not write `[book]` in that file.
3. Copy this skill `templates/Makefile.deck` to the deck root as `Makefile` and `templates/build.py` as `build.py` if they are absent. Those two files stay identical to the copies under `markdown-slides/templates/`; sync both skills after trampoline edits. This skill `templates/book.css` is engine CSS; do not copy it into the deck on init.
4. Create the chosen book directory if needed. Write `meta.toml` with `type = "pages"`, `name` (output basename), optional `title`, and `[book] order = auto`.
5. **Plan then generate.** Follow the SOP below. Do not seed chapters before the user approves the plan.

### Plan (required; stop before chapters)

1. Ask for the document topic plan in the **user's preferred language** (audience, goal, outline, chapter list). Prefer AskQuestion when available for short choices; accept free-form outline text for the rest.
2. Create `<book>/references/` if needed and write `<book>/references/plan.md` in that language. Include at least: title, audience, goal, and an ordered chapter outline (a repository `README.md` summary, which is not compiled, plus `NN-slug.md` / `NNN-slug.md` filenames with one-line intent each).
3. **Stop.** Tell the user to edit `references/plan.md` until satisfied. Do **not** seed `examples/pages/`, do **not** write `README.md` or numbered chapters, and do **not** run customize yet.
4. Resume only when the user clearly says the plan is ready (or pastes a final plan and asks you to generate).

### Generate after plan approval

1. Seed chapters from `examples/pages/` into the book directory **only when it has no `README.md` and no `NN-slug.md` / `NNN-slug.md`**. Do not copy a template file over an existing chapter.
2. **Customize the seeded Markdown** using `<book>/references/plan.md` as the outline source. Follow the customize SOP below before you treat init as done.
3. **Write `<book>/AGENTS.md`** (required). Start from this skill `templates/AGENTS.md`. It must name **markdown-pages**, summarize the Markdown dialect, link this skill `SKILL.md` and `references/design.md` (fix relative paths for how the skill is installed), and list deck-root build commands for **this directory** (`make html <dir>`, `make pdf <dir>`, `make serve`). Write it in the **user's preferred language**. `AGENTS.md` is not a chapter. Do not skip this file.

### Customize seeded Markdown (required)

`examples/pages/` is the English engine self-test. Deployed books must not ship that copy unchanged.

1. Keep the example **structure**: repository `README.md` (not compiled), numbered `NN-slug.md` / `NNN-slug.md`, and the grammar from this skill's `references/design.md`. Adjust the page set to match `references/plan.md` (add/remove/rename numbered files as the plan requires; keep valid filenames).
2. Rewrite **all visible copy** for the **user's topic** from `references/plan.md` (and any later user notes). Do not leave generic example marketing text.
3. Write that copy in the **user's preferred language** (conversation language, user rules, or locale). Confirmations and `plan.md` already use that language; chapter bodies must match it. If the user asked for English, keep English.
4. Init is incomplete until every seeded chapter has been rewritten for topic and language. Do not stop after a byte-identical copy of `examples/pages/`.

## Config and build

`config.ini` in the deck root holds `[serve]`, optional `[paths] skills_root` / `build_root`, and optional `[assets] webfont` (`off` by default). Each book directory has `meta.toml`: `type` must be `pages` for this skill (other types such as slides are not built here), `name` is the output basename, `title` is the HTML document title (defaults to `name`). Chapter order defaults to filename order of `NN-slug.md` / `NNN-slug.md` in that directory (`order = auto` in `meta.toml` `[book]`). Set `sort = <file.md>` relative to that pages directory to a Markdown file whose heading links list the chapters. Do not set `order` and `sort` together. Artifacts go under `[paths] build_root` (default `build/`).

The trampoline picks the engine from document `meta.toml` `type`, then `[paths] skills_root` / `markdown-pages`, else `.agents/skills/markdown-pages`, else `~/.agents/skills/markdown-pages`. `MARKDOWN_PAGES_HOME` overrides that lookup. For deep generator customization, install and edit the skill in the project (typically `.agents/skills/markdown-pages`). PDF still uses skill-bundled browser tooling.

MathJax is vendored under `vendor/mathjax/` and copied into `build/<name>/assets/mathjax/` (no CDN). Chapter pages link to it as `../assets/`. The one-file HTML inlines CSS and links `assets/mathjax/` beside itself. Webfonts are off by default; set `[assets] webfont = on` and run `make fonts` to cache Google Fonts under the skill `.cache/fonts/`. HTML never links fonts.googleapis.com / fonts.gstatic.com / jsDelivr.

## After initialize

Write `README.md` as a short summary for people opening the repository. It is not compiled. Write one Markdown file per chapter under the book directory, named `NN-slug.md` or `NNN-slug.md`. Page order is that filename sort unless `meta.toml` `[book] sort` points at an index file. Keep `<book>/references/plan.md` as the authoring plan and `<book>/AGENTS.md` as agent guidance. `README.md` and `AGENTS.md` are not compiled into the site, the one-file HTML, or the PDF.

A project may hold more than one pages directory. Each has its own `meta.toml`. This skill builds only `type = "pages"`. Artifacts go under `build/<name>/`: the multi-page site in `pages/` (`index.html` and chapter pages), a one-file ebook `<name>.html`, and `<name>.pdf`. Build from the deck root: `make html <name>` builds HTML for that directory. `make pdf <name>` writes the PDF. `make serve` serves `build/`. That Makefile runs `python3 build.py`, which finds the skill and forwards with `DECK_ROOT` set to the deck; the skill Makefile then uses `.venv/bin/python` after `ensure-venv`. Commit the chapter markdown, `meta.toml`, `config.ini`, `Makefile`, and `build.py`. Leave `build/`, `node_modules/`, `.cache/`, and `.venv/` untracked.

Later chapter edits change Markdown, then commit, then rebuild. Do not hand-edit HTML. Do not re-run this skill to change copy in an existing book.

## Cover version stamp

The generator may write a git describe stamp into the built HTML. Do not put the revision in the chapter Markdown. A build before the sources are committed prints `unknown`.
