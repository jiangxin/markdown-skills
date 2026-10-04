# markdown-publisher

本仓库放 **markdown-slides** 和 **markdown-pages** 两套 Agent Skill，以及一套用 markdown-slides 在本仓库里生成的演示稿。publisher 演示稿不内嵌任何引擎拷贝。

[English](README.md)

## 依赖

运行 skill（构建 HTML 和 Make 转发）需要：

- **Python 3**（3.11 或更新）
- **Make**（GNU Make）
- markdown-pages 的 HTML 还需要 Python 包 **`markdown`**

`make slides` 和 `make serve` 只用 Python。`make ppt` 和 `make pdf` 还需要 **Node.js**（pages 的 PDF 用 Playwright Chromium 或本机 Chrome）。质量检查（`make fmt`、`make lint`、`make test`）需要 PATH 上的 `ruff`，以及在 `skills/markdown-slides/` 和 `skills/markdown-pages/` 里都执行过 `npm install`（markdownlint）。这些质量目标会对**两个**嵌套 skill 各跑一遍。

## 用 `/markdown-slides` 生成幻灯片

从 [`skills/markdown-slides/`](skills/markdown-slides/) 安装或挂上 skill（见 [`SKILL.md`](skills/markdown-slides/SKILL.md)）。命令：不加参数（推断创建或编辑）、`create`、`edit`、`theme`、`scripts`。

**不加参数**时先看工程：已有 `config.ini`、trampoline 的 `Makefile` / `build.py`、以及 `NNN-slug.md`，则只 **编辑**，不重复初始化，也不用示例页覆盖已有 slides。还不是一套稿时才 **创建**。

创建（只补缺的文件）：

1. 选定页面目录（未指定时默认 `slides/`）。
2. 写下 `config.ini`（只有 `[serve]`），从 `templates/Makefile.deck` 拷来的 `Makefile`，以及从 `templates/build.py` 拷来的 `build.py`。在页面目录写下 `meta.toml`（`type = "slides"`、`name`、可选 `title`、`theme`、`[deck] order`）。仅当页面目录里还没有 `NNN-slug.md` 时，才从 `examples/slides/` 播种。
3. 把本 skill 放在 `skills/markdown-slides`，或设置 `SKILL`。
4. 提交这些源文件，再在**稿根目录**执行 `make slides`（HTML 在 `build/slides/`）。PPT/PDF 用 `make ppt slides`、`make pdf slides`。

之后改 Markdown、提交、再构建。不要手改 HTML。

## `config.ini` 与 `meta.toml`

可复制 [`skills/markdown-slides/config.ini.example`](skills/markdown-slides/config.ini.example)，或让 skill 生成。每套页面目录有 [`slides/meta.toml`](slides/meta.toml)。本 skill 只构建 `type = "slides"`。

`config.ini` 里的工程级键：

| 段 | 键 | 含义 |
|----|----|------|
| `[serve]` | `port` | `make serve` 端口。缺省 `8000`。文档根是 `build/`。 |

该页面目录 `meta.toml` 里的稿级键：

| 表 | 键 | 含义 |
|----|----|------|
| （顶层） | `type`、`name`、`title` | 文档类型（`slides`）、产物基名、HTML 标题。 |
| （顶层） | `theme` | 主题名。稿内 `themes/<name>/` 完整则用之，否则 skill `templates/`。缺省 `swiss-modern`。另有 `paper-ink`、`terminal-green`、`blue-professional`。 |
| `[deck]` | `order` | `auto`（默认）按文件名排序 `NNN-slug.md`。不要与 `sort` 同时设置。 |
| `[deck]` | `sort` | 可选 Markdown，相对该页面目录，用其中 `## Slides` 的链接决定页序。 |
| `[cover]` | `presenter`、`presented_at` | 封面为 `010-cover.md` 时的可选覆盖。 |

## Skill

路径：[`skills/markdown-slides/`](skills/markdown-slides/)。

用 Markdown 页面生成单文件 HTML 演示稿（也可出 PPTX / PDF）。语法见 [`skills/markdown-slides/references/design.md`](skills/markdown-slides/references/design.md)。Agent 用法见 [`skills/markdown-slides/SKILL.md`](skills/markdown-slides/SKILL.md)。

