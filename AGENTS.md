# Agent notes

This repo is two things in one git tree: the **markdown-slides** skill under `skills/markdown-slides/`, and a **demo deck** at the repo root (`slides/`, `config.ini`, `Makefile`, `build.py`).

Deck authoring follows `skills/markdown-slides/SKILL.md` and `skills/markdown-slides/references/design.md`. This demo keeps the engine in the skill: do not copy `scripts/` or theme templates into the publisher deck. Other projects may vendor a look into `themes/` or, after confirmation, copy `scripts/`. Do not restyle by editing generated HTML. Do not re-initialize this deck or overwrite `slides/` with the English example template.

## Quality

After changing Python or Markdown, run these from the **repo root**. Do not skip them.

```bash
make fmt
make lint
make test
```

`fmt` is `ruff format` on skill `scripts/`, `tests/`, and `templates/build.py`. `lint` is `ruff check`, `ruff format --check`, and `markdownlint-cli2` (skill docs, `examples/slides/`, plus this deck’s `README*.md` and `slides/*.md`). `test` is `python3 -m unittest discover` in the skill.

Needs `ruff` on PATH and `npm install` in `skills/markdown-slides/` (for `markdownlint-cli2`).

After editing the root demo, also `make html` from the repo root. Commit slide Markdown, `config.ini`, `Makefile`, and `build.py` before that build so the cover stamp is not `unknown`. Leave `markdown-publisher.html`, `.pptx`, `.pdf`, `node_modules/`, and `.cache/` untracked.

## Deployed deck files

The root trampoline and slide tree come from **using** the skill in this repo. Keep them aligned with the skill sources that generate them.

| Deck (repo root) | Skill source | Rule |
|------------------|--------------|------|
| `Makefile` | `skills/markdown-slides/templates/Makefile.deck` | Same file. If you change the trampoline Makefile, copy it to the root `Makefile`. Do not fork it in the deck. |
| `build.py` | `skills/markdown-slides/templates/build.py` | Same file. If you change skill resolution or forwarding, copy it to the root `build.py`. |
| `config.ini` | `skills/markdown-slides/config.ini.example` | Same keys and comments intent. This repo’s values: `slides = slides`, `skill = skills/markdown-slides`, `theme = swiss-modern`. |
| `slides/` | `skills/markdown-slides/examples/slides/` | Same page set and layouts (`NNN-slug.md`, same `layout:` values). Root `slides/` is the Chinese demo; `examples/slides/` is the English engine self-test. Do not treat them as byte-identical. A dialect or layout change belongs in `design.md` first, then both decks if they still demonstrate that layout. |

Do not add engine files next to this demo. `[build] skill` stays a path to `skills/markdown-slides`. Do not set `[build] scripts` here. Custom looks for other decks go in that deck’s `themes/`.
