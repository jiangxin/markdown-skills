# markdown-publisher

本仓库既放 **markdown-slides** Agent Skill，也放一套用该 skill 在本仓库里生成的演示稿。

[English](README.md)

## 依赖

运行 skill（构建 HTML 和 Make 转发）需要：

- **Python 3**（3.11 或更新）
- **Make**（GNU Make）

`make html` 和 `make serve` 只用 Python。`make ppt` 和 `make pdf` 还需要 **Node.js**。质量检查（`make fmt`、`make lint`、`make test`）需要 PATH 上的 `ruff`，以及在 `skills/markdown-slides/` 里执行过 `npm install`（markdownlint）。

## 用 `/markdown-slides` 生成幻灯片

从 [`skills/markdown-slides/`](skills/markdown-slides/) 安装或挂上 skill（见 [`SKILL.md`](skills/markdown-slides/SKILL.md)）。在对话里输入 `/markdown-slides`，说明要新建一套稿。

Skill 会：

1. 记下 `[deck] slides`（未指定目录时默认 `slides/`）。
2. 写下 `NNN-slug.md`、`config.ini`，以及从 `templates/Makefile.deck` 拷来的 `Makefile`。**不会**拷贝 `scripts/` 或 `templates/`。
3. 把 `[build] skill` 指到本 skill（与稿同处一个 git 树时用相对路径，否则用绝对路径）。
4. 提交这些源文件，再在**稿根目录**执行 `make html`。

之后改 Markdown、提交、再构建。不要手改 HTML。

## `config.ini`

可复制 [`skills/markdown-slides/config.ini.example`](skills/markdown-slides/config.ini.example)，或让 skill 生成。常改的键：

| 段 | 键 | 含义 |
|----|----|------|
| `[deck]` | `name` | 产物基名（`name.html` / `.pptx` / `.pdf`）。仅字母、数字、连字符。缺省为稿目录名。 |
| `[deck]` | `title` | HTML 文档标题。缺省为 `name`。 |
| `[deck]` | `slides` | 相对稿根的幻灯片目录。缺省 `slides`。 |
| `[deck]` | `order` | `auto`（默认）按文件名排序 `NNN-slug.md`。不要与 `sort` 同时设置。 |
| `[deck]` | `sort` | 可选 Markdown，用其中 `## Slides` 的链接决定页序。 |
| `[build]` | `skill` | markdown-slides 目录（含 `scripts/build-slides.py`）。本仓库为 `skills/markdown-slides`。可用 `SKILL` 或 `MARKDOWN_SLIDES_HOME` 覆盖。在 skill 目录里直接 `make` 时可省略。 |
| `[build]` | `theme` | skill `templates/` 下的目录。缺省 `swiss-modern`。另有 `paper-ink`、`terminal-green`、`blue-professional`。 |
| `[cover]` | `presenter`、`presented_at` | 封面为 `010-cover.md` 时的可选覆盖。 |
| `[serve]` | `port` | `make serve` 端口。缺省 `8000`。 |

## Skill

路径：[`skills/markdown-slides/`](skills/markdown-slides/)。

用 Markdown 页面生成单文件 HTML 演示稿（也可出 PPTX / PDF）。语法见 [`skills/markdown-slides/references/design.md`](skills/markdown-slides/references/design.md)。Agent 用法见 [`skills/markdown-slides/SKILL.md`](skills/markdown-slides/SKILL.md)。

引擎（`scripts/`、`templates/`）留在 skill 里，不拷进稿仓库。用户稿只有 `config.ini`、`Makefile`、幻灯片 Markdown，以及构建产物。

## 主题

版式在 [`skills/markdown-slides/templates/`](skills/markdown-slides/templates/)。它们是把 **frontend-slides 的 preset** 迁到本 Markdown 方言（同一套 layout 和 `:::card`），不是拷贝 frontend-slides 的 HTML 生成器。

| `[build] theme` | 用途 |
|-----------------|------|
| `swiss-modern` | 教学 / 工程分享（默认）。白底、黑字、信号红、可见网格。 |
| `paper-ink` | 报告、文学、异步阅读。奶油纸、绯红、衬线。 |
| `terminal-green` | 开发者 / 内部技术会。深色底、终端绿、等宽。 |
| `blue-professional` | 咨询 / B2B。奶油纸、钴蓝。 |

在 `[build] theme` 里写目录名。要再加一种：用 `/frontend-slides` 做视觉挑选，然后在 `templates/<slug>/` 放入 `deck.css`、`deck.js`、`pptx/`（可从 `swiss-modern` 拷一份再改编配色）。把 `[build] theme` 指过去。不要把 frontend-slides 的 HTML 丢进稿仓库。

Skill 目录里的 `examples/slides/` 是引擎自测用的英文页。在 skill 目录执行 `make html` 会构建那一套。

## 本仓库的演示稿

根目录的 [`slides/`](slides/) 就是 skill 的示例演示稿：用 markdown-slides 在本项目里生成，稿和 skill 同处一个 git 仓库。

| 文件 | 作用 |
|------|------|
| [`slides/`](slides/) | 页面源文件，`NNN-slug.md`，顺序按文件名 |
| [`config.ini`](config.ini) | `slides = slides`，`skill = skills/markdown-slides`，`theme = swiss-modern` |
| [`Makefile`](Makefile) | 转发到 skill，设置 `DECK_ROOT` 为本仓库根 |

在仓库根目录构建：

```bash
make html
```

得到 `markdown-publisher.html`（不入库）。`make ppt`、`make pdf`、`make serve` 同样可用。改文案只改 Markdown，提交后再构建，不要手改 HTML。
