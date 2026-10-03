# Agent notes

This repo is two things in one git tree: the **markdown-slides** skill under `skills/markdown-slides/`, and a **demo deck** at the repo root (`slides/`, `config.ini`, `Makefile`).

Deck authoring follows `skills/markdown-slides/SKILL.md` and `skills/markdown-slides/references/design.md`. Do not copy `scripts/` or `templates/` into a deck. Do not restyle Swiss Modern. Do not hand-edit generated HTML.

## Quality

After changing Python or Markdown, run these from the **repo root**. Do not skip them.

```bash
make fmt
make lint
make test
```

`fmt` is `ruff format` on skill `scripts/` and `tests/`. `lint` is `ruff check`, `ruff format --check`, and `markdownlint-cli2` (skill docs, `examples/slides/`, plus this deck’s `README*.md` and `slides/*.md`). `test` is `python3 -m unittest discover` in the skill.

Needs `ruff` on PATH and `npm install` in `skills/markdown-slides/` (for `markdownlint-cli2`).

After editing the root demo, also `make html` from the repo root. Commit slide Markdown, `config.ini`, and `Makefile` before that build so the cover stamp is not `unknown`. Leave `markdown-publisher.html`, `.pptx`, `.pdf`, `node_modules/`, and `.cache/` untracked.

## Deployed deck files

The root Makefile and slide tree come from **using** the skill in this repo. Keep them aligned with the skill sources that generate them.

| Deck (repo root) | Skill source | Rule |
|------------------|--------------|------|
| `Makefile` | `skills/markdown-slides/templates/Makefile.deck` | Same file. If you change the trampoline, copy it to the root `Makefile`. Do not fork the trampoline in the deck. |
| `config.ini` | `skills/markdown-slides/config.ini.example` | Same keys and comments intent. This repo’s values: `slides = slides`, `skill = skills/markdown-slides`, `theme = swiss-modern`. |
| `slides/` | `skills/markdown-slides/examples/slides/` | Same page set and layouts (`NNN-slug.md`, same `layout:` values). Root `slides/` is the Chinese demo; `examples/slides/` is the English engine self-test. Do not treat them as byte-identical. A dialect or layout change belongs in `design.md` first, then both decks if they still demonstrate that layout. |

Do not add engine files next to the demo. `[build] skill` stays a path to `skills/markdown-slides`.
