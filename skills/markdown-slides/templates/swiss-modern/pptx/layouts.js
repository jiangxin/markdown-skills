"use strict";

const chrome = require("./chrome");

function paintChrome(slide, pres, theme, page, headerSizes) {
  chrome.addRedBar(slide, pres, theme);
  chrome.addFooter(slide, pres, theme, page);
  return chrome.addHeader(slide, theme, page, headerSizes);
}

// 字号档位 s / m / l / xl / xxl；未识别的值返回 null，走 theme.sizesPx 默认字号。
function textStep(theme, size) {
  const key = String(size || "").trim().toLowerCase();
  return (theme.textScalePx || {})[key] || null;
}

// 整页 text_size 打底，单张卡片 size 覆盖；图片卡不受影响。
function scaleCards(theme, page, items) {
  const pageSize = (page.meta && page.meta.text_size) || "";
  return items.map((card) => {
    const step = card.image ? null : textStep(theme, card.size || pageSize);
    return step ? { ...card, numPx: step.num, titlePx: step.title, bodyPx: step.body } : card;
  });
}

function title(slide, pres, theme, page) {
  chrome.addRedBar(slide, pres, theme);
  chrome.addFooter(slide, pres, theme, page);
  const meta = page.meta || {};
  const p = chrome.pad(theme);
  chrome.addText(
    slide,
    theme,
    meta.meta_left || "",
    { x: p.left, y: p.top, w: 6.5, h: 0.36 },
    {
      fontFace: theme.fonts.body,
      fontSize: chrome.pxToPt(theme, theme.sizesPx.coverMeta),
      color: theme.colors.muted,
    }
  );
  chrome.addText(
    slide,
    theme,
    meta.meta_right || "",
    { x: theme.width - p.right - 2.2, y: p.top, w: 2.2, h: 0.36 },
    {
      fontFace: theme.fonts.display,
      fontSize: chrome.pxToPt(theme, theme.sizesPx.coverMeta),
      color: theme.colors.muted,
      align: "right",
    }
  );
  let titleY = chrome.pxToIn(theme, 104 + 48);
  if (meta.eyebrow) {
    chrome.addText(
      slide,
      theme,
      meta.eyebrow,
      { x: p.left, y: chrome.pxToIn(theme, 88 + 48), w: 8, h: 0.4 },
      {
        fontFace: theme.fonts.display,
        fontSize: 13,
        color: theme.colors.accent,
        bold: true,
      }
    );
    titleY = chrome.pxToIn(theme, 88 + 48 + 16 + 26);
  }
  const titlePt = meta.title_size
    ? chrome.pxToPt(theme, parseInt(meta.title_size, 10))
    : chrome.pxToPt(theme, theme.sizesPx.coverTitle);
  const titleLines = chrome.splitLines(meta.title);
  const titleH = Math.max(1.4, titleLines.length * (titlePt / 72) * 1.1);
  chrome.addText(
    slide,
    theme,
    meta.title || "",
    { x: p.left, y: titleY, w: 8.6, h: titleH },
    {
      fontFace: theme.fonts.body,
      fontSize: titlePt,
      color: theme.colors.ink,
      bold: true,
    }
  );
  chrome.addText(
    slide,
    theme,
    meta.subtitle || "",
    { x: p.left, y: titleY + titleH + 0.22, w: 7.8, h: 1.35 },
    {
      fontFace: theme.fonts.body,
      fontSize: chrome.pxToPt(theme, theme.sizesPx.coverSub),
      color: theme.colors.ink,
    }
  );

  const css = chrome.parseCssDecl(meta.badge_style);
  const size = chrome.pxToIn(theme, 340);
  let badgeH = size;
  let badgeY = chrome.pxToIn(theme, 268);
  const heightPx = chrome.cssPx(css.height);
  const bottomPx = chrome.cssPx(css.bottom);
  const topPx = chrome.cssPx(css.top);
  if (heightPx) badgeH = chrome.pxToIn(theme, heightPx);
  if (bottomPx != null) badgeY = theme.height - chrome.pxToIn(theme, bottomPx) - badgeH;
  else if (topPx != null) badgeY = chrome.pxToIn(theme, topPx);
  const badgeX = theme.width - p.right - size;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: badgeX,
    y: badgeY,
    w: size,
    h: badgeH,
    fill: { color: theme.colors.accent },
    line: { color: theme.colors.accent, pt: 0 },
  });
  const longEn = (meta.badge_text || "").length > 6;
  const padIn = chrome.pxToIn(theme, 28);
  chrome.addText(
    slide,
    theme,
    meta.badge_label || "",
    { x: badgeX + padIn, y: badgeY + padIn, w: size - padIn * 2, h: longEn ? badgeH * 0.55 : 0.4 },
    {
      fontFace: theme.fonts.body,
      fontSize: longEn ? chrome.pxToPt(theme, theme.sizesPx.badgeLabel) : 11,
      color: "FFFFFF",
      bold: true,
      valign: longEn ? "top" : "top",
    }
  );
  chrome.addText(
    slide,
    theme,
    meta.badge_text || "",
    {
      x: badgeX + padIn,
      y: badgeY + (longEn ? badgeH * 0.55 : badgeH - 0.85),
      w: size - padIn * 2,
      h: longEn ? badgeH * 0.35 : 0.7,
    },
    {
      fontFace: theme.fonts.display,
      fontSize: longEn ? chrome.pxToPt(theme, theme.sizesPx.badgeEn) : 28,
      color: "FFFFFF",
      bold: true,
      valign: "bottom",
    }
  );
  if (meta.presenter || meta.presented_at) {
    const footLineY = theme.height - p.bottom - chrome.pxToIn(theme, 28);
    const barW = chrome.pxToIn(theme, 4);
    const labelW = chrome.pxToIn(theme, 88);
    const textX = p.left + chrome.pxToIn(theme, 18 + 4);
    const valueW = 5.4;
    let rowY = footLineY - 0.86;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: p.left,
      y: rowY - 0.02,
      w: barW,
      h: 0.74,
      fill: { color: theme.colors.accent },
      line: { color: theme.colors.accent, pt: 0 },
    });
    const labelOpts = {
      fontFace: theme.fonts.display,
      fontSize: 9,
      color: theme.colors.accent,
      bold: true,
    };
    if (meta.presenter) {
      chrome.addText(
        slide,
        theme,
        "SPEAKER",
        { x: textX, y: rowY, w: labelW, h: 0.22 },
        labelOpts
      );
      chrome.addText(
        slide,
        theme,
        meta.presenter,
        { x: textX + labelW, y: rowY - 0.03, w: valueW, h: 0.34 },
        {
          fontFace: theme.fonts.body,
          fontSize: chrome.pxToPt(theme, 28),
          color: theme.colors.ink,
          bold: true,
        }
      );
      rowY += 0.36;
    }
    if (meta.presented_at) {
      chrome.addText(
        slide,
        theme,
        "WHEN",
        { x: textX, y: rowY, w: labelW, h: 0.22 },
        labelOpts
      );
      chrome.addText(
        slide,
        theme,
        meta.presented_at,
        { x: textX + labelW, y: rowY, w: valueW, h: 0.28 },
        {
          fontFace: theme.fonts.mono,
          fontSize: chrome.pxToPt(theme, 20),
          color: theme.colors.muted,
        }
      );
    }
  }
}

