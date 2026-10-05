---
layout: table
overline: Config
title: Keys in config.ini
summary: Each page directory has meta.toml. Project config.ini holds serve.
---

| File | Key | Meaning |
| --- | --- | --- |
| meta.toml | type / name | `slides`; basename under `build/<slides>/` |
| meta.toml | theme | Deck `themes/` or skill `templates/` |
| meta.toml [deck] | order / sort | Page order; do not set both |
| meta.toml [cover] | presenter | Optional cover override |
| config.ini [serve] | port | `make serve` port; root is `build/` |
| config.ini [assets] | webfont | Default off; on inlines local font cache |
