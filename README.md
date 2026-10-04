# markdown-publisher

This repository holds the **markdown-slides** and **markdown-pages** Agent Skills, plus a demo slide deck built with markdown-slides in this same repo. The publisher demo does not vendor either engine.

[中文](README.zh.md)

## Requirements

To run the skills (HTML build and `make` trampoline):

- **Python 3** (3.11 or newer)
- **Make** (GNU Make)
- **Python package `markdown`** for markdown-pages HTML

`make slides` and `make serve` use only Python. `make ppt` and `make pdf` also need **Node.js** (pages PDF uses Playwright Chromium or system Chrome). Quality targets (`make fmt`, `make lint`, `make test`) need `ruff` on PATH and `npm install` in both `skills/markdown-slides/` and `skills/markdown-pages/` (for markdownlint). Those quality targets run for **both** nested skills.

## Create slides with `/markdown-slides`

Install or attach the skill from [`skills/markdown-slides/`](skills/markdown-slides/) (see [`SKILL.md`](skills/markdown-slides/SKILL.md)). Commands: no extra words (infer create vs edit), `create`, `edit`, `theme`, `scripts`.

With **no extra words**, the skill inspects the project. If `config.ini`, the trampoline `Makefile` / `build.py`, and `NNN-slug.md` pages already exist, it **edits** and does not re-initialize or copy example pages over existing slides. If the project is not a deck yet, it **creates**.

Create (only when missing):

1. Choose a page directory (default `slides/` if you do not name one).
2. Write `config.ini` (`[serve]` only), a `Makefile` from `templates/Makefile.deck`, and `build.py` from `templates/build.py`. Write `meta.toml` (`type = "slides"`, `name`, optional `title`, `theme`, `[deck] order`) in the slides directory. Seed `NNN-slug.md` from `examples/slides/` only when that directory has no pages.
3. Nest this skill under `skills/markdown-slides` or set `SKILL`.
4. Commit those sources, then `make slides` from the **deck root** (HTML under `build/slides/`). Use `make ppt slides` and `make pdf slides` for those formats.

Later edits: change Markdown, commit, rebuild. Do not hand-edit the HTML.

## `config.ini` and `meta.toml`

Copy [`skills/markdown-slides/config.ini.example`](skills/markdown-slides/config.ini.example) or let the skill write the file. Each page directory has [`slides/meta.toml`](slides/meta.toml). `type` must be `slides` for this skill.

Project keys in `config.ini`:

| Section | Key | What to set |
|---------|-----|-------------|
| `[serve]` | `port` | `make serve` port. Default: `8000`. Document root is `build/`. |

Per-slides keys in that directory's `meta.toml`:

| Table | Key | What to set |
|-------|-----|-------------|
| (top) | `type`, `name`, `title` | Document kind (`slides`), output basename, HTML title. |
| (top) | `theme` | Look name. Deck `themes/<name>/` if complete, else skill `templates/`. Default: `swiss-modern`. Bundled also: `paper-ink`, `terminal-green`, `blue-professional`. |
| `[deck]` | `order` | `auto` (default): sort `NNN-slug.md` by filename. Do not set together with `sort`. |
| `[deck]` | `sort` | Optional Markdown file relative to the slides directory whose `## Slides` links list page order. |
| `[cover]` | `presenter`, `presented_at` | Optional cover overrides when a page is `010-cover.md`. |

## Skill

Path: [`skills/markdown-slides/`](skills/markdown-slides/).

It turns Markdown pages into a single-file HTML deck (PPTX and PDF as well). Dialect: [`skills/markdown-slides/references/design.md`](skills/markdown-slides/references/design.md). Agent workflow: [`skills/markdown-slides/SKILL.md`](skills/markdown-slides/SKILL.md).

