---
name: markdown-slides
description: Create or edit a Markdown slide deck that builds onto the existing Swiss Modern HTML stage. Use when the user wants a new presentation, wants to keep this Markdown page dialect, or wants to change copy and slide order in an existing slides directory.
---

# Markdown Slides

Build a deck from Markdown pages and the engine already in this skill. User project files are only `config.ini`, the slides directory, and build outputs. The engine stays in the skill. Deck root resolution is `--deck-root`, else `DECK_ROOT`, else the skill root. Visual is the existing Swiss Modern stage; do not restyle.

## Create a deck

Read `references/design.md` before creating slides. That note is the grammar for layouts, frontmatter, and the cover. Do not invent a new stage, typeface, or palette.

If the prompt does not name a directory, ask in English and offer `slides/` as the default. Store the choice in `[deck] slides`. Do not write slides until that choice is recorded. When the prompt already names a directory, use that path and record it the same way. `config.ini` in the deck root also holds `name` (output basename and storage key) and `title` (HTML document title).

If the deck root is not a git work tree, ask in English before git init. If the user agrees, git init, ignore `<name>.html`, `<name>.pptx`, `<name>.pdf`, `node_modules/`, and `.cache/`, then commit the slide markdown and `config.ini`. If the user refuses, do not write slides and do not git init.

Write `index.md` and one Markdown file per slide, following the layouts in `references/design.md`. A new deck may start from the bundled example pages and then replace the copy. The bundled example already lives in this repository. Skip git init when building it.

Commit the sources before the build. Then run `make html DECK_ROOT=<deck-root>` so the cover stamp is not unknown. Run that `make` from this skill directory. For PowerPoint or PDF, run `make ppt` or `make pdf` with the same `DECK_ROOT`. The generator runs `git describe --always --dirty` in the deck root and writes the result into the cover footer. Point at `examples/slides/010-cover.md` as the version-stamp example (`git describe --always --dirty` written into the cover footer).

Later edits change Markdown, then commit, then rebuild. Do not hand-edit HTML. Do not rerun frontend-slides to change copy.

## Hotkeys

The built HTML keeps the existing stage behavior:

| Key | Action |
| --- | --- |
| arrows | arrows change slides |
| `F` | F fullscreen |
| `=` / `+` and `-` | `=` / `+` and `-` zoom |
| `0` | 0 resets zoom and pan |
| `#N` | #N opens slide N |
| `E` | E inline edit |
| Ctrl/Cmd+S | Ctrl/Cmd+S saves |
