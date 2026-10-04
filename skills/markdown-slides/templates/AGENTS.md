# Agent notes (this deck)

This directory is a **markdown-slides** deck (`type = "slides"` in `meta.toml`).
Edit page Markdown here; do not hand-edit generated HTML under `build/`.

## Skill

- Skill name: `markdown-slides`
- Workflow: resolve the installed skill, then read its `SKILL.md`
- Typical locations (first match wins for the trampoline):
  - `<deck>/skills/markdown-slides/` when `[paths] skills_root = skills`
  - `<deck>/.agents/skills/markdown-slides/`
  - `~/.agents/skills/markdown-slides/`

Replace the links below if this deck uses another skill path.

- Skill SOP: [`../skills/markdown-slides/SKILL.md`](../skills/markdown-slides/SKILL.md)
- Dialect (source of truth): [`../skills/markdown-slides/references/design.md`](../skills/markdown-slides/references/design.md)

## Markdown format (summary)

- Flat slides directory: one `NNN-slug.md` file per page (three-digit prefix).
- `meta.toml` and this `AGENTS.md` are **not** slides. Authoring notes may live under `references/` (for example `plan.md`); those files are not slides.
- Each page needs YAML frontmatter with a valid `layout:` (see the dialect).
- Cards use `:::card` fences and the field grammar in the dialect. Keep content inside the 1920×1080 stage; split across pages instead of overflowing.
- Order defaults to filename sort (`[deck] order = auto`). Optional `[deck] sort = <file.md>` uses a `## Slides` link list instead.
- Optional `meta.toml` `theme =` selects `themes/<theme>/` in the deck or `templates/<theme>/` in the skill.

For layouts, frontmatter flags, card fields, and inline marks, follow the dialect file above.

## Build

From the **deck root** (parent of this directory), with trampoline `Makefile` / `build.py`:

```bash
make html <dir>
make ppt <dir>
make pdf <dir>
make serve
```

Replace `<dir>` with this directory's name (for example `slides` or `example-slides`).
`make <dir>` is the same as `make html <dir>`. Artifacts go under `build/<dir>/` as `<name>.html` / `.pptx` / `.pdf`.
Commit Markdown before building when you care about the cover git stamp. Leave `build/`, `node_modules/`, and `.cache/` untracked.
