"use strict";

function pxToIn(theme, px) {
  return (Number(px) * theme.width) / theme.stagePx[0];
}

function parsePx(value) {
  const m = String(value || "").match(/^(\d+(?:\.\d+)?)\s*(px)?$/i);
  return m ? Number(m[1]) : null;
}

function parsePercent(value) {
  const m = String(value || "").trim().match(/^(\d+(?:\.\d+)?)\s*%$/);
  return m ? Number(m[1]) : null;
}

function pxToPt(theme, px) {
  return (Number(px) * theme.height * 72) / theme.stagePx[1];
}

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function pad(theme) {
  const p = theme.padPx;
  return {
    top: pxToIn(theme, p.top),
    right: pxToIn(theme, p.right),
    bottom: pxToIn(theme, p.bottom),
    left: pxToIn(theme, p.left),
  };
}

function contentBox(theme) {
  const p = pad(theme);
  const footer = pxToIn(theme, theme.footerHPx);
  return {
    x: p.left,
    y: p.top,
    w: theme.width - p.left - p.right,
    h: theme.height - p.top - p.bottom - footer,
    footerH: footer,
  };
}

function parseCssDecl(style) {
  const out = {};
  if (!style) return out;
  for (const part of String(style).split(";")) {
    const idx = part.indexOf(":");
    if (idx < 0) continue;
    out[part.slice(0, idx).trim()] = part.slice(idx + 1).trim();
  }
  return out;
}

function cssPx(value) {
  if (!value || value === "auto") return null;
  const m = String(value).match(/^(-?[\d.]+)px$/);
  return m ? Number(m[1]) : null;
}

function splitLines(text) {
  return String(text || "")
    .replace(/<br\s*\/?>/gi, "\n")
    .split("\n");
}

function estimateLines(text, fontPt, widthIn) {
  const clean = String(text || "")
    .replace(/\[([^\]]+?)\]\([^)]+?\)/g, "$1")
    .replace(/==/g, "")
    .replace(/`/g, "")
    .replace(/<br\s*\/?>/gi, "\n");
  const lines = clean.split("\n");
  const charsPerLine = Math.max(8, Math.floor((widthIn * 72) / fontPt));
  let n = 0;
  for (const line of lines) {
    const chars = [...line].length || 1;
    n += Math.max(1, Math.ceil(chars / charsPerLine));
  }
  return Math.max(1, n);
}

function richRuns(theme, text, base) {
  const src = String(text || "");
  const re = /==(.+?)==|`([^`]+)`|<br\s*\/?>|\[([^\]]+?)\]\(([^)]+?)\)/g;
  const runs = [];
  let last = 0;
  let match;
  const push = (value, extra) => {
    if (value == null || value === "") return;
    runs.push({
      text: value,
      options: Object.assign(
        {
          fontFace: base.fontFace,
          fontSize: base.fontSize,
          color: base.color,
          bold: !!base.bold,
          charSpacing: base.charSpacing,
        },
        extra || {}
      ),
    });
  };
  while ((match = re.exec(src))) {
    push(src.slice(last, match.index));
    if (match[0].startsWith("==")) {
      push(match[1], {
        bold: true,
        ...(base.onAccentBg ? {} : { color: theme.colors.accent }),
      });
    } else if (match[0].startsWith("`")) {
      push(match[2], { fontFace: theme.fonts.mono });
    } else if (match[0].startsWith("[")) {
      const url = String(match[4] || "").trim();
      const href = /^https?:\/\//i.test(url)
        ? url
        : url.startsWith("//")
          ? "https:" + url
          : "https://" + url;
      push(match[3], {
        hyperlink: { url: href, tooltip: match[3] },
        color: base.onAccentBg ? base.color : theme.colors.accent,
        underline: true,
      });
    } else if (runs.length) {
      runs[runs.length - 1].options.breakLine = true;
    } else {
      push(" ", { breakLine: true });
    }
    last = match.index + match[0].length;
  }
  push(src.slice(last));
  if (!runs.length) push(" ");
  return runs;
}

function addText(slide, theme, text, box, base) {
  const opts = {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    margin: 0,
    valign: base.valign || "top",
    align: base.align || "left",
  };
  slide.addText(richRuns(theme, text, base), opts);
}

