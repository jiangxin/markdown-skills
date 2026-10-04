# Slide design

This file is the syntax source for a deck. The generator reads the layouts, frontmatter, blocks, and inline marks defined here. The stage size and color tokens live in `templates/<theme>/deck.css`; change those tokens together with this file when the visual system changes. The default theme is `swiss-modern`.

## Stage

- The stage is fixed at **1920×1080**. It scales to the viewport as a whole, letterboxing is allowed, and the layout does not reflow per device.
- Slides show and hide with `.active` and `.visible` (`visibility` and `opacity`). A slide is not hidden with `display: none`.
- A page does not scroll and must not overflow the frame. Split the content across pages instead of shrinking type outside the size steps. The exception is a card flagged `scroll`: that card scrolls, and the wheel does not advance the deck.

## Theme

The default `swiss-modern` look is white ground, black ink, signal red, with a visible grid. Chinese text uses Noto Sans SC, display titles use Archivo, body text uses Nunito, and code uses IBM Plex Mono. Other directories under `templates/` (for example `paper-ink`, `terminal-green`, `blue-professional`) keep this grammar and swap tokens in `deck.css`. Those looks are ports of frontend-slides presets, not copies of frontend-slides HTML.

| Role | Value |
|------|--------|
| Outside the stage | `#ffffff` (the gap around 16:9; fullscreen fills the screen) |
| Page ground | `#ffffff` |
| Ink | `#000000` |
| Muted | `#5a5a5a` |
| Grid line | `#e8e8e8` |
| Accent | `#ff3300` |
| Left bar | 14px, full height, accent |
| Frame padding | `48px 72px 44px 86px` |

Title and section pages paint an 80px grid. The left red bar is on every page.

## Page order

The generator and bundled stage live in the skill (`scripts/` and `templates/<theme>/`). By default a user deck does not copy those files. The trampoline resolves the skill from document `meta.toml` `type`, then `[paths] skills_root`, `.agents/skills/markdown-slides`, `~/.agents/skills/markdown-slides`, or `SKILL` / `MARKDOWN_SLIDES_HOME`. Each page directory has `meta.toml` with `type` (must be `slides` for this skill), `name`, optional `title`, `theme`, `[deck]` page-order keys, and optional `[cover]`. `theme` names a look (default `swiss-modern`): the generator reads `themes/<theme>/` in the deck when that copy is complete, otherwise `templates/<theme>/` in the skill. A project may contain several page directories. Artifacts are `build/<slides>/<name>.html` (and `.pptx` / `.pdf`). `make slides` builds HTML for that directory; `make ppt slides` and `make pdf slides` need the directory name. `make serve` serves `build/`. The deck `Makefile` and `build.py` are copied from either skill’s identical `templates/Makefile.deck` and `templates/build.py`. That script runs `make` in the skill with `DECK_ROOT` set to the deck. `SLIDES` selects a page directory.

The slides directory is `--slides` / `SLIDES`, or the only `type = "slides"` directory under the deck root.

Page order defaults to the filename sort of `NNN-slug.md` files in that directory. `index.md` and other files that do not match `NNN-slug.md` are not slides. Set `[deck] order = auto` in that directory's `meta.toml` to name that mode. Set `[deck] sort` to a Markdown file relative to the slides directory (for example `index.md`) to use a link list instead. Do not set `order` and `sort` together.

When `sort` is set, the generator walks Markdown links under the heading `## Slides` from top to bottom. A link target is a slug: an optional `NNN-` prefix, then lowercase letters, digits, and hyphens. The file on disk is `NNN-slug.md` in the slides directory, so a link written as `cover.md` resolves to `010-cover.md` when that file is the only `cover` slug. The link label is not read. A missing `## Slides` heading, an empty list, a missing file, or a duplicate slug is an error. The numeric prefix does not set the order in this mode.

Every footer ends with a stamp the generator writes from `git describe --always --dirty` in the deck root, plus the one-based index and the page total, each zero-padded to two digits. Do not author that stamp in the page. When git cannot describe the deck, the version text is `unknown`.

## Layouts

This table is the layout inventory. The generator renders these layouts and no others.

| layout | purpose |
|--------|---------|
| `title` | Cover or closing page: meta row, title, subtitle, badge, optional speaker and time |
| `section` | Chapter opener: a large number, a title, and a summary |
| `cards` | Card grid; `columns` is `2`, `3`, or `4` |
| `split` | Two equal columns; an image card sits full width under them |
| `stack-split` | A wide column beside a narrow stack; `slot: mid` adds a middle column |
| `table` | A Markdown table; a body cell that starts with `!` is highlighted |
| `table-cards` | A table stacked above a row of cards |

`layout` defaults to `cards` when the frontmatter omits it. Any other name is an error.

### `title`

The closing page uses the same layout as the cover. The generator draws, from top to bottom:

1. Meta row: `meta_left` and `meta_right`, small, tracked, muted.
2. Optional `eyebrow`.
3. The `title` as the main heading. A literal `\n` in the title becomes a line break. `title_size`, when set, is a CSS font-size on that heading, not a size step.
4. `subtitle`.
5. A 340×340 accent square: `badge_label` over `badge_text`. `badge_style` is optional inline CSS on the square. `badge_text` longer than six characters uses the compact square style.
6. Session lines, only when `presenter` or `presented_at` is set. The labels are Speaker and When.
7. The footer.

