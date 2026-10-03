---
layout: table
overline: 构建
title: 在稿根执行 Make
summary: 先提交 Markdown 与 config.ini，再构建，封面版本戳才不是 unknown。
summary_after: html / serve 只需 Python。ppt / pdf 还要 Node.js。产物不入库。
---

| 命令 | 产物 | 依赖 |
| --- | --- | --- |
| `make html` | `name.html` 单文件舞台 | Python |
| `make ppt` | `name.pptx` | Node.js |
| `make pdf` | `name.pdf` | Node.js |
| `make serve` | 本地预览 | Python |
| `make fonts` | 预热字体缓存 | 可选联网 |