function cardPalette(theme, tone) {
  if (tone === "filled") {
    return { bg: theme.colors.ink, fg: "FFFFFF", num: "FFFFFF", border: theme.colors.ink };
  }
  if (tone === "red") {
    return { bg: theme.colors.accent, fg: "FFFFFF", num: "FFFFFF", border: theme.colors.accent };
  }
  return {
    bg: theme.colors.bg,
    fg: theme.colors.ink,
    num: theme.colors.accent,
    border: theme.colors.ink,
  };
}

function addRedBar(slide, pres, theme) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0,
    y: 0,
    w: pxToIn(theme, theme.barPx),
    h: theme.height,
    fill: { color: theme.colors.accent },
    line: { color: theme.colors.accent, pt: 0 },
  });
}

function addFooter(slide, pres, theme, page) {
  const p = pad(theme);
  const meta = page.meta || {};
  const isFootNote = page.note_slot === "foot" && page.note;
  // Match band :::note: note_size wins, else page text_size, else default card body.
  const sizeKey = String(meta.note_size || meta.text_size || "")
    .trim()
    .toLowerCase();
  const scale = (theme.textScalePx && theme.textScalePx[sizeKey]) || null;
  const footPx = isFootNote
    ? (scale && scale.body) || theme.sizesPx.cardBody
    : theme.sizesPx.foot;
  const textH = isFootNote ? Math.max(0.36, (footPx / 1920) * theme.height + 0.08) : 0.32;
  const y = theme.height - p.bottom - pxToIn(theme, isFootNote ? 32 : 28);
  slide.addShape(pres.shapes.RECTANGLE, {
    x: p.left,
    y: y,
    w: theme.width - p.left - p.right,
    h: 0.015,
    fill: { color: theme.colors.ink },
    line: { color: theme.colors.ink, pt: 0 },
  });
  const stamp =
    page.stamp ||
    `${String(page.index).padStart(2, "0")} / ${String(page.total).padStart(2, "0")}`;
  const stampW = 2.8;
  const leftText = isFootNote ? page.note : meta.footer || "";
  addText(
    slide,
    theme,
    leftText,
    { x: p.left, y: y + 0.06, w: theme.width - p.left - p.right - stampW - 0.12, h: textH },
    {
      fontFace: theme.fonts.body,
      fontSize: pxToPt(theme, footPx),
      color: isFootNote ? theme.colors.ink : theme.colors.muted,
      valign: "middle",
    }
  );
  addText(
    slide,
    theme,
    stamp,
    { x: theme.width - p.right - stampW, y: y + 0.06, w: stampW, h: textH },
    {
      fontFace: theme.fonts.mono,
      fontSize: pxToPt(theme, theme.sizesPx.foot),
      color: theme.colors.muted,
      align: "right",
      valign: "middle",
    }
  );
}

function resolveOverlineStyle(text, style) {
  const raw = String(style == null ? "auto" : style).trim().toLowerCase() || "auto";
  if (raw === "cn") return "cjk";
  if (raw === "cjk" || raw === "en") return raw;
  const ascii = [...String(text || "")].every((ch) => ch.codePointAt(0) < 128);
  return ascii ? "en" : "cjk";
}

function addHeader(slide, theme, page, sizes) {
  const box = contentBox(theme);
  const meta = page.meta || {};
  let y = box.y;
  const overline = meta.overline || "";
  const overlineStyle = resolveOverlineStyle(overline, meta.overline_style);
  if (overline) {
    const isCjk = overlineStyle === "cjk";
    addText(
      slide,
      theme,
      overline,
      { x: box.x, y, w: box.w, h: 0.28 },
      {
        fontFace: isCjk ? theme.fonts.body : theme.fonts.display,
        fontSize: pxToPt(theme, theme.sizesPx.overline),
        color: theme.colors.accent,
        bold: true,
        charSpacing: isCjk ? undefined : 2,
      }
    );
    y += 0.3;
  }
  const title = meta.title || "";
  const titlePt = sizes && sizes.titlePt ? sizes.titlePt : pxToPt(theme, theme.sizesPx.h2);
  const titleLines = estimateLines(title, titlePt, box.w);
  const titleH = Math.max(0.42, titleLines * (titlePt / 72) * 1.2);
  addText(
    slide,
    theme,
    title,
    { x: box.x, y, w: box.w, h: titleH },
    {
      fontFace: theme.fonts.body,
      fontSize: titlePt,
      color: theme.colors.ink,
      bold: true,
    }
  );
  y += titleH + 0.08;
  if (meta.summary) {
    const summaryPt = sizes && sizes.summaryPt ? sizes.summaryPt : pxToPt(theme, theme.sizesPx.summary);
    const summaryLines = estimateLines(meta.summary, summaryPt, box.w);
    const summaryH = Math.max(0.36, summaryLines * (summaryPt / 72) * 1.35);
    addText(
      slide,
      theme,
      meta.summary,
      { x: box.x, y, w: box.w * 0.92, h: summaryH },
      {
        fontFace: theme.fonts.body,
        fontSize: summaryPt,
        color: theme.colors.ink,
      }
    );
    y += summaryH + 0.12;
  }
  return { x: box.x, y, w: box.w, h: box.y + box.h - y };
}

