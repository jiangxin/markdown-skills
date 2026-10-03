---
layout: table
overline: 配置
title: config.ini 常改键
summary: 每套页面目录有 meta.toml。稿根 config.ini 只管预览服务。
---

| 文件 | 键 | 含义 |
| --- | --- | --- |
| meta.toml | type / name | `slides`；产物基名，写到 `build/<slides>/` |
| meta.toml | theme | 稿 `themes/` 或 skill `templates/` |
| meta.toml [deck] | order / sort | 页序；两键不要同时设 |
| meta.toml [cover] | presenter | 封面可选覆盖 |
| config.ini [serve] | port | `make serve` 端口；根是 `build/` |
