---
layout: table
overline: Build
title: Make from the deck root
summary: Commit Markdown and config.ini first, then build, or the cover stamp is unknown.
summary_after: html and serve need Python. ppt and pdf also need Node.js. Outputs stay untracked.
---

| Command | Output | Needs |
| --- | --- | --- |
| `make slides` | `build/slides/name.html` | Python |
| `make ppt slides` | `build/slides/name.pptx` | Node.js |
| `make pdf slides` | `build/slides/name.pdf` | Node.js |
| `make serve` | Local preview | Python |
| `make fonts` | Warm the font cache | Network optional |
