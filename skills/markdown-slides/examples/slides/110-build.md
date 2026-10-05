---
layout: table
overline: Build
title: Make from the deck root
summary: Commit Markdown and config.ini first, then build, or the cover stamp is unknown.
summary_after: slides and serve need Python. ppt and pdf also need Node.js. Outputs stay untracked.
---

| Command | Output | Needs |
| --- | --- | --- |
| `make slides` | `build/slides/name.html` | Python |
| `make ppt slides` | `build/slides/name.pptx` | Node.js |
| `make pdf slides` | `build/slides/name.pdf` | Node.js |
| `make serve` | Local preview | Python |
| `make fonts` | Download webfonts into skill cache | Network; use with `webfont=on` |