function equalHeightImageBoxes(items, area, gapIn) {
  const ratios = items.map((card) => {
    const w = Number(card.image && card.image.width) || 1;
    const h = Number(card.image && card.image.height) || 1;
    return w / Math.max(1, h);
  });
  const sumR = ratios.reduce((a, b) => a + b, 0) || 1;
  const avail = Math.max(0.5, area.w - gapIn * Math.max(0, items.length - 1));
  const rowH = Math.min(area.h, avail / sumR);
  const totalW = rowH * sumR + gapIn * Math.max(0, items.length - 1);
  let x = area.x + (area.w - totalW) / 2;
  return items.map((_, i) => {
    const w = rowH * ratios[i];
    const box = { x, y: area.y, w, h: rowH };
    x += w + gapIn;
    return box;
  });
}

function gridBoxes(count, cols, area, gapIn) {
  const rows = Math.max(1, Math.ceil(count / cols));
  const cw = (area.w - gapIn * (cols - 1)) / cols;
  const ch = (area.h - gapIn * (rows - 1)) / rows;
  const boxes = [];
  for (let i = 0; i < count; i++) {
    const r = Math.floor(i / cols);
    const c = i % cols;
    boxes.push({
      x: area.x + c * (cw + gapIn),
      y: area.y + r * (ch + gapIn),
      w: cw,
      h: ch,
    });
  }
  return boxes;
}

// 列表要不要方块项目符：marker 写了就听它，没写沿用旧推断（有 title、无 num）。
// 与 scripts/build-slides.py 的 wants_marker() 保持一致。
function wantsMarker(card) {
  const token = String(card.marker || "").trim().toLowerCase();
  if (["on", "true", "1", "yes"].includes(token)) return true;
  if (["off", "false", "0", "no"].includes(token)) return false;
  return Boolean(card.title) && !card.num;
}

