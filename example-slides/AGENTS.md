# Agent 说明（本稿）

本目录是 **markdown-slides** 演示稿（`meta.toml` 中 `type = "slides"`）。
在此编辑页面 Markdown；不要手改 `build/` 下生成的 HTML。

## Skill

- 名称：`markdown-slides`
- 工作流：先找到已安装的 skill，再读其 `SKILL.md`
- 本仓库路径：[`../skills/markdown-slides/`](../skills/markdown-slides/)

参考链接：

- Skill SOP：[`../skills/markdown-slides/SKILL.md`](../skills/markdown-slides/SKILL.md)
- 语法（权威）：[`../skills/markdown-slides/references/design.md`](../skills/markdown-slides/references/design.md)

## Markdown 格式（概要）

- 扁平页面目录：每个页面一个 `NNN-slug.md`（三位数字前缀）
- `meta.toml` 与本 `AGENTS.md` **不是**幻灯片；`references/`（如 `plan.md`）也不是幻灯片
- 每页需要带合法 `layout:` 的 YAML frontmatter（见 dialect）
- 卡片用 `:::card` 及 dialect 中的字段；内容放进 1920×1080 舞台，溢出就拆页
- 默认按文件名排序（`[deck] order = auto`）；`theme =` 选择外观

版式、frontmatter、卡片字段与行内标记以 dialect 文件为准。

## 构建

在**稿根目录**（本目录的上一级）执行：

```bash
make example-slides
make ppt example-slides
make pdf example-slides
make serve
```

`make example-slides` 等同于 `make html example-slides`。产物在 `build/example-slides/`。
需要封面 git 版本戳时先提交再构建。`build/`、`node_modules/`、`.cache/` 不要入库。