function section(slide, pres, theme, page) {
  chrome.addRedBar(slide, pres, theme);
  chrome.addFooter(slide, pres, theme, page);
  const meta = page.meta || {};
  const p = chrome.pad(theme);
  chrome.addText(
    slide,
    theme,
    meta.number || "",
    { x: p.left, y: p.top + 0.15, w: 8, h: 1.7 },
    {
      fontFace: theme.fonts.display,
      fontSize: chrome.pxToPt(theme, theme.sizesPx.sectionNum),
      color: theme.colors.accent,
      bold: true,
    }
  );
  chrome.addText(
    slide,
    theme,
    meta.title || "",
    { x: p.left, y: p.top + 1.85, w: 10.2, h: 1.35 },
    {
      fontFace: theme.fonts.body,
      fontSize: chrome.pxToPt(theme, theme.sizesPx.sectionTitle),
      color: theme.colors.ink,
      bold: true,
    }
  );
  chrome.addText(
    slide,
    theme,
    meta.summary || "",
    { x: p.left, y: p.top + 3.3, w: 9.2, h: 1.6 },
    {
      fontFace: theme.fonts.body,
      fontSize: chrome.pxToPt(theme, theme.sizesPx.sectionLede),
      color: theme.colors.ink,
    }
  );
}

function cards(slide, pres, theme, page) {
  const area = paintChrome(slide, pres, theme, page);
  const meta = page.meta || {};
  const cols = Number((page.meta && page.meta.columns) || 2);
  const items = scaleCards(theme, page, page.cards || []);
  const gap = chrome.pxToIn(theme, theme.gapPx);
  let body = area;
  if (page.note && page.note_slot !== "foot") {
    const noteStep = textStep(theme, page.meta && page.meta.note_size);
    const notePx = (noteStep && noteStep.body) || theme.sizesPx.cardBody;
    const notePt = chrome.pxToPt(theme, notePx);
    const lines = chrome.estimateLines(page.note, notePt, area.w - chrome.pxToIn(theme, 48));
    const cap = Math.max(2.15, (notePx / 34) * 3.4);
    const noteH = Math.min(cap, Math.max(0.7, lines * (notePt / 72) * 1.45 + 0.32));
    body = { x: area.x, y: area.y, w: area.w, h: area.h - noteH - 0.12 };
    chrome.drawCard(
      slide,
      pres,
      theme,
      { tone: "default", paragraphs: [page.note], bullets: [], num: "", title: "", bodyPx: notePx },
      { x: area.x, y: area.y + body.h + 0.12, w: area.w, h: noteH }
    );
  }
  const images = items.filter((card) => card.image);
  const text = items.filter((card) => !card.image);
  const imagesInline = ["true", "1", "yes", "on"].includes(
    String((page.meta && page.meta.images_inline) || "").trim().toLowerCase()
  );
  // widths 只描述一行：列数与卡数相等才认，和 HTML 侧的 grid-template-columns 对齐。
  const widths = String(meta.widths || "")
    .split(",")
    .map((w) => parseFloat(w))
    .filter((w) => !Number.isNaN(w));
  const widthBoxes = (count, box) =>
    widths.length >= 2 && widths.length === count ? chrome.columnBoxes(theme, box, widths) : null;
  if (items.length && items.every((card) => card.image)) {
    const boxes = widthBoxes(items.length, body) || chrome.equalHeightImageBoxes(items, body, gap);
    boxes.forEach((box, i) => {
      chrome.drawCard(slide, pres, theme, items[i], box);
    });
    return;
  }
  if (!imagesInline && images.length && text.length) {
    const textH = Math.min(2.15, body.h * 0.38);
    const imgH = body.h - textH - gap;
    chrome.gridBoxes(text.length, cols, { x: body.x, y: body.y, w: body.w, h: textH }, gap).forEach((box, i) => {
      chrome.drawCard(slide, pres, theme, text[i], box);
    });
    const bandH = (imgH - gap * (images.length - 1)) / images.length;
    images.forEach((card, i) => {
      chrome.drawCard(slide, pres, theme, card, {
        x: body.x,
        y: body.y + textH + gap + i * (bandH + gap),
        w: body.w,
        h: bandH,
      });
    });
    return;
  }
  const boxes = widthBoxes(items.length, body) || chrome.gridBoxes(items.length, cols, body, gap);
  items.forEach((card, i) => chrome.drawCard(slide, pres, theme, card, boxes[i]));
}

