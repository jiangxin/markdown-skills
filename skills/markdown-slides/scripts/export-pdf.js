#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const { createRequire } = require("module");
const fs = require("fs");
const http = require("http");
const path = require("path");

const { SKILL_ROOT, loadOutputs, deckEnv } = require("./deck-paths");
const CACHE = path.join(SKILL_ROOT, ".cache", "pdf-export");
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "application/javascript",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

function parseArgs(argv, outputs) {
  let compact = false;
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--compact") {
      compact = true;
      continue;
    }
    if (arg === "--print-output") continue;
    if (arg === "--deck-root") {
      i += 1;
      continue;
    }
    if (arg.startsWith("--deck-root=")) continue;
    rest.push(arg);
  }
  return {
    html: rest[0] ? path.resolve(rest[0]) : outputs.html,
    out: rest[1] ? path.resolve(rest[1]) : outputs.pdf,
    width: compact ? 1280 : 1920,
    height: compact ? 720 : 1080,
  };
}

function fail(message) {
  process.stderr.write(`${message}\n`);
  process.exit(1);
}

function run(command, args, cwd, env) {
  const result = spawnSync(command, args, { cwd, env, encoding: "utf8", stdio: "inherit" });
  if (result.status !== 0) {
    fail(`failed: ${command} ${args.join(" ")}`);
  }
}

function ensureHtml(htmlPath, outputs) {
  if (fs.existsSync(htmlPath)) return;
  if (path.resolve(htmlPath) !== path.resolve(outputs.html)) fail(`HTML not found: ${htmlPath}`);
  process.stdout.write(`${path.basename(htmlPath)} missing; building HTML\n`);
  run(
    "python3",
    [path.join(SKILL_ROOT, "scripts", "build-slides.py")],
    SKILL_ROOT,
    deckEnv(outputs)
  );
  if (!fs.existsSync(htmlPath)) fail(`HTML not found: ${htmlPath}`);
}

function cacheRequire() {
  fs.mkdirSync(CACHE, { recursive: true });
  const pkg = path.join(CACHE, "package.json");
  if (!fs.existsSync(pkg)) {
    fs.writeFileSync(pkg, JSON.stringify({ name: "pdf-export-cache", private: true }));
  }
  return { pkg, require: createRequire(pkg) };
}

function ensureNpm(name) {
  if (fs.existsSync(path.join(CACHE, "node_modules", name))) return;
  process.stdout.write(`installing ${name} (first run, may take a minute)...\n`);
  run("npm", ["install", name], CACHE);
}

function loadPlaywright() {
  const local = path.join(SKILL_ROOT, "node_modules", "playwright");
  if (fs.existsSync(local)) return require(local);
  cacheRequire();
  ensureNpm("playwright");
  const playwright = cacheRequire().require("playwright");
  const browserPath = playwright.chromium.executablePath();
  if (!browserPath || !fs.existsSync(browserPath)) {
    process.stdout.write("installing Chromium for Playwright...\n");
    run("npx", ["playwright", "install", "chromium"], CACHE);
  }
  return playwright;
}

function loadPdfLib() {
  cacheRequire();
  ensureNpm("pdf-lib");
  return cacheRequire().require("pdf-lib");
}

function startServer(root, indexName) {
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
    const rel = urlPath === "/" ? indexName : urlPath.replace(/^\/+/, "");
    const filePath = path.normalize(path.join(root, rel));
    const allowed = filePath === root || filePath.startsWith(root + path.sep);
    if (!allowed) {
      res.writeHead(403).end();
      return;
    }
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404).end("Not found");
        return;
      }
      res.writeHead(200, { "Content-Type": MIME[path.extname(filePath).toLowerCase()] || "application/octet-stream" });
      res.end(data);
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      resolve({ server, port: server.address().port });
    });
  });
}

/** Same stamp as the in-page cache-bust script (mtime + size). */
function htmlRevision(htmlPath) {
  const st = fs.statSync(htmlPath);
  return `${st.mtimeMs}-${st.size}`;
}

