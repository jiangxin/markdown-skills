# Book design

This file is the syntax source for a Markdown book. The generator reads the
chapter names, home page, and `meta.toml` keys defined here. Visual tokens
live with the engine templates in a later step; do not restyle by editing
generated HTML.

## Layout of sources

Chapters sit in a **flat** book directory. There is **no `docs/`**
subdirectory. The book directory is `--doc` / `DOC`, or the only
`type = "pages"` directory under the deck root.

Authoring notes may live under `<book>/references/` (for example
`plan.md`). That tree is not chapters. `README.md` in the book
directory is a summary for people opening the repository.
`AGENTS.md` is guidance for agents. Neither file is compiled into
the multi-page site, the one-file HTML, or the PDF. Only numbered
chapter files in the book directory are chapters.

Do not scan `scripts/`, `skills/`, `build/`, `themes/`, or `.git` for
chapters.

## Home page

`index.md` is the home page when that file exists. The generator writes
it to `pages/index.html`, and places the same text at the start of the
one-file HTML. A line that is only `[TOC]` marks where the chapter list
goes. Each entry is a chapter, with that chapter's level-2 and level-3
headings nested under it. The marker is replaced in both outputs:
chapter and heading links in the multi-page site, in-page anchors in
the one-file HTML. `[TOC]` inside a code fence stays literal. Numbered
chapters do not grow a chapter list from that marker.

When `index.md` is absent, `pages/index.html` is the book title plus the
numbered chapter list. The generator does not read `README.md` or
`AGENTS.md`. `README.md` is not the home page.

`meta.toml` is not a chapter.

## Chapter files

A chapter filename is `NN-slug.md` (two digits) or `NNN-slug.md` (three
digits): a numeric prefix, a hyphen, then a slug of lowercase letters,
digits, and hyphens. Examples: `01-intro.md`, `010-cover.md`.

Chapter Markdown is ordinary CommonMark (headings, lists, links, code
fences). This skill does not use slide layouts, card fences, or
frontmatter `layout:` keys.

## meta.toml

Each book directory has `meta.toml`:

| Key | Meaning |
| --- | --- |
| `type` | Must be `"pages"`. The slides skill does not build this directory. |
| `name` | Output basename under `build/<name>/`. Letters, digits, hyphens. |
| `title` | Book title for HTML. Defaults to `name` when omitted. |
| `[book] order` | `auto` sorts `NN-slug.md` and `NNN-slug.md` by filename. |
| `[book] sort` | Optional Markdown file, relative to the book directory, whose heading links set chapter order. Do not set `order` and `sort` together. |

`config.ini` at the deck root holds only `[serve]`. Book identity stays in
`meta.toml`.

## Page order

Page order defaults to the filename sort of `NN-slug.md` / `NNN-slug.md`
files. `README.md` and `AGENTS.md` are not ordered and are not compiled.
Set `[book] order = auto` to name that mode. Set `[book] sort` to a
Markdown file relative to the book directory to use a link list instead.

When `sort` is set, the generator walks Markdown links under a heading
(details in a later step, aligned with slides `## Slides` lists). Do not
set `order` and `sort` together.

## Artifacts

From the deck root, `make html <name>` writes the multi-page site to
`build/<name>/pages/` and the one-file ebook to
`build/<name>/<name>.html`. `make pdf <name>` writes
`build/<name>/<name>.pdf`. Shared CSS and MathJax stay in
`build/<name>/assets/`. PPTX is not this skill.

In the multi-page site, `.md` links rewrite to `.html`, and each chapter
page footer links to the previous chapter, the next chapter, and home.
In the one-file ebook, `.md` links rewrite to in-page anchors. Do not
end a chapter with `下一篇：` or `返回首页`. The builder drops a trailing
line that only says that, so it does not appear between chapters in the
one-file HTML or again under the multi-page footer.

## Engine

The generator and templates live in this skill (`scripts/` and
`templates/`). By default a user deck does not copy those files. The
trampoline resolves this skill from document `meta.toml` `type`, then
`[paths] skills_root`, `.agents/skills/markdown-pages`,
`~/.agents/skills/markdown-pages`, or `MARKDOWN_PAGES_HOME`. Deck-root
`Makefile` and `build.py` are identical copies from either skill's
`templates/Makefile.deck` and `templates/build.py`.
