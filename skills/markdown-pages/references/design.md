# Book design

This file is the syntax source for a Markdown book. The generator reads the
chapter names, home page, and `meta.toml` keys defined here. Visual tokens
live with the engine templates in a later step; do not restyle by editing
generated HTML.

## Layout of sources

Chapters sit in a **flat** book directory. There is **no `docs/`**
subdirectory. The book directory is `--slides` / `SLIDES`, `--pages` /
`PAGES`, or the only `type = "pages"` directory under the deck root.

Do not scan `scripts/`, `skills/`, `build/`, `themes/`, or `.git` for
chapters.

## Home page

`README.md` is the home chapter. The generator writes it as `index.html`.
`index.md` is not the preferred home; use `README.md` so the source tree
matches a typical GitHub book.

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
files. `README.md` is always the home page and is not ordered among those
files. Set `[book] order = auto` to name that mode. Set `[book] sort` to a
Markdown file relative to the book directory to use a link list instead.

When `sort` is set, the generator walks Markdown links under a heading
(details in a later step, aligned with slides `## Slides` lists). Do not
set `order` and `sort` together.

## Artifacts

From the deck root, `make html <name>` writes a multi-page site and a
one-file ebook under `build/<name>/`. `make pdf <name>` writes
`build/<name>/<name>.pdf`. PPTX is not this skill.

In the multi-page site, `.md` links rewrite to `.html`. In the one-file
ebook, `.md` links rewrite to in-page anchors.

## Engine

The generator and templates live in this skill (`scripts/` and
`templates/` in later steps). By default a user deck does not copy those
files. Copy `scripts/` to `scripts/markdown-pages/` only after the user
confirms.