function split(slide, pres, theme, page) {
  const area = paintChrome(slide, pres, theme, page);
  const items = scaleCards(theme, page, page.cards || []);
  const gap = chrome.pxToIn(theme, 20);
  const images = items.filter((c) => c.image);
  const text = items.filter((c) => !c.image);
  if (images.length) {
    const textH = Math.min(2.35, area.h * 0.4);
    const imgH = area.h - textH - gap;
    chrome.gridBoxes(text.length, 2, { x: area.x, y: area.y, w: area.w, h: textH }, gap).forEach((box, i) => {
      chrome.drawCard(slide, pres, theme, text[i], box);
    });
    const bandH = (imgH - gap * (images.length - 1)) / images.length;
    images.forEach((card, i) => {
      chrome.drawCard(slide, pres, theme, card, {
        x: area.x,
        y: area.y + textH + gap + i * (bandH + gap),
        w: area.w,
        h: bandH,
      });
    });
    return;
  }
  const boxes = chrome.gridBoxes(items.length, 2, area, gap);
  items.forEach((card, i) => chrome.drawCard(slide, pres, theme, card, boxes[i]));
}

function stackSplit(slide, pres, theme, page) {
  const area = paintChrome(slide, pres, theme, page);
  const items = scaleCards(theme, page, page.cards || []);
  const left = [];
  const mid = [];
  const right = [];
  items.forEach((card, i) => {
    const slot = card.slot || (i === 0 ? "left" : "right");
    if (slot === "left") left.push(card);
    else if (slot === "mid") mid.push(card);
    else right.push(card);
  });
  const gap = chrome.pxToIn(theme, 16);
  const meta = page.meta || {};
  const widths = String(meta.widths || "")
    .split(",")
    .map((w) => parseFloat(w))
    .filter((w) => !Number.isNaN(w));
  const used = [
    ["left", left],
    ["mid", mid],
    ["right", right],
  ].filter(([, cards]) => cards.length);
  const columns = [];
  if (widths.length >= 2 && widths.length === used.length) {
    const boxes = chrome.columnBoxes(theme, area, widths);
    used.forEach(([, cards], i) => columns.push([cards, boxes[i]]));
  } else if (mid.length) {
    const boxes = chrome.columnBoxes(theme, area, [1.05, 0.95, 1]);
    columns.push([left, boxes[0]], [mid, boxes[1]], [right, boxes[2]]);
  } else {
    const cols = chrome.splitColumns(theme, area);
    columns.push([left, cols.left], [right, cols.right]);
  }
  columns.forEach(([cards, box]) => {
    chrome.weightedStackBoxes(cards, box, gap).forEach((cardBox, i) => {
      chrome.drawCard(slide, pres, theme, cards[i], cardBox);
    });
  });
}

