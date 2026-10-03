# markdown-publisher

This repository holds both the **markdown-slides** Agent Skill and a demo deck built with that skill in this same repo.

[中文](README.zh.md)

## Requirements

To run the skill (HTML build and `make` trampoline):

- **Python 3** (3.11 or newer)
- **Make** (GNU Make)

`make html` and `make serve` use only Python. `make ppt` and `make pdf` also need **Node.js**. Quality targets (`make fmt`, `make lint`, `make test`) need `ruff` on PATH and `npm install` in `skills/markdown-slides/` (for markdownlint).

## Create slides with `/markdown-slides`

Install or attach the skill from [`skills/markdown-slides/`](skills/markdown-slides/) (see [`SKILL.md`](skills/markdown-slides/SKILL.md)). In the agent chat, invoke it with `/markdown-slides` and say you want a new deck.

The skill will:

1. Record `[deck] slides` (default `slides/` if you do not name a directory).
2. Write `NNN-slug.md` pages, `config.ini`, a `Makefile` copied from `templates/Makefile.deck`, and `build.py` copied from `templates/build.py`. It does **not** copy `scripts/` or theme templates.
3. Point `[build] skill` at this skill (a path relative to the deck if they share a git tree; otherwise an absolute path).
4. Commit those sources, then `make html` from the **deck root**.

Later edits: change Markdown, commit, rebuild. Do not hand-edit the HTML.

## `config.ini`

Copy [`skills/markdown-slides/config.ini.example`](skills/markdown-slides/config.ini.example) or let the skill write the file. Keys you usually change:

| Section | Key | What to set |
|---------|-----|-------------|
| `[deck]` | `name` | Output basename (`name.html` / `.pptx` / `.pdf`). Letters, digits, hyphens. Default: deck directory name. |
| `[deck]` | `title` | HTML document title. Default: `name`. |
| `[deck]` | `slides` | Slide directory relative to the deck root. Default: `slides`. |
| `[deck]` | `order` | `auto` (default): sort `NNN-slug.md` by filename. Do not set together with `sort`. |
| `[deck]` | `sort` | Optional Markdown file whose `## Slides` links list page order. |
| `[build]` | `skill` | Path to the markdown-slides directory (the one with `scripts/build-slides.py`). In this repo: `skills/markdown-slides`. Override with `SKILL` or `MARKDOWN_SLIDES_HOME`. Omit when you `make` from the skill directory itself. |
| `[build]` | `theme` | Directory under skill `templates/`. Default: `swiss-modern`. Bundled also: `paper-ink`, `terminal-green`, `blue-professional`. |
| `[cover]` | `presenter`, `presented_at` | Optional cover overrides when a page is `010-cover.md`. |
| `[serve]` | `port` | `make serve` port. Default: `8000`. |

## Skill

Path: [`skills/markdown-slides/`](skills/markdown-slides/).

It turns Markdown pages into a single-file HTML deck (PPTX and PDF as well). Dialect: [`skills/markdown-slides/references/design.md`](skills/markdown-slides/references/design.md). Agent workflow: [`skills/markdown-slides/SKILL.md`](skills/markdown-slides/SKILL.md).

The engine (`scripts/`, theme directories under `templates/`) stays in the skill. User decks keep `config.ini`, `Makefile`, `build.py`, slide Markdown, and build outputs.

## Themes

Looks live in [`skills/markdown-slides/templates/`](skills/markdown-slides/templates/). They are **ports of frontend-slides presets** onto this Markdown dialect (same layouts and `:::card` grammar). They are not a copy of the frontend-slides HTML generator.

| `[build] theme` | Use |
|-----------------|-----|
| `swiss-modern` | Teaching and engineering talks (default). White, black, signal red, visible grid. |
| `paper-ink` | Reports, literary, async reading. Cream paper, crimson, serif. |
| `terminal-green` | Developer / internal tech. Dark canvas, green, monospace. |
| `blue-professional` | Consulting and B2B. Cream paper, cobalt. |

Set the name in `[build] theme`. To add another look: run `/frontend-slides` for visual discovery, pick a style, then add `templates/<slug>/` with `deck.css`, `deck.js`, and `pptx/` (copy `swiss-modern` and restyle tokens). Point `[build] theme` at the new directory. Do not drop frontend-slides HTML into the deck.

The built HTML inlines webfonts. `make html` may download Google Fonts once into `skills/markdown-slides/.cache/` (needs network). Opening the HTML does not. `make fonts` warms that cache. Without a cache and without a network, the build still succeeds and the deck uses system fonts instead of blocking on the CDN.

`examples/slides/` inside the skill is English engine self-test pages. `make html` in the skill directory builds that set.

## Demo deck in this repo

Root [`slides/`](slides/) **is** the skill’s example deck: generated here with markdown-slides, with the deck and the skill in one git repository.

| File | Role |
|------|------|
| [`slides/`](slides/) | Page sources, `NNN-slug.md`, ordered by filename |
| [`config.ini`](config.ini) | `slides = slides`, `skill = skills/markdown-slides`, `theme = swiss-modern` |
| [`Makefile`](Makefile) | Thin wrapper: `python3 build.py <target>` |
| [`build.py`](build.py) | Resolves `[build] skill` and forwards `make` with `DECK_ROOT` |

Build from the repo root:

```bash
make html
```

That writes `markdown-publisher.html` (not committed). `make ppt`, `make pdf`, and `make serve` work the same way. Edit Markdown only, commit, then rebuild. Do not hand-edit the HTML.
