# Agent notes

This repo holds two Agent Skills and a **demo slide deck** in one git tree:

- **markdown-slides** under `skills/markdown-slides/`
- **markdown-pages** under `skills/markdown-pages/`
- the publisher demo at the repo root (`slides/`, `config.ini`, `Makefile`, `build.py`)

This demo vendors **no** engine: do not copy `scripts/` or theme templates into the publisher deck. Other projects may vendor a look into `themes/` (slides). For deep generator customization, install the skill in that project (typically `.agents/skills/markdown-slides` or `.agents/skills/markdown-pages`). Do not restyle by editing generated HTML.

Deck authoring follows `skills/markdown-slides/SKILL.md` and `skills/markdown-slides/references/design.md`. Do not re-initialize this deck or overwrite `slides/` with the English example template. Keep identity in `slides/meta.toml`. There is no required Chinese `pages/` demo book at the publisher root; the pages engine self-test is `skills/markdown-pages/examples/pages/`.

Book authoring follows `skills/markdown-pages/SKILL.md` and `skills/markdown-pages/references/design.md`. That skill **only initializes** an ebook directory (default `pages/`; more than one `type = "pages"` book is allowed). It has no `create` / `edit` / `scripts` subcommands. Do not vendor `scripts/markdown-pages/` into this publisher demo.

## Quality

After changing Python or Markdown, run these from the **repo root**. Do not skip them.

```bash
make fmt
make lint
make test
```

The trampoline runs those targets for **both** nested skills. `fmt` is `ruff format` (slides: skill `scripts/`, `tests/`, and `templates/build.py`; pages: skill `scripts/` and `tests/`). `lint` is `ruff check`, `ruff format --check`, and `markdownlint-cli2` (slides: skill docs and `examples/slides/`; pages: skill docs and `examples/pages/`; plus this deck’s `README*.md`, `AGENTS.md`, `slides/*.md`, and `pages/*.md` when present). `test` is `python3 -m unittest discover` in each skill. `make fonts` is slides-only.

Needs `ruff` on PATH and `npm install` in **each** of `skills/markdown-slides/` and `skills/markdown-pages/` (for `markdownlint-cli2`).

After editing the root demo, also `make slides` from the repo root. Commit slide Markdown, `config.ini`, `Makefile`, and `build.py` before that build so the cover stamp is not `unknown`. Leave `build/`, `node_modules/`, and `.cache/` untracked.

## Deployed deck files

The root trampoline and slide tree come from **using** the skills in this repo. Keep them aligned with the skill sources that generate them.

After dispatch changes, trampoline `build.py` stays identical to `skills/markdown-slides/templates/build.py`. If you change skill resolution, type dispatch, or quality forwarding, copy that template to the root `build.py`. Do not fork it in the deck.

| Deck (repo root) | Skill source | Rule |
|------------------|--------------|------|
| `Makefile` | `skills/markdown-slides/templates/Makefile.deck` | Same file. If you change the trampoline Makefile, copy it to the root `Makefile`. Do not fork it in the deck. |
| `build.py` | `skills/markdown-slides/templates/build.py` | Same file (including pages dispatch). Copy the template to the root after trampoline edits. |
| `config.ini` | `skills/markdown-slides/config.ini.example` | Same keys and comments intent. This repo keeps `[serve]` only. Theme, order, and cover live in `slides/meta.toml`. |
| `slides/` | `skills/markdown-slides/examples/slides/` | Same page set and layouts (`NNN-slug.md`, same `layout:` values). Root `slides/` is the Chinese demo; `examples/slides/` is the English engine self-test. Do not treat them as byte-identical. A dialect or layout change belongs in `design.md` first, then both decks if they still demonstrate that layout. |

Do not add engine files next to this demo. The trampoline finds `skills/markdown-slides` and `skills/markdown-pages` by `meta.toml` `type`. Do not vendor `scripts/` here. Custom looks for other decks go in that deck’s `themes/`.