function tableColWidths(area, meta, colCount) {
  const widths = String(meta.widths || "")
    .split(",")
    .map((w) => w.trim())
    .filter(Boolean)
    .map((w) => Number(w.replace("%", "")));
  if (!widths.length) return Array(colCount).fill(area.w / colCount);
  const known = widths.reduce((a, b) => a + (Number.isFinite(b) ? b : 0), 0);
  const rest = Math.max(0, 100 - known);
  const missing = colCount - widths.length;
  const colW = [];
  for (let i = 0; i < colCount; i++) {
    const pct = i < widths.length ? widths[i] : rest / Math.max(1, missing);
    colW.push((area.w * pct) / 100);
  }
  return colW;
}

function tableCellLines(theme, text, fontPt, colW) {
  const innerW = Math.max(0.4, colW - chrome.pxToIn(theme, 32));
  return chrome.estimateLines(text, fontPt, innerW);
}

function tableRowH(fontPt, lines, padYPt) {
  return (fontPt * 1.4 * Math.max(1, lines) + padYPt * 2) / 72;
}

function table(slide, pres, theme, page) {
  const area = paintChrome(slide, pres, theme, page);
  const data = page.table || { headers: [], rows: [] };
  const meta = page.meta || {};
  const step = textStep(theme, meta.text_size) || {};
  const bodyPx = step.table || theme.sizesPx.table;
  const headPx = step.tableHead || theme.sizesPx.tableHead;
  const summaryH = meta.summary_after ? 0.7 : 0;
  const maxTableH = area.h - (summaryH ? summaryH + 0.12 : 0);
  const colCount = data.headers.length || 1;
  const colW = tableColWidths(area, meta, colCount);
  const headPt = chrome.pxToPt(theme, headPx);
  const bodyPt = chrome.pxToPt(theme, bodyPx);
  const padYPt = chrome.pxToPt(theme, 14);
  const padXPt = chrome.pxToPt(theme, 16);
  const headLines = data.headers.reduce(
    (n, text, i) => Math.max(n, tableCellLines(theme, text, headPt, colW[i])),
    1
  );
  const rowH = [
    tableRowH(headPt, headLines, padYPt),
    ...data.rows.map((row) => {
      const lines = row.reduce(
        (n, cell, i) => Math.max(n, tableCellLines(theme, cell.text, bodyPt, colW[i])),
        1
      );
      return tableRowH(bodyPt, lines, padYPt);
    }),
  ];
  let tableH = rowH.reduce((a, b) => a + b, 0);
  if (tableH > maxTableH && tableH > 0) {
    const scale = maxTableH / tableH;
    for (let i = 0; i < rowH.length; i++) rowH[i] *= scale;
    tableH = maxTableH;
  }
  if (meta.summary_after) {
    chrome.addText(
      slide,
      theme,
      meta.summary_after,
      { x: area.x, y: area.y + tableH + 0.12, w: area.w, h: summaryH },
      {
        fontFace: theme.fonts.body,
        fontSize: chrome.pxToPt(theme, theme.sizesPx.summary),
        color: theme.colors.ink,
      }
    );
  }
  const rows = [
    data.headers.map((text) => ({
      text,
      options: {
        fill: { color: theme.colors.ink },
        color: "FFFFFF",
        bold: true,
        fontFace: theme.fonts.body,
        fontSize: headPt,
        valign: "middle",
        margin: [padYPt, padXPt, padYPt, padXPt],
      },
    })),
    ...data.rows.map((row) =>
      row.map((cell) => ({
        text: cell.text,
        options: {
          fill: { color: theme.colors.bg },
          color: cell.hl ? theme.colors.accent : theme.colors.ink,
          bold: !!cell.hl,
          fontFace: theme.fonts.body,
          fontSize: bodyPt,
          valign: "top",
          margin: [padYPt, padXPt, padYPt, padXPt],
        },
      }))
    ),
  ];
  slide.addTable(rows, {
    x: area.x,
    y: area.y,
    w: area.w,
    h: tableH,
    colW,
    rowH,
    border: [
      { pt: 1.5, color: theme.colors.ink },
      { pt: 1.5, color: theme.colors.ink },
      { pt: 1.5, color: theme.colors.ink },
      { pt: 1.5, color: theme.colors.ink },
    ],
    fontFace: theme.fonts.body,
    valign: "top",
  });
}

