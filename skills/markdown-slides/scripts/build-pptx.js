#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const { SKILL_ROOT, SCRIPTS, loadOutputs, deckEnv } = require("./deck-paths");

function loadPptxgen() {
  const local = path.join(SKILL_ROOT, "node_modules", "pptxgenjs");
  try {
    return require(local);
  } catch {
    try {
      return require("pptxgenjs");
    } catch {
      const install = spawnSync("npm", ["install"], {
        cwd: SKILL_ROOT,
        encoding: "utf8",
        stdio: "inherit",
      });
      if (install.status !== 0) {
        process.stderr.write("failed to install pptxgenjs\n");
        process.exit(1);
      }
      return require(local);
    }
  }
}

function loadDeck(outputs) {
  const result = spawnSync("python3", [path.join(SCRIPTS, "slide_model.py")], {
    encoding: "utf8",
    env: deckEnv(outputs),
  });
  if (result.status !== 0) {
    process.stderr.write(result.stderr || "slide_model.py failed\n");
    process.exit(1);
  }
  return JSON.parse(result.stdout);
}

function explicitOut(argv) {
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--print-output") continue;
    if (arg === "--deck-root") {
      i += 1;
      continue;
    }
    if (arg.startsWith("--deck-root=")) continue;
    rest.push(arg);
  }
  return rest[0] ? path.resolve(rest[0]) : null;
}

function shown(root, file) {
  const rel = path.relative(root, file);
  if (!rel || rel.startsWith("..") || path.isAbsolute(rel)) return file;
  return rel;
}

async function main() {
  const argv = process.argv.slice(2);
  const outputs = loadOutputs(argv);
  if (argv.includes("--print-output")) {
    process.stdout.write(`${outputs.pptx}\n`);
    return;
  }
  const out = explicitOut(argv) || outputs.pptx;
  const themeDir = outputs.themeDir;
  if (!themeDir) {
    process.stderr.write("config.py json is missing themeDir\n");
    process.exit(1);
  }
  const theme = JSON.parse(
    fs.readFileSync(path.join(themeDir, "pptx", "theme.json"), "utf8")
  );
  const layouts = require(path.join(themeDir, "pptx", "layouts.js"));
  const PptxGenJS = loadPptxgen();
  const deck = loadDeck(outputs);
  const pres = new PptxGenJS();
  pres.defineLayout({ name: "WIDE_16x9", width: theme.width, height: theme.height });
  pres.layout = "WIDE_16x9";
  pres.title = deck.title;
  pres.subject = deck.version || "";
  // Do not set pres.revision: PowerPoint requires a whole number.

  for (const page of deck.slides) {
    if (Array.isArray(page.cards)) {
      page.cards = page.cards.filter((card) => {
        const token = String(card.html_only || "").trim().toLowerCase();
        return !["on", "true", "1", "yes"].includes(token);
      });
    }
    const slide = pres.addSlide();
    slide.background = { color: theme.colors.bg };
    const render = layouts[page.layout];
    if (!render) {
      process.stderr.write(`unknown layout: ${page.layout} (${page.file})\n`);
      process.exit(1);
    }
    render(slide, pres, theme, page);
  }

  await fs.promises.mkdir(path.dirname(out), { recursive: true });
  await pres.writeFile({ fileName: out });
  const ver = deck.version ? `, ${deck.version}` : "";
  process.stdout.write(`wrote ${shown(outputs.root, out)} (${deck.total} slides${ver})\n`);
}

main().catch((err) => {
  process.stderr.write(`${err.stack || err}\n`);
  process.exit(1);
});