The engine (`scripts/` in the skill, theme directories under `templates/`) stays in the skill by default. User decks keep `config.ini`, `Makefile`, `build.py`, slide Markdown, and build outputs. Optional: copy a look into deck `themes/`; copy `scripts/` into `scripts/markdown-slides/` only after confirmation.

## Initialize a book with `/markdown-pages`

Install or attach the skill from [`skills/markdown-pages/`](skills/markdown-pages/) (see [`SKILL.md`](skills/markdown-pages/SKILL.md)). The skill **only initializes** an ebook directory. Pass an optional directory name (default `pages/`). A project may hold several `type = "pages"` books. There are no `create` / `edit` / `scripts` subcommands.

Initialize (only when that directory is still empty of book sources):

1. Choose a book directory (default `pages/` if you do not name one). Another name starts another ebook in the same project.
2. Reuse the same trampoline `Makefile` / `build.py` as slides. Write `meta.toml` (`type = "pages"`, `name`, optional `title`, `[book] order`) in that directory. Seed chapters from `examples/pages/` only when the directory has no `README.md` and no numbered chapters.
3. Nest this skill under `skills/markdown-pages` or set `MARKDOWN_PAGES_HOME`.
4. Commit those sources, then `make html pages` from the **deck root** (multi-page site and one-file ebook under `build/pages/`). Use `make pdf pages` for PDF. `make ppt pages` is an error.

This publisher demo does not vendor `scripts/markdown-pages/`. Later chapter edits are ordinary Markdown work; do not re-run the skill to change copy in an existing book.

`examples/pages/` inside the skill is the English engine self-test book. `make html` in the skill directory builds that set. This repo’s root demo has no `pages/` book.

## Themes

Looks live in [`skills/markdown-slides/templates/`](skills/markdown-slides/templates/). They are **ports of frontend-slides presets** onto this Markdown dialect (same layouts and `:::card` grammar). They are not a copy of the frontend-slides HTML generator.

| `theme` in `meta.toml` | Use |
|-----------------|-----|
| `swiss-modern` | Teaching and engineering talks (default). White, black, signal red, visible grid. |
| `paper-ink` | Reports, literary, async reading. Cream paper, crimson, serif. |
| `terminal-green` | Developer / internal tech. Dark canvas, green, monospace. |
| `blue-professional` | Consulting and B2B. Cream paper, cobalt. |

Set the name in `meta.toml` `theme`. To customize a look in the project, copy `templates/<slug>/` to `themes/<slug>/` (the `/markdown-slides theme` command). To add another look: run `/frontend-slides` for visual discovery, then put `deck.css`, `deck.js`, and `pptx/` in deck `themes/<slug>/` or skill `templates/<slug>/`. Point `theme` at the name. Do not drop frontend-slides HTML into the deck.

The built HTML inlines webfonts. `make slides` may download Google Fonts once into `skills/markdown-slides/.cache/` (needs network). Opening the HTML does not. `make fonts` warms that cache. Without a cache and without a network, the build still succeeds and the deck uses system fonts instead of blocking on the CDN.

`examples/slides/` inside the skill is English engine self-test pages. `make html` in the skill directory builds that set.

## Demo deck in this repo

Root [`slides/`](slides/) **is** the skill’s example deck: generated here with markdown-slides, with the deck and the skill in one git repository.

| File | Role |
|------|------|
| [`slides/`](slides/) | Page sources, `NNN-slug.md`, ordered by filename |
| [`config.ini`](config.ini) | `[serve]` port; document root is `build/` |
| [`Makefile`](Makefile) | Thin wrapper: `python3 build.py <target>` |
| [`build.py`](build.py) | Finds nested skills by `meta.toml` `type` and forwards `make` with `DECK_ROOT` |

Build from the repo root:

```bash
make slides
```

That writes `build/slides/markdown-publisher.html` (not committed). `make ppt slides`, `make pdf slides`, and `make serve` work the same way. Edit Markdown only, commit, then rebuild. Do not hand-edit the HTML.
