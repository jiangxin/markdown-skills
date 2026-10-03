---
layout: table
overline: 配置
title: config.ini 常改键
summary: 文件在稿根。skill 与稿同仓库时，[build] skill 用相对路径。
---

| 段 | 键 | 含义 |
| --- | --- | --- |
| [deck] | name | 产物基名：`name.html` / `.pptx` / `.pdf` |
| [deck] | title | HTML 文档标题 |
| [deck] | slides | 相对稿根的页面目录 |
| [deck] | order / sort | 页序；两键不要同时设 |
| [build] | skill | 引擎目录（可用环境变量覆盖） |
| [build] | theme | 稿 `themes/` 或 skill `templates/` |
| [build] | scripts | 可选，稿内引擎副本 |
| [serve] | port | `make serve` 端口，缺省 8000 |