On a file named `010-cover.md`, a non-empty `[cover]` value for `presenter` or `presented_at` in that directory's `meta.toml` replaces the frontmatter value. Empty values do not.

### `section`

A large accent `number`, then the title, then `summary`, then the footer. This layout does not draw `overline`.

### `cards`

Content pages share one skeleton: red bar, then `overline`, title, optional `summary`, the body, then the footer.

`columns` is `2`, `3`, or `4`. The default is `2`. `columns: 1` is a single full-width column. Cards have a 2px ink border. `tone: filled` is an ink ground; `tone: red` is an accent ground.

An `image` card is placed in a full-width band under the grid, and it may share that band with `:::note`. Two exceptions keep the image in the grid: every card is an image, or `images_inline` is true (`true`, `1`, `yes`, or `on`).

`widths` describes that grid row as column weights, for example `20%,60%,20%`. The generator reads `widths` only when the list has at least two entries and the count equals the number of cards in the grid. Otherwise it ignores `widths` and warns. A percentage becomes a fractional track; a `fr` or `px` value is passed through as CSS.

If any card is `html-only`, the HTML deck shows only those cards, forces one column, and drops the band note.

### `split`

Two equal text columns. `widths` is not read. A card with `image` is not a third column: it is a full-width band under the pair. A band `:::note` is not drawn; use `:::note foot` for footer text.

### `stack-split`

The first card is the left column and later cards go right, unless a card sets `slot`. `slot` is `left`, `mid`, or `right` (any other value is treated as `right`). Cards that share a slot stack vertically in that column. Adding `slot: mid` makes three columns.

Without `widths`, two occupied columns use `1.15fr` and `0.85fr`, and three use `1.05fr`, `0.95fr`, and `1fr`. `widths` replaces those ratios when its length equals the number of occupied columns, in `left`, `mid`, `right` order, skipping an empty slot. Example: `35%,35%,30%`. Percentages are weights, same as on `cards`. A band `:::note` is not drawn.

### `table`

The body is a Markdown table, not a card. Body cells that start with `!` are highlighted, and the `!` is not shown. Header cells are not highlighted. `summary` sits under the title. `summary_after`, when set, is drawn under the table instead, and `summary` is omitted. `widths` sets each header cell's CSS `width` in column order; unlike the card grids, a percentage is not rewritten. A band `:::note` is not drawn.

### `table-cards`

The same table, then the cards. Optional `table_title` and `cards_title` label the two regions. `columns` defaults to `3` and follows the same `2`, `3`, `4` grid as `cards`. `widths` sizes the table columns the way `table` does. A band `:::note` is not drawn.

## Frontmatter

Frontmatter is a `---` block of `key: value` lines. A line that is empty, starts with `#`, or has no colon is skipped. The value is the rest of the line, with one layer of matching quotes removed. This is not full YAML: no nested maps and no multi-line values.

| Field | Where it is read | Meaning |
|-------|------------------|---------|
| `layout` | every page | One of the seven layouts; default `cards` |
| `title` | every page | Heading; `\n` becomes a line break; `<br>` also breaks |
| `summary` | `section`, `cards`, `split`, `stack-split`, `table`, `table-cards` | Lead under the title; hidden on `table` when `summary_after` is set |
| `columns` | `cards` (default `2`), `table-cards` (default `3`) | `2`, `3`, or `4`; `1` is one full-width column |
| `widths` | `cards`, `stack-split`, `table`, `table-cards` | Column weights; other layouts ignore it and warn |
| `text_size` | every page | Page size step: `s`, `l`, `xl`, or `xxl` |
| `presenter` | `title` | Speaker line; overridable from `[cover]` on `010-cover.md` |
| `presented_at` | `title` | When line; overridable from `[cover]` on `010-cover.md` |
| `footer` | every page | Small footer text; ignored when `:::note foot` is present, with a warning |
| `overline` | `cards`, `split`, `stack-split`, `table`, `table-cards` | Kicker above the title |
| `overline_style` | pages with `overline` | `auto` (default), `en`, or `cjk`; `cn` is `cjk` |
| `note_size` | `:::note` and `:::note foot` | Size step for the note; otherwise the note inherits `text_size` |
| `number` | `section` | Large chapter number |
| `images_inline` | `cards` | Keep image cards in the grid |
| `summary_after` | `table` | Lead under the table |
| `table_title` | `table-cards` | Label above the table |
| `cards_title` | `table-cards` | Label above the cards |
| `meta_left` `meta_right` | `title` | Top row |
| `subtitle` | `title` | Line under the title |
| `eyebrow` | `title` | Optional kicker above the title |
| `badge_label` `badge_text` | `title` | Two lines in the accent square |
| `badge_style` `title_size` | `title` | Optional raw CSS on the square and the title |

`overline_style: auto` uses `en` when the overline is entirely ASCII, and `cjk` otherwise.