function exportCss(width, height) {
  return `
    @page { size: ${width}px ${height}px; margin: 0; }
    .progress-track, .edit-toggle, .edit-hotzone, .deck-controls {
      display: none !important;
    }
    .reveal, .slide.visible .reveal, .slide.active .reveal {
      opacity: 1 !important;
      transform: none !important;
      transition: none !important;
      animation: none !important;
    }
    html, body {
      width: ${width}px !important;
      height: ${height}px !important;
      overflow: hidden !important;
      background: #fff !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .deck-viewport {
      position: fixed !important;
      inset: 0 !important;
      overflow: hidden !important;
      background: #fff !important;
    }
    .deck-stage {
      position: absolute !important;
      left: 0 !important;
      top: 0 !important;
      width: 1920px !important;
      height: 1080px !important;
      overflow: hidden !important;
      transform-origin: 0 0 !important;
    }
    .slide:not(.active) {
      display: none !important;
    }
    .slide.active {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      position: absolute !important;
      inset: 0 !important;
      break-after: auto !important;
      page-break-after: auto !important;
    }
  `;
}

async function waitForAssets(page) {
  // Webfonts may hang if the network is blocked; don't stall the whole export.
  await page
    .evaluate(async () => {
      await Promise.race([
        document.fonts.ready,
        new Promise((r) => setTimeout(r, 3000)),
      ]);
      const imgs = [
        ...document.querySelectorAll(".slide.active img, .slide.visible img"),
      ];
      await Promise.all(
        imgs.map((img) => {
          if (img.complete) return null;
          return new Promise((resolve) => {
            img.addEventListener("load", resolve, { once: true });
            img.addEventListener("error", resolve, { once: true });
          });
        })
      );
    })
    .catch(() => {});
}

async function showSlideByHash(page, n) {
  await page.evaluate((num) => {
    const hash = "#" + num;
    if (location.hash === hash) {
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    } else {
      location.hash = String(num);
    }
  }, n);
  await page.waitForFunction((num) => {
    const slide = document.querySelectorAll(".slide")[num - 1];
    return !!(slide && slide.classList.contains("active"));
  }, n);
  await waitForAssets(page);
}

async function printSlide(page, width, height) {
  const buf = await page.pdf({
    width: `${width}px`,
    height: `${height}px`,
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
    pageRanges: "1",
  });
  return buf;
}

async function mergePdfPages(pages) {
  const { PDFDocument } = loadPdfLib();
  const merged = await PDFDocument.create();
  for (const buf of pages) {
    const doc = await PDFDocument.load(buf);
    const copied = await merged.copyPages(doc, doc.getPageIndices());
    copied.forEach((p) => merged.addPage(p));
  }
  return Buffer.from(await merged.save());
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
    process.stdout.write(`${outputs.pdf}\n`);
    return;
  }
  const opts = parseArgs(argv, outputs);
  ensureHtml(opts.html, outputs);
  const playwright = loadPlaywright();
  const { server, port } = await startServer(path.dirname(opts.html), path.basename(opts.html));

  try {
    const browser = await playwright.chromium.launch();
    const page = await browser.newPage({
      viewport: { width: opts.width, height: opts.height },
      deviceScaleFactor: 1,
    });
    // Head <link> to fonts.googleapis.com blocks HTML parsing until the CSS
    // returns; offline / slow CDN makes page.goto(waitUntil:'load') hang.
    await page.route(/fonts\.googleapis\.com|fonts\.gstatic\.com/, (route) =>
      route.fulfill({ status: 200, contentType: "text/css", body: "/* pdf-export: skip webfonts */" })
    );
    const fileName = path.basename(opts.html);
    const rev = encodeURIComponent(htmlRevision(opts.html));
    // Include ?_v= so the in-page cache-bust script does not location.replace mid-load.
    const baseUrl = `http://127.0.0.1:${port}/${encodeURIComponent(fileName)}?_v=${rev}`;
    await page.goto(`${baseUrl}#1`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.addStyleTag({ content: exportCss(opts.width, opts.height) });
    await page.emulateMedia({ media: "screen" });
    await waitForAssets(page);

    const slideCount = await page.evaluate(() => document.querySelectorAll(".slide").length);
    if (slideCount === 0) fail("no .slide elements found in HTML");

    const pages = [];
    for (let n = 1; n <= slideCount; n++) {
      await showSlideByHash(page, n);
      pages.push(await printSlide(page, opts.width, opts.height));
      process.stdout.write(`  printed #${n}/${slideCount}\n`);
    }
    await browser.close();

    fs.writeFileSync(opts.out, await mergePdfPages(pages));
    const size = fs.statSync(opts.out).size;
    const mb = (size / (1024 * 1024)).toFixed(1);
    process.stdout.write(
      `wrote ${shown(outputs.root, opts.out)} (${slideCount} slides, ${opts.width}×${opts.height}, ${mb} MB, selectable text)\n`
    );
  } finally {
    server.close();
  }
}

main().catch((err) => {
  process.stderr.write(`${err.stack || err}\n`);
  process.exit(1);
});
