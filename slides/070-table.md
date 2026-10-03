---
layout: table
overline: 表格
title: 三列表
summary: 单元格以 ! 开头会高亮，感叹号不显示。
---

| 文件 | 作用 | 入库 |
| --- | --- | --- |
| slides/*.md | 页面文案 | 要 |
| config.ini | 稿名与路径 | 要 |
| Makefile | `python3 build.py` | 要 |
| build.py | 解析 skill 并转发 | 要 |
| build/slides/*.html | 单文件舞台 | !不入库 |