Bare `http(s)` URLs and scheme-less hosts in `footer` become links. A footer may also contain a Markdown link.

## Blocks

A page is frontmatter plus `:::` blocks. The generator keeps one note per page: if several are written, the last one wins. A band note is rendered only on `cards`. `:::note foot` is drawn in the footer on every layout, including `title`.

```markdown
---
layout: cards
overline: Outline
title: Two columns
summary: A short lead under the title.
columns: 2
text_size: l
footer: Source note
---

:::card
num: "01"
title: First card
body: One sentence with `code` and an ==accent==.
:::

:::card filled
title: Second card
body: A filled card.
- First point
  - Nested point
:::

:::note
A band under the cards.
:::
```

`:::note foot` replaces `footer`. The note supports paragraphs and lists marked with a leading `-` or `*` and a space.

```markdown
:::note foot
A discussion line in the footer.
:::
```

`foot` may also be written `slot:foot` or `slot:footer`.

### Card flags

Flags are extra words on the opening line. The same fact can be written as a field inside the card. The generator accepts both.

| Flag on `:::card` | Same as |
|-------------------|---------|
| `filled` / `red` | `tone:` |
| `left` / `mid` / `right` | `slot:` |
| `s` / `l` / `xl` / `xxl` | `size:` |
| `marker` | `marker: on` |
| `inline-head` | `inline_head: on` |
| `scroll` | `scroll: on` |
| `html-only` | `html_only: on` |

| Flag on `:::note` | Meaning |
|-------------------|---------|
| `foot`, `slot:foot`, `slot:footer` | Draw the note in the footer |
| (none) | Band under the cards on `cards` only |

## Card fields

| Field | Meaning |
|-------|---------|
| `num` | Eyebrow or index |
| `title` | Card title |
| `body` | Paragraph text; several `body` lines become several paragraphs |
| `-` item | A list item (hyphen, then space); a deeper indent nests it; a nested item uses a hollow mark |
| `tone` | `filled` or `red` |
| `slot` | `left`, `mid`, or `right` (`stack-split`) |
| `size` | `s`, `l`, `xl`, or `xxl` |
| `marker` | `on` forces the square marks; `off` removes them; when omitted, marks appear only if the card has a `title` and no `num` |
| `inline_head` | `on` puts `num` and `title` on one row |
| `image` | Image path; see Paths |
| `alt` | Image alt text |
| `image_fit` | `contain` (default), `cover`, `fill`, `width`, or `height` |
| `image_height` | With `image_fit: width`, a CSS height such as `150%` |
| `image_max_height` | CSS max-height on the image |
| `image_max_width` | CSS max-width on the image |
| `include` | Markdown file read at build time and rendered inside the card |
| `scroll` | `on` lets the card scroll |
| `html_only` | On layout `cards` only, `on` keeps the card in the HTML deck; a page with any such card shows only those cards, forces one column, and drops the band note |
| `weight` | CSS `flex` grow for the card |
| `height` | CSS `min-height` for the card |

`marker: on` also accepts `true`, `1`, and `yes`. `marker: off` also accepts `false`, `0`, and `no`.

List marks are accent squares, and they turn white on `filled` and `red` cards.

## Inline syntax

These marks work in titles, summaries, card text, notes, table cells, and footer text.

| Mark | Result |
|------|--------|
| `**bold**` | Bold |
| `==accent==` | Accent-colored text |
| `` `code` `` | Monospace label |
| `[label](url)` | Link; opens in a new tab |
| `<br>` | Forced line break |

A table body cell may also start with `!` to highlight that cell.

## Size steps

Card and table type uses steps, not raw pixel sizes in the page source. The steps are `s`, `l`, `xl`, and `xxl`. An empty or unknown step is the default.

| Step | Number / title / body | Table body / table head | When to use |
|------|------------------------|-------------------------|-------------|
| `s` | 20 / 22 / 17 | 19 / 17 | Many cards, or long copy |
| default | 22 / 26 / 20 | 22 / 20 | Most pages |
| `l` | 24 / 32 / 25 | 27 / 24 | Few cards and more empty space |
| `xl` | 26 / 38 / 30 | 32 / 28 | Two or three cards, or a short table |
| `xxl` | 28 / 44 / 34 | 36 / 32 | A short quotation, often a `:::note` |

The nearer scope wins:

- The page: `text_size: l` in frontmatter. It applies to every card on the page, on any layout, and on `table` it also scales the table.
- One card: `:::card xl` or `size: xl` inside the card.
- The note: `note_size: xxl` in frontmatter, for both the band and `foot`. When it is omitted, the note uses the page `text_size`.

The generator maps a step to a class such as `text-l` and the variables in `templates/<theme>/deck.css`.

## Paths

`include` and `image` paths resolve from the slide file's directory, then from the deck root. The resolved file must stay inside the deck root. A relative `../` path is allowed when the file it names is still inside the deck. An absolute path is accepted when the resolved file stays inside the deck root, and rejected when the file is missing or the resolved path leaves the deck. A `../` path that leaves the deck is an error, and a missing file is an error.

The value stored for the page is the path relative to the deck root.
