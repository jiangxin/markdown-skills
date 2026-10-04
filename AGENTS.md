# Agent notes

This repo holds two Agent Skills and a **demo slide deck** in one git tree:

- **markdown-slides** under `skills/markdown-slides/`
- **markdown-pages** under `skills/markdown-pages/`
- the publisher demo at the repo root (`example-slides/`, `example-pages/`, `config.ini`, `Makefile`, `build.py`)

This demo vendors **no** engine: do not copy `scripts/` or theme templates into the publisher deck. Other projects may vendor a look into `themes/` (slides). For deep generator customization, install the skill in that project (typically `.agents/skills/markdown-slides` or `.agents/skills/markdown-pages`). Do not restyle by editing generated HTML.

Deck authoring follows `skills/markdown-slides/SKILL.md` and `skills/markdown-slides/references/design.md`. Do not re-initialize this deck or overwrite `example-slides/` with the English example template. Keep identity in `example-slides/meta.toml`. The Chinese pages demo is `example-pages/`; the pages engine self-test is `skills/markdown-pages/examples/pages/`.

Book authoring follows `skills/markdown-pages/SKILL.md` and `skills/markdown-pages/references/design.md`. That skill **only initializes** an ebook directory (default `pages/`; more than one `type = "pages"` book is allowed). It has no `create` / `edit` / `scripts` subcommands. Do not vendor `scripts/markdown-pages/` into this publisher demo.

## Quality

After changing Python or Markdown, run these from the **repo root**. Do not skip them.

```bash
make fmt
make lint
make test
```

The trampoline runs those targets for **both** nested skills. `fmt` is `ruff format` (slides: skill `scripts/`, `tests/`, and `templates/build.py`; pages: skill `scripts/`, `tests/`, and `templates/build.py`). `lint` is `ruff check`, `ruff format --check`, and `markdownlint-cli2` (slides: skill docs and `examples/slides/`; pages: skill docs and `examples/pages/`; plus this deck’s `README*.md`, `AGENTS.md`, `example-slides/*.md`, and `example-pages/*.md` when present). `test` is `python3 -m unittest discover` in each skill. `make fonts` is slides-only.

Needs `ruff` on PATH and `npm install` in **each** of `skills/markdown-slides/` and `skills/markdown-pages/` (for `markdownlint-cli2`).

After editing the root demo, also `make example-slides` from the repo root. Commit slide Markdown, `config.ini`, `Makefile`, and `build.py` before that build so the cover stamp is not `unknown`. Leave `build/`, `node_modules/`, and `.cache/` untracked.

## Deployed deck files

The root trampoline and slide tree come from **using** the skills in this repo. Keep them aligned with the skill sources that generate them.

### Shared trampoline (identical in both skills)

These two files are **byte-identical** across both skills. Edit one pair, then copy to the other skill’s `templates/` and to the project root. Do not fork them.

| File | markdown-slides | markdown-pages | Project root on install |
|------|-----------------|----------------|-------------------------|
| `build.py` | `skills/markdown-slides/templates/build.py` | `skills/markdown-pages/templates/build.py` | `build.py` |
| `Makefile` | `skills/markdown-slides/templates/Makefile.deck` | `skills/markdown-pages/templates/Makefile.deck` | `Makefile` |

Either skill may copy them to the deck root on init. After trampoline edits, sync all three copies (`templates/` in each skill + root).

### Engine lookup (`build.py`)

Document type comes from that directory’s `meta.toml` (`type = "slides"` or `type = "pages"`). Then resolve the skill that contains `scripts/`:

1. Explicit override: `SKILL` / `MARKDOWN_SLIDES_HOME` (slides) or `MARKDOWN_PAGES_HOME` (pages)
2. `config.ini` `[paths] skills_root` → `<skills_root>/<skill-name>/` (this demo uses `skills_root = skills`)
3. `<deck>/.agents/skills/<skill-name>/`
4. `~/.agents/skills/<skill-name>/`

Skill names are `markdown-slides` and `markdown-pages`. A valid skill has `scripts/build-slides.py` or `scripts/build-pages.py` plus `templates/`.

### Other deck alignment

| Deck (repo root) | Skill source | Rule |
|------------------|--------------|------|
| `config.ini` | `skills/markdown-slides/config.ini.example` (and pages example for the same keys) | Same keys and comments intent. This repo keeps `[serve]` and `[paths] skills_root = skills`. Optional `[paths] build_root` overrides the default `build/` artifact directory. Theme, order, and cover live in `example-slides/meta.toml`. |
| `example-slides/` | `skills/markdown-slides/examples/slides/` | Same page set and layouts (`NNN-slug.md`, same `layout:` values). Root `example-slides/` is the Chinese demo; `examples/slides/` is the English engine self-test. Do not treat them as byte-identical. A dialect or layout change belongs in `design.md` first, then both decks if they still demonstrate that layout. |
| `example-pages/` | `skills/markdown-pages/examples/pages/` | Chinese publisher demo book; skill `examples/pages/` stays the English engine self-test. |

Do not add engine files next to this demo. Custom looks for other decks go in that deck’s `themes/`.
