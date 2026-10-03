---
layout: table
overline: Config
title: Keys in config.ini
summary: The file sits at the deck root. Keep [build] skill relative when the skill shares the git tree.
---

| Section | Key | Meaning |
| --- | --- | --- |
| [deck] | name | Basename under `build/<slides>/` |
| [deck] | title | HTML document title |
| [deck] | slides | Page directory relative to the deck root |
| [deck] | order / sort | Page order; do not set both |
| [build] | skill | Engine directory (env vars may override) |
| [build] | theme | Deck `themes/` or skill `templates/` |
| [build] | scripts | Optional local engine copy |
| [serve] | port | `make serve` port, default 8000 |
