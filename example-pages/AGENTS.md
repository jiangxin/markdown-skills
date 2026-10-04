# Agent 说明（本书）

本目录是 **markdown-pages** 电子书（`meta.toml` 中 `type = "pages"`）。
在此编辑章节 Markdown；不要手改 `build/` 下生成的 HTML。

## Skill

- 名称：`markdown-pages`
- 工作流：先找到已安装的 skill，再读其 `SKILL.md`
- 本仓库路径：[`../skills/markdown-pages/`](../skills/markdown-pages/)

参考链接：

- Skill SOP：[`../skills/markdown-pages/SKILL.md`](../skills/markdown-pages/SKILL.md)
- 语法（权威）：[`../skills/markdown-pages/references/design.md`](../skills/markdown-pages/references/design.md)

## Markdown 格式（概要）

- 扁平书目录：首页 `README.md`，章节为 `NN-slug.md` 或 `NNN-slug.md`
- `meta.toml` 与本 `AGENTS.md` **不是**章节；`references/`（如 `plan.md`）也不是章节
- 正文为普通 CommonMark（标题、列表、链接、代码块）
- **不要**使用幻灯片 `layout:` 或 `:::card`
- 默认按文件名排序（`[book] order = auto`）

文件名、首页规则、`meta.toml` 键与链接改写以 dialect 文件为准。

## 构建

在**稿根目录**（本目录的上一级）执行：

```bash
make html example-pages
make pdf example-pages
make serve
```

产物在 `build/example-pages/`。skill 的 `Makefile` 会通过 `scripts/ensure_venv.py` 准备 `.venv`（安装 `requirements.txt` 里的 `markdown`），再用 `.venv/bin/python` 构建。需要 git 版本戳时先提交再构建。`build/`、`node_modules/`、`.cache/`、`.venv/` 不要入库。
