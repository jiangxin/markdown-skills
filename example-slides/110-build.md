---
layout: table
overline: 构建
title: 在稿根执行 Make
summary: 先提交 Markdown 与 config.ini，再构建，封面版本戳才不是 unknown。
summary_after: slides / serve 只需 Python。ppt / pdf 还要 Node.js。产物不入库。
---

| 命令 | 产物 | 依赖 |
| --- | --- | --- |
| `make example-slides` | `build/example-slides/name.html` | Python |
| `make ppt example-slides` | `build/example-slides/name.pptx` | Node.js |
| `make pdf example-slides` | `build/example-slides/name.pdf` | Node.js |
| `make serve` | 本地预览 | Python |
| `make fonts` | 下载 webfont 到 skill 缓存 | 需联网；配合 `webfont=on` |
