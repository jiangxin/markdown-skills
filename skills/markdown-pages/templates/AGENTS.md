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

- Flat book directory: optional home `index.md`, then numbered `NN-slug.md` or `NNN-slug.md` chapters. A line that is only `[TOC]` in `index.md` is where the chapter list is inserted on the home page and in the one-file HTML. `README.md` is a repository summary and is not compiled. `meta.toml` and this `AGENTS.md` are not compiled either. Authoring notes may live under `references/` (for example `plan.md`); that tree is not chapters.
- Chapter bodies are ordinary CommonMark (headings, lists, links, code fences).
- Do **not** end a chapter with 「下一篇：」 or 「返回首页」. The multi-page HTML footer already links to the previous chapter, the next chapter, and home. The one-file HTML does not insert those lines between chapters.
- Order defaults to filename sort (`[book] order = auto`). Optional `[book] sort = <file.md>` uses a heading link list instead.

For filenames, home page rules, `meta.toml` keys, and link rewriting, follow the dialect file above.

## Voice

These rules apply only to reader-facing chapter copy in this directory. They do not apply to code, commit messages, or technical replies.

- Do not use: 「在……的时代」, 「不可否认」, 「总而言之」, 「宛如一幅画卷」, 「视觉盛宴」, 「值得注意的是」, Delve, Testament, Tapestry, It's important to remember, In conclusion. Do not open with a 总-分-总 frame. Do not close with a summary sermon.
- Mix sentence lengths. A short sentence, a question, or a spoken turn (老实说 / 其实不然) is allowed.
- Use first person. Name a concrete sensation, a number, or a specific snag. Do not summarize a mood from above.
- Keep one clear preference. Stop when the point is made.
- Do not define the point by rejecting an alternative (不是 A，而是 B). State what holds.
- Do not announce a count of equal parts (三条, 四件事) and then list them at matching length. A list still needs one sentence only this section can say.
- Do not repeat the heading in the next sentence.
- Do not write a lesson frame: handing the reader a map, 「读完应能判断」, or a closing recap of what this part taught. Name one example. Do not leave it as A 或 B.
- Do not stack abstract nouns (薄底座, 横切, 最小闭环, 可隔离、可停止、可复核). Name the thing.
- Do not end every page with the same sentence. A link to the next page is navigation. A repeated closer is not.

Machine:

> 这片风景令人心旷神怡，光线恰到好处。

Human:

> 清晨五点爬上山顶，手指冻得按快门都发僵。那道冷金色的逆光劈开云层时，连着喝三天的冷风都值了。

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