引擎（skill 里的 `scripts/`、`templates/` 下的主题目录）默认留在 skill 里。用户稿只有 `config.ini`、`Makefile`、`build.py`、幻灯片 Markdown，以及构建产物。可选：把外观拷到稿的 `themes/`；拷 `scripts/` 到 `scripts/markdown-slides/` 前必须确认。

## 用 `/markdown-pages` 初始化电子书

从 [`skills/markdown-pages/`](skills/markdown-pages/) 安装或挂上 skill（见 [`SKILL.md`](skills/markdown-pages/SKILL.md)）。该 skill **只负责初始化**电子书目录。可传目录名（默认 `pages/`）。同一项目里可以有多本 `type = "pages"` 的书。没有 `create` / `edit` / `scripts` 子命令。

初始化（该书目录尚无书源时才写）：

1. 选定书目录（未指定时默认 `pages/`）。换一个目录名即可再开一本。
2. 复用与 slides 相同的 trampoline `Makefile` / `build.py`。在该书目录写下 `meta.toml`（`type = "pages"`、`name`、可选 `title`、`[book] order`）。仅当目录里还没有 `README.md` 和带编号的章节时，才从 `examples/pages/` 播种。
3. 把本 skill 放在 `skills/markdown-pages`，或设置 `MARKDOWN_PAGES_HOME`。
4. 提交这些源文件，再在**稿根目录**执行 `make html pages`（多页站点和单文件 HTML 在 `build/pages/`）。PDF 用 `make pdf pages`。`make ppt pages` 会失败。

本仓库演示稿不内嵌 `scripts/markdown-pages/`。之后改章节就是改 Markdown，不要为改文案再跑一遍本 skill。

Skill 目录里的 `examples/pages/` 是引擎自测用的英文小书。在 skill 目录执行 `make html` 会构建那一套。本仓库根目录没有 `pages/` 演示书。

## 主题

版式在 [`skills/markdown-slides/templates/`](skills/markdown-slides/templates/)。它们是把 **frontend-slides 的 preset** 迁到本 Markdown 方言（同一套 layout 和 `:::card`），不是拷贝 frontend-slides 的 HTML 生成器。

| `theme`（`meta.toml`） | 用途 |
|-----------------|------|
| `swiss-modern` | 教学 / 工程分享（默认）。白底、黑字、信号红、可见网格。 |
| `paper-ink` | 报告、文学、异步阅读。奶油纸、绯红、衬线。 |
| `terminal-green` | 开发者 / 内部技术会。深色底、终端绿、等宽。 |
| `blue-professional` | 咨询 / B2B。奶油纸、钴蓝。 |

在 `meta.toml` 的 `theme` 里写目录名。要在工程里改外观：把 `templates/<slug>/` 拷到 `themes/<slug>/`（`/markdown-slides theme`）。要再加一种：用 `/frontend-slides` 做视觉挑选，然后在稿 `themes/<slug>/` 或 skill `templates/<slug>/` 放入 `deck.css`、`deck.js`、`pptx/`。把 `theme` 指过去。不要把 frontend-slides 的 HTML 丢进稿仓库。

构建好的 HTML 会内联 webfont。`make slides` 可能把 Google Fonts 下载一次到 `skills/markdown-slides/.cache/`（需要联网）。打开 HTML 不再访问外网。`make fonts` 可预热缓存。没有缓存、也没有网络时，构建仍会成功，稿用系统字体，而不会卡在 CDN。

Skill 目录里的 `examples/slides/` 是引擎自测用的英文页。在 skill 目录执行 `make html` 会构建那一套。

## 本仓库的演示稿

根目录的 [`slides/`](slides/) 就是 skill 的示例演示稿：用 markdown-slides 在本项目里生成，稿和 skill 同处一个 git 仓库。

| 文件 | 作用 |
|------|------|
| [`slides/`](slides/) | 页面源文件，`NNN-slug.md`，顺序按文件名 |
| [`config.ini`](config.ini) | `[serve]` 端口；文档根是 `build/` |
| [`Makefile`](Makefile) | 薄封装：`python3 build.py <target>` |
| [`build.py`](build.py) | 按 `meta.toml` 的 `type` 找到嵌套 skill，再带 `DECK_ROOT` 转发 |

在仓库根目录构建：

```bash
make slides
```

得到 `build/slides/markdown-publisher.html`（不入库）。`make ppt slides`、`make pdf slides`、`make serve` 同样可用。改文案只改 Markdown，提交后再构建，不要手改 HTML。
