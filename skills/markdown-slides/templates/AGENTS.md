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

## Voice

These rules apply only to reader-facing slide copy in this directory. They do not apply to code, commit messages, or technical replies.

- Do not use: 「在……的时代」, 「不可否认」, 「总而言之」, 「宛如一幅画卷」, 「视觉盛宴」, 「值得注意的是」, Delve, Testament, Tapestry, It's important to remember, In conclusion. Do not open with a 总-分-总 frame. Do not close with a summary sermon.
- Mix sentence lengths. A short sentence, a question, or a spoken turn (老实说 / 其实不然) is allowed.
- Do not use first person singular (「我」). The copy is often written by more than one person. State the decision as the document's decision. Still name a concrete number or a specific snag. Do not summarize a mood from above.
- Keep one clear preference. Stop when the point is made.
- Do not define the point by rejecting an alternative (不是 A，而是 B). State what holds.
- Do not announce a count of equal parts (三条, 四件事) and then list them at matching length. A list still needs one sentence only this section can say.
- Do not repeat the heading in the next sentence.
- Do not write a lesson frame: handing the reader a map, 「读完应能判断」, or a closing recap of what this part taught. Name one example. Do not leave it as A 或 B.
- Do not stack abstract nouns (薄底座, 横切, 最小闭环, 可隔离、可停止、可复核). Name the thing.
- Do not end every page with the same sentence. A link to the next page is navigation. A repeated closer is not.
- Keep each page short. Do not expand a slide into an essay to satisfy sentence rhythm. The stage is 1920×1080.

Machine:

> 这片风景令人心旷神怡，光线恰到好处。

Human:

> 清晨五点，山顶气温零下。快门键上有霜。冷金色的逆光从云缝里切出来。

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