function tableCards(slide, pres, theme, page) {
  const area = paintChrome(slide, pres, theme, page);
  const data = page.table || { headers: [], rows: [] };
  const meta = page.meta || {};
  const step = textStep(theme, meta.text_size) || {};
  const bodyPx = step.table || theme.sizesPx.table;
  const headPx = step.tableHead || theme.sizesPx.tableHead;
  const gap = 0.1;
  const labelH = 0.26;
  const labelGap = 0.06;
  const labelPt = chrome.pxToPt(theme, 22);
  let y = area.y;

  function sectionLabel(text) {
    if (!text) return;
    chrome.addText(
      slide,
      theme,
      text,
      { x: area.x, y, w: area.w, h: labelH },
      {
        fontFace: theme.fonts.body,
        fontSize: labelPt,
        color: theme.colors.ink,
        bold: true,
      }
    );
    y += labelH + labelGap;
  }

  sectionLabel(meta.table_title);
  const tableBox = { x: area.x, y, w: area.w, h: Math.min(area.h * 0.34, area.h) };
  const colCount = data.headers.length || 1;
  const colW = tableColWidths(tableBox, meta, colCount);
  const headPt = chrome.pxToPt(theme, headPx);
  const bodyPt = chrome.pxToPt(theme, bodyPx);
  const padYPt = chrome.pxToPt(theme, 14);
  const padXPt = chrome.pxToPt(theme, 16);
  const headLines = data.headers.reduce(
    (n, text, i) => Math.max(n, tableCellLines(theme, text, headPt, colW[i])),
    1
  );
  const rowH = [
    tableRowH(headPt, headLines, padYPt),
    ...data.rows.map((row) => {
      const lines = row.reduce(
        (n, cell, i) => Math.max(n, tableCellLines(theme, cell.text, bodyPt, colW[i])),
        1
      );
      return tableRowH(bodyPt, lines, padYPt);
    }),
  ];
  let tableH = rowH.reduce((a, b) => a + b, 0);
  if (tableH > tableBox.h && tableH > 0) {
    const scale = tableBox.h / tableH;
    for (let i = 0; i < rowH.length; i++) rowH[i] *= scale;
    tableH = tableBox.h;
  }
  const rows = [
    data.headers.map((text) => ({
      text,
      options: {
        fill: { color: theme.colors.ink },
        color: "FFFFFF",
        bold: true,
        fontFace: theme.fonts.body,
        fontSize: headPt,
        valign: "middle",
        margin: [padYPt, padXPt, padYPt, padXPt],
      },
    })),
    ...data.rows.map((row) =>
      row.map((cell) => ({
        text: cell.text,
        options: {
          fill: { color: theme.colors.bg },
          color: cell.hl ? theme.colors.accent : theme.colors.ink,
          bold: !!cell.hl,
          fontFace: theme.fonts.body,
          fontSize: bodyPt,
          valign: "top",
          margin: [padYPt, padXPt, padYPt, padXPt],
        },
      }))
    ),
  ];
  slide.addTable(rows, {
    x: tableBox.x,
    y: tableBox.y,
    w: tableBox.w,
    h: tableH,
    colW,
    rowH,
    border: [
      { pt: 1.5, color: theme.colors.ink },
      { pt: 1.5, color: theme.colors.ink },
      { pt: 1.5, color: theme.colors.ink },
      { pt: 1.5, color: theme.colors.ink },
    ],
    fontFace: theme.fonts.body,
    valign: "top",
  });
  y += tableH + gap;
  sectionLabel(meta.cards_title);
  const cardsBox = { x: area.x, y, w: area.w, h: Math.max(0.5, area.y + area.h - y) };
  const cols = Number(meta.columns || 3);
  const items = scaleCards(theme, page, page.cards || []);
  const boxes = chrome.gridBoxes(items.length, cols, cardsBox, chrome.pxToIn(theme, theme.gapPx));
  items.forEach((card, i) => chrome.drawCard(slide, pres, theme, card, boxes[i]));
}

module.exports = {
  title,
  section,
  cards,
  split,
  "stack-split": stackSplit,
  table,
  "table-cards": tableCards,
};
