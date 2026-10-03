---
layout: cards
overline: 配置
title: 稿仓库里有什么
summary: 引擎不拷贝进来。页序默认按文件名。
columns: 2
text_size: s
note_size: xxl
---

:::card
num: "01"
title: 源文件
body: `config.ini`、`Makefile`、`build.py`、以及 `slides/` 下的 `NNN-slug.md`。行内可用 `code`、==强调==、**粗体**。
:::

:::card
num: "02"
title: 构建
body: 嵌套的 `skills/markdown-slides` 即引擎。主题写在 `meta.toml` 的 `theme`。在稿根运行 `make slides`。
:::

:::note
通栏提示：不要手改 HTML。
:::
