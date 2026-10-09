# Agent notes (this book)

This directory is a **markdown-pages** ebook (`type = "pages"` in `meta.toml`).
Edit chapter Markdown here; do not hand-edit generated HTML under `build/`.

## Skill

- Skill name: `markdown-pages`
- Workflow: resolve the installed skill, then read its `SKILL.md`
- Typical locations (first match wins for the trampoline):
  - `<deck>/skills/markdown-pages/` when `[paths] skills_root = skills`
  - `<deck>/.agents/skills/markdown-pages/`
  - `~/.agents/skills/markdown-pages/`

Replace the links below if this deck uses another skill path.

- Skill SOP: [`../skills/markdown-pages/SKILL.md`](../skills/markdown-pages/SKILL.md)
- Dialect (source of truth): [`../skills/markdown-pages/references/design.md`](../skills/markdown-pages/references/design.md)

## Markdown format (summary)

- Flat book directory: home `README.md` plus `NN-slug.md` or `NNN-slug.md` chapters.
- `meta.toml` and this `AGENTS.md` are **not** chapters. Authoring notes may live under `references/` (for example `plan.md`); that tree is not chapters.
- Chapter bodies are ordinary CommonMark (headings, lists, links, code fences).
- Do **not** use slide layouts, `layout:` frontmatter, or `:::card` fences.
- Order defaults to filename sort (`[book] order = auto`). Optional `[book] sort = <file.md>` uses a heading link list instead.

For filenames, home page rules, `meta.toml` keys, and link rewriting, follow the dialect file above.

## Build

From the **deck root** (parent of this directory), with trampoline `Makefile` / `build.py`:

```bash
make html <dir>
make pdf <dir>
make serve
```

Replace `<dir>` with this directory's name (for example `pages` or `example-pages`).
Artifacts go under `build/<dir>/pages/` (multi-page site) and `build/<dir>/<name>.html` / `<name>.pdf` (one-file HTML and PDF).
The skill Makefile creates `<skill>/.venv` from `requirements.txt` (`markdown`) via `scripts/ensure_venv.py`, then runs `.venv/bin/python`. Commit Markdown before building when you care about the git stamp. Leave `build/`, `node_modules/`, `.cache/`, and `.venv/` untracked.