/** Plain-text preview of an included Markdown doc for PPTX (no scroll). */
function markdownPreview(src) {
  const lines = String(src || "")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) =>
      line
        .replace(/\*\*/g, "")
        .replace(/`/g, "")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .replace(/^#+\s+/, "")
        .replace(/^>\s?/, "")
        .replace(/^\|/, "")
        .replace(/\|/g, " · ")
        .trim()
    )
    .filter((line) => line && !/^[-*:|\s]+$/.test(line));
  const kept = lines.slice(0, 26);
  kept.push("The full list is in the HTML deck (scroll to read it).");
  return kept.join("\n");
}

function drawCard(slide, pres, theme, card, box) {
  const pal = cardPalette(theme, card.tone);
  slide.addShape(pres.shapes.RECTANGLE, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fill: { color: pal.bg },
    line: { color: pal.border, pt: 1.5 },
  });
  const inset = pxToIn(theme, theme.cardPadPx);
  let y = box.y + inset * 0.85;
  const x = box.x + inset;
  const w = box.w - inset * 2;
  const bottom = box.y + box.h - inset * 0.7;

  if (card.image && card.image.abs) {
    const hasCaption = Boolean(card.num || card.title);
    if (card.num) {
      addText(
        slide,
        theme,
        card.num,
        { x, y, w, h: 0.28 },
        {
          fontFace: theme.fonts.display,
          fontSize: pxToPt(theme, card.numPx || theme.sizesPx.cardNum),
          color: pal.num,
          bold: true,
        }
      );
      y += 0.3;
    }
    if (card.title) {
      const tPt = pxToPt(theme, card.titlePx || theme.sizesPx.cardTitle);
      const tH = Math.max(0.32, estimateLines(card.title, tPt, w) * (tPt / 72) * 1.25);
      addText(
        slide,
        theme,
        card.title,
        { x, y, w, h: tH },
        {
          fontFace: theme.fonts.body,
          fontSize: tPt,
          color: pal.fg,
          bold: true,
        }
      );
      y += tH + 0.06;
    }
    const imgW = Number(card.image.width) || 1;
    const imgH = Number(card.image.height) || 1;
    const innerPad = pxToIn(theme, 8);
    const inner = {
      x: box.x + innerPad,
      y: hasCaption ? y : box.y + innerPad,
      w: box.w - innerPad * 2,
      h: Math.max(0.1, box.y + box.h - innerPad - (hasCaption ? y : box.y + innerPad)),
    };
    const maxHPx = parsePx(card.image_max_height);
    const maxWPx = parsePx(card.image_max_width);
    const maxH = maxHPx ? Math.min(inner.h, pxToIn(theme, maxHPx)) : inner.h;
    const maxW = maxWPx ? Math.min(inner.w, pxToIn(theme, maxWPx)) : inner.w;
    const fit = String(card.image_fit || "contain").trim().toLowerCase();
    let drawW;
    let drawH;
    if (fit === "fill") {
      drawW = maxW;
      drawH = maxH;
    } else if (fit === "cover") {
      const scale = Math.max(maxW / imgW, maxH / imgH);
      drawW = imgW * scale;
      drawH = imgH * scale;
    } else if (fit === "width") {
      drawW = maxW;
      const heightPct = parsePercent(card.image_height);
      if (heightPct) {
        drawH = maxH * (heightPct / 100);
      } else {
        drawH = imgH * (maxW / imgW);
        if (drawH > maxH) {
          const shrink = maxH / drawH;
          drawW *= shrink;
          drawH = maxH;
        }
      }
    } else if (fit === "height") {
      drawH = maxH;
      drawW = imgW * (maxH / imgH);
      if (drawW > maxW) {
        const shrink = maxW / drawW;
        drawH *= shrink;
        drawW = maxW;
      }
    } else {
      const scale = Math.min(maxW / imgW, maxH / imgH);
      drawW = imgW * scale;
      drawH = imgH * scale;
    }
    slide.addImage({
      path: card.image.abs,
      x: inner.x + (inner.w - drawW) / 2,
      y: inner.y + (inner.h - drawH) / 2,
      w: drawW,
      h: drawH,
    });
    return;
  }
  const inline_head = ["on", "true", "1", "yes"].includes(String(card.inline_head || "").trim().toLowerCase());
  if (inline_head && card.num && card.title) {
    const numPt = pxToPt(theme, card.numPx || theme.sizesPx.cardNum);
    const titlePt = pxToPt(theme, card.titlePx || theme.sizesPx.cardTitle);
    const tH = Math.max(0.32, estimateLines(card.title, titlePt, w) * (titlePt / 72) * 1.25);
    slide.addText(
      [
        { text: card.num + " ", options: { fontFace: theme.fonts.display, fontSize: numPt, color: pal.num, bold: true } },
        { text: card.title, options: { fontFace: theme.fonts.body, fontSize: titlePt, color: pal.fg, bold: true } },
      ],
      { x, y, w, h: tH, margin: 0, valign: "top" }
    );
    y += tH + 0.06;
  } else {
    if (card.num) {
      addText(
        slide,
        theme,
        card.num,
        { x, y, w, h: 0.28 },
        {
          fontFace: theme.fonts.display,
          fontSize: pxToPt(theme, card.numPx || theme.sizesPx.cardNum),
          color: pal.num,
          bold: true,
        }
      );
      y += 0.3;
    }
    if (card.title) {
      const tPt = pxToPt(theme, card.titlePx || theme.sizesPx.cardTitle);
      const tH = Math.max(0.32, estimateLines(card.title, tPt, w) * (tPt / 72) * 1.25);
      addText(
        slide,
        theme,
        card.title,
        { x, y, w, h: tH },
        {
          fontFace: theme.fonts.body,
          fontSize: tPt,
          color: pal.fg,
          bold: true,
        }
      );
      y += tH + 0.06;
    }
  }
  const body = card.markdown
    ? markdownPreview(card.markdown)
    : (card.paragraphs || []).join("\n");
  const bullets = card.bullets || [];
  const remain = Math.max(0.2, bottom - y);
  const bodyPt = pxToPt(theme, card.bodyPx || theme.sizesPx.cardBody);
  const onAccentBg = pal.bg === theme.colors.accent;
  if (body) {
    const fitted = Math.max(0.22, (bodyPt * 1.4 * estimateLines(body, bodyPt, w)) / 72);
    const bodyH = bullets.length ? Math.min(fitted, Math.max(0.22, remain - 0.4)) : remain;
    addText(
      slide,
      theme,
      body,
      { x, y, w, h: bodyH },
      {
        fontFace: theme.fonts.body,
        fontSize: bodyPt,
        color: pal.fg,
        onAccentBg,
      }
    );
    y += bodyH + 0.04;
  }
  if (bullets.length) {
    const marker = wantsMarker(card);
    const items = [];
    bullets.forEach((item, i) => {
      const depth = Math.max(0, Number(item.depth) || 0);
      const raw = String(item.text || "");
      const wrapped = /^\*\*(.+)\*\*$/.exec(raw);
      const runs = richRuns(theme, wrapped ? wrapped[1] : raw, {
        fontFace: theme.fonts.body,
        fontSize: bodyPt,
        color: pal.fg,
        bold: Boolean(wrapped),
        onAccentBg,
      });
      const first = runs[0].options;
      first.bullet = marker ? { characterCode: depth ? "25A1" : "25A0" } : false;
      first.indentLevel = depth;
      first.paraSpaceAfter = 4;
      if (i !== bullets.length - 1) {
        runs[runs.length - 1].options.breakLine = true;
      }
      items.push(...runs);
    });
    slide.addText(items, {
      x,
      y,
      w,
      h: Math.max(0.2, bottom - y),
      margin: 0,
      valign: "top",
    });
  }
}

function splitColumns(theme, area) {
  const gap = pxToIn(theme, 24);
  const leftW = (area.w - gap) * (theme.grid23[0] / (theme.grid23[0] + theme.grid23[1]));
  const rightW = area.w - gap - leftW;
  return {
    left: { x: area.x, y: area.y, w: leftW, h: area.h },
    right: { x: area.x + leftW + gap, y: area.y, w: rightW, h: area.h },
    gap,
  };
}

// 按权重切出任意列数；权重可以是页面 widths 里的百分比数字。
function columnBoxes(theme, area, weights) {
  const gap = pxToIn(theme, 24);
  const list = (weights || []).map((w) => Math.max(0.1, Number(w) || 1));
  if (!list.length) return [];
  const total = list.reduce((a, b) => a + b, 0);
  const available = area.w - gap * (list.length - 1);
  const boxes = [];
  let x = area.x;
  for (const weight of list) {
    const w = available * (weight / total);
    boxes.push({ x, y: area.y, w, h: area.h });
    x += w + gap;
  }
  return boxes;
}

function stackBoxes(count, area, gapIn) {
  if (count <= 0) return [];
  const h = (area.h - gapIn * (count - 1)) / count;
  const boxes = [];
  for (let i = 0; i < count; i++) {
    boxes.push({ x: area.x, y: area.y + i * (h + gapIn), w: area.w, h });
  }
  return boxes;
}

function weightedStackBoxes(cards, area, gapIn) {
  const count = cards.length;
  if (count <= 0) return [];
  const weights = cards.map((c) => Math.max(0.1, Number(c.weight) || 1));
  const total = weights.reduce((a, b) => a + b, 0);
  const available = area.h - gapIn * (count - 1);
  const boxes = [];
  let y = area.y;
  for (let i = 0; i < count; i++) {
    const h = available * (weights[i] / total);
    boxes.push({ x: area.x, y, w: area.w, h });
    y += h + gapIn;
  }
  return boxes;
}

module.exports = {
  pxToIn,
  pxToPt,
  clone,
  pad,
  contentBox,
  parseCssDecl,
  cssPx,
  splitLines,
  estimateLines,
  richRuns,
  addText,
  cardPalette,
  addRedBar,
  addFooter,
  addHeader,
  resolveOverlineStyle,
  gridBoxes,
  equalHeightImageBoxes,
  drawCard,
  splitColumns,
  columnBoxes,
  stackBoxes,
  weightedStackBoxes,
};
