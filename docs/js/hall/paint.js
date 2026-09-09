// History hall — every painted surface in the hall.
//
// Sheet faces, brass plates, decade markers, book covers, and book pages are
// drawn on 2D canvases and handed to the scene as textures. Type is drawn, not
// modelled: a typeset publication name is a contemporary exhibit label, never a
// recreated masthead, and nothing here invents historical imagery. Where a
// cleared wall copy exists it is drawn whole, fitted inside its space, never
// cropped again.

import * as THREE from 'three';

// The palette comes from the site's Tailwind tokens through one object, so the
// hall and the page cannot drift apart.
export const PAINT = {
  paper: '#f3eee2',
  pageWarm: '#f7f0e0',
  paperShade: '#e3dccc',
  ink: '#14100b',
  inkSoft: '#4b4335',
  rule: '#cdc4b1',
  brass: '#a89179',
  brassEdge: '#8a7252',
  brassInk: '#241c12',
  walnut: '#2b2318',
  // The site's stain accent. One token, so the hall's marks and the pages of a
  // volume cannot drift apart from each other or from the page.
  accent: '#e2662b',
  display: '"Libre Franklin", "Helvetica Neue", Arial, sans-serif',
  body: '"DM Sans", Arial, sans-serif'
};

export const FACE_SIZE = { width: 512, height: 704 };
export const PLATE_SIZE = { width: 512, height: 100 };
export const MARKER_SIZE = { width: 288, height: 256 };
export const COVER_SIZE = { width: 320, height: 428 };
export const PAGE_SIZE = { width: 512, height: 704 };

/**
 * Fonts arrive after the first paint on a cold visit. Entry never waits for
 * them: the hall paints with the fallback stack, and repaints once the real
 * faces are ready.
 */
export function whenFontsReady(callback) {
  if (!document.fonts || !document.fonts.ready) return () => {};
  let live = true;
  const wanted = ['700 48px "Libre Franklin"', '400 24px "DM Sans"'];
  Promise.all(wanted.map((font) => document.fonts.load(font).catch(() => null)))
    .then(() => document.fonts.ready)
    .then(() => { if (live) callback(); })
    .catch(() => {});
  return () => { live = false; };
}

function surface(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return { canvas, ctx: canvas.getContext('2d') };
}

/**
 * What one texture of this size costs in GPU memory, as RGBA8 with a full mip
 * chain. The mip chain adds a third again. This is a calculation from the
 * dimensions, not a measurement, and the review reports it as such.
 */
export function textureBytes(width, height) {
  return Math.round(width * height * 4 * (4 / 3));
}

/** A canvas becomes a colour texture, so it must say it holds sRGB colour. */
export function textureFrom(canvas, anisotropy = 4) {
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.anisotropy = anisotropy;
  texture.needsUpdate = true;
  return texture;
}

function wrap(ctx, text, maxWidth, maxLines = 99) {
  const words = String(text || '').split(/\s+/).filter(Boolean);
  const lines = [];
  let line = '';
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width <= maxWidth || !line) { line = next; continue; }
    lines.push(line);
    line = word;
    if (lines.length === maxLines) break;
  }
  if (lines.length < maxLines && line) lines.push(line);
  if (lines.length === maxLines && words.length) {
    // Trailing ellipsis only when something really was left out.
    const joined = lines.join(' ');
    if (joined.split(/\s+/).length < words.length) lines[lines.length - 1] = `${lines[lines.length - 1]}…`;
  }
  return lines;
}

function drawLines(ctx, lines, x, y, lineHeight) {
  let cursor = y;
  for (const line of lines) {
    ctx.fillText(line, x, cursor);
    cursor += lineHeight;
  }
  return cursor;
}

// Low contrast grain. Printed matter is the most distinct thing in the hall, so
// the paper under it stays quiet.
function grain(ctx, width, height, amount = 8) {
  const image = ctx.getImageData(0, 0, width, height);
  const data = image.data;
  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * amount;
    data[i] += noise; data[i + 1] += noise; data[i + 2] += noise;
  }
  ctx.putImageData(image, 0, 0);
}

/**
 * One sheet face: publication name first, then city, then the shared date
 * sentence, and below the rule either the cleared wall copy, the record's own
 * exhibit label, or the line that says no copy is cleared for display here.
 *
 * @param {object} view prepared record view from hall.js
 * @param {HTMLImageElement|null} image decoded wall copy, when one is cleared
 * @param {{unavailable?: boolean}} [state] the copy is cleared but would not load
 */
export function paintSheetFace(view, image, state = {}) {
  const { width, height } = FACE_SIZE;
  const { canvas, ctx } = surface(width, height);
  ctx.fillStyle = PAINT.paper;
  ctx.fillRect(0, 0, width, height);

  const pad = 40;
  const textWidth = width - pad * 2;

  // Era colour is an accent on the sheet, never the only carrier of meaning:
  // the dates and the plate say the same thing in words.
  ctx.fillStyle = view.eraColor;
  ctx.fillRect(pad, 34, 74, 7);

  ctx.fillStyle = PAINT.ink;
  ctx.textBaseline = 'top';
  const name = String(view.name || 'Untitled publication');
  let size = name.length > 46 ? 36 : name.length > 28 ? 42 : 50;
  let lines = [];
  for (;;) {
    ctx.font = `700 ${size}px ${PAINT.display}`;
    lines = wrap(ctx, name, textWidth, 4);
    if (lines.length <= 3 || size <= 30) break;
    size -= 4;
  }
  let y = drawLines(ctx, lines, pad, 66, size * 1.08);

  y += 14;
  ctx.font = `400 24px ${PAINT.body}`;
  ctx.fillStyle = PAINT.inkSoft;
  ctx.fillText(view.city || 'City unrecorded', pad, y);
  y += 34;
  ctx.font = `500 27px ${PAINT.body}`;
  ctx.fillStyle = PAINT.ink;
  ctx.fillText(view.dateText, pad, y);
  y += 44;

  ctx.strokeStyle = PAINT.rule;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(pad, y);
  ctx.lineTo(width - pad, y);
  ctx.stroke();
  y += 26;

  const boxHeight = height - y - pad;
  if (image && image.naturalWidth) {
    // Fitted whole. A wall copy is already cropped and cleared; the hall never
    // crops one again to make it fill a space.
    const scale = Math.min(textWidth / image.naturalWidth, boxHeight / image.naturalHeight);
    const w = Math.max(1, Math.round(image.naturalWidth * scale));
    const h = Math.max(1, Math.round(image.naturalHeight * scale));
    const x = Math.round(pad + (textWidth - w) / 2);
    ctx.fillStyle = PAINT.paperShade;
    ctx.fillRect(x - 6, y - 6, w + 12, h + 12);
    ctx.drawImage(image, x, y, w, h);
    ctx.strokeStyle = view.rightsStatus === 'crop_first' ? view.eraColor : PAINT.rule;
    ctx.lineWidth = 2;
    ctx.strokeRect(x - 6.5, y - 6.5, w + 13, h + 13);
  } else {
    ctx.fillStyle = PAINT.inkSoft;
    ctx.font = `400 25px ${PAINT.body}`;
    // An image that would not load is said in words on the sheet itself, so a
    // blank space is never mistaken for "nothing survives".
    const label = state.unavailable
      ? 'Image unavailable. The cleared copy could not be loaded here; its record is in the panel.'
      : view.note || 'No copies cleared for display here. Copies may survive elsewhere.';
    drawLines(ctx, wrap(ctx, label, textWidth, Math.floor(boxHeight / 34)), pad, y, 34);
  }

  grain(ctx, width, height, 7);
  return canvas;
}

/**
 * The brass plate under a sheet: founding year, how many source records the
 * archive holds, whether the title still publishes, and the credit a cleared
 * copy requires. The plate supplements the record panel's attribution; it never
 * replaces it.
 */
export function paintPlate(view) {
  const { width, height } = PLATE_SIZE;
  const { canvas, ctx } = surface(width, height);
  ctx.fillStyle = PAINT.brass;
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = PAINT.brassEdge;
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, width - 2, height - 2);

  ctx.fillStyle = PAINT.brassInk;
  ctx.textBaseline = 'top';
  ctx.font = `700 26px ${PAINT.display}`;
  const year = view.yearFounded == null ? 'Date unrecorded' : String(view.yearFounded);
  ctx.fillText(year, 16, 12);

  ctx.font = `500 18px ${PAINT.body}`;
  const right = [view.recordsLabel];
  if (view.active) right.push('Still publishing');
  ctx.textAlign = 'right';
  ctx.fillText(right.join(' · '), width - 16, 16);
  ctx.textAlign = 'left';

  // A cropped detail still carries its citation: the rights rule for crop_first
  // material is that it may be published only as a cited crop, so the words
  // "Cropped detail" never stand in for the credit. The record panel keeps the
  // full credit either way, which is why small type here is safe.
  const credit = view.rightsStatus === 'crop_first'
    ? ['Cropped detail', view.citation].filter(Boolean).join(' · ')
    : view.rightsStatus === 'publishable_with_credit' && view.citation ? view.citation : '';
  if (credit) {
    ctx.font = `400 13px ${PAINT.body}`;
    drawLines(ctx, wrap(ctx, credit, width - 32, 2), 16, 48, 17);
  }
  return canvas;
}

/** A decade marker, painted as a wall plate above the sheets. */
export function paintMarker(label) {
  const { width, height } = MARKER_SIZE;
  const { canvas, ctx } = surface(width, height);
  ctx.fillStyle = PAINT.brass;
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = PAINT.brassEdge;
  ctx.lineWidth = 4;
  ctx.strokeRect(2, 2, width - 4, height - 4);
  ctx.fillStyle = PAINT.brassInk;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const text = String(label);
  ctx.font = `800 ${text.length > 6 ? 44 : 88}px ${PAINT.display}`;
  const lines = wrap(ctx, text, width - 36, 2);
  const lineHeight = text.length > 6 ? 52 : 92;
  lines.forEach((line, i) => {
    ctx.fillText(line, width / 2, height / 2 + (i - (lines.length - 1) / 2) * lineHeight);
  });
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  return canvas;
}

/** A closed volume's cover: the approved title, its era wording, and its note. */
export function paintCover(story, eraColor) {
  const { width, height } = COVER_SIZE;
  const { canvas, ctx } = surface(width, height);
  ctx.fillStyle = PAINT.walnut;
  ctx.fillRect(0, 0, width, height);
  // A muted era colour, so the covers read as a set rather than as a rating.
  ctx.globalAlpha = 0.35;
  ctx.fillStyle = eraColor;
  ctx.fillRect(0, 0, width, height);
  ctx.globalAlpha = 1;
  ctx.strokeStyle = PAINT.brass;
  ctx.lineWidth = 3;
  ctx.strokeRect(14.5, 14.5, width - 29, height - 29);

  ctx.fillStyle = PAINT.paper;
  ctx.textBaseline = 'top';
  ctx.font = `700 30px ${PAINT.display}`;
  const lines = wrap(ctx, story.title, width - 68, 6);
  let y = drawLines(ctx, lines, 34, 52, 36);
  y += 16;
  ctx.font = `400 21px ${PAINT.body}`;
  ctx.fillStyle = PAINT.rule;
  ctx.fillText(story.era || '', 34, y);
  if (story.note) {
    y += 30;
    drawLines(ctx, wrap(ctx, story.note, width - 68, 2), 34, y, 26);
  }
  ctx.font = `400 19px ${PAINT.body}`;
  ctx.fillText(`${story.stopCount} stop${story.stopCount === 1 ? '' : 's'}`, 34, height - 62);
  return canvas;
}

/**
 * One page of the open volume. The left page carries the cleared clipping, the
 * right page carries the stop's title and date at headline size, and a stop
 * without a clipping gets a deliberate text page rather than invented paper.
 */
export function paintPage(page, image) {
  const { width, height } = PAGE_SIZE;
  const { canvas, ctx } = surface(width, height);
  ctx.fillStyle = PAINT.pageWarm;
  ctx.fillRect(0, 0, width, height);
  const pad = 44;
  const inner = width - pad * 2;
  ctx.textBaseline = 'top';

  if (page.kind === 'clipping' && image && image.naturalWidth) {
    const boxHeight = height - pad * 2 - 60;
    const scale = Math.min(inner / image.naturalWidth, boxHeight / image.naturalHeight);
    const w = Math.round(image.naturalWidth * scale);
    const h = Math.round(image.naturalHeight * scale);
    const x = Math.round(pad + (inner - w) / 2);
    const y = Math.round(pad + (boxHeight - h) / 2);
    ctx.drawImage(image, x, y, w, h);
    if (page.rightsStatus === 'crop_first') {
      // The outline says the public file is a cropped detail. It is a label, not
      // a crop: the hall never crops a cleared file.
      ctx.strokeStyle = page.accent || PAINT.accent;
      ctx.lineWidth = 3;
      ctx.strokeRect(x - 4.5, y - 4.5, w + 9, h + 9);
    }
    ctx.fillStyle = PAINT.inkSoft;
    ctx.font = `400 18px ${PAINT.body}`;
    drawLines(ctx, wrap(ctx, page.caption || '', inner, 2), pad, height - pad - 46, 23);
  } else if (page.kind === 'clipping') {
    ctx.fillStyle = PAINT.inkSoft;
    ctx.font = `400 23px ${PAINT.body}`;
    drawLines(ctx, wrap(ctx, page.message || 'No clipping is cleared for this stop.', inner, 6), pad, pad + 40, 32);
  } else {
    ctx.fillStyle = PAINT.inkSoft;
    ctx.font = `500 22px ${PAINT.body}`;
    ctx.fillText(page.date || '', pad, pad);
    ctx.fillStyle = PAINT.ink;
    let size = 44;
    let lines;
    for (;;) {
      ctx.font = `700 ${size}px ${PAINT.display}`;
      lines = wrap(ctx, page.title || '', inner, 7);
      if (lines.length <= 5 || size <= 28) break;
      size -= 4;
    }
    let y = drawLines(ctx, lines, pad, pad + 52, size * 1.12);
    if (page.note) {
      y += 20;
      ctx.font = `400 21px ${PAINT.body}`;
      ctx.fillStyle = PAINT.inkSoft;
      drawLines(ctx, wrap(ctx, page.note, inner, 4), pad, y, 28);
    }
    ctx.font = `400 18px ${PAINT.body}`;
    ctx.fillStyle = PAINT.inkSoft;
    ctx.fillText(page.footer || '', pad, height - pad - 22);
  }
  // The gutter side of the page darkens into the fold.
  if (page.gutter === 'left' || page.gutter === 'right') {
    const band = 64;
    const from = page.gutter === 'left' ? 0 : width;
    const to = page.gutter === 'left' ? band : width - band;
    const shade = ctx.createLinearGradient(from, 0, to, 0);
    shade.addColorStop(0, 'rgba(72, 58, 40, 0.30)');
    shade.addColorStop(1, 'rgba(72, 58, 40, 0)');
    ctx.fillStyle = shade;
    ctx.fillRect(Math.min(from, to), 0, band, height);
  }
  grain(ctx, width, height, 6);
  return canvas;
}

/** The shared low detail paper for sheets too far away to read. */
export function paintPlainPaper() {
  const { canvas, ctx } = surface(128, 176);
  ctx.fillStyle = PAINT.paper;
  ctx.fillRect(0, 0, 128, 176);
  ctx.fillStyle = PAINT.paperShade;
  ctx.fillRect(0, 0, 128, 10);
  grain(ctx, 128, 176, 10);
  return canvas;
}

/** Floor grain: dark walnut with a quiet, low contrast figure. */
export function paintFloor() {
  const { canvas, ctx } = surface(256, 256);
  ctx.fillStyle = '#463527';
  ctx.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 90; i++) {
    ctx.strokeStyle = `rgba(${120 + Math.random() * 40}, ${96 + Math.random() * 30}, ${64 + Math.random() * 24}, 0.07)`;
    ctx.lineWidth = 0.6 + Math.random() * 1.6;
    ctx.beginPath();
    const y = Math.random() * 256;
    ctx.moveTo(0, y);
    ctx.bezierCurveTo(85, y + (Math.random() - 0.5) * 8, 170, y + (Math.random() - 0.5) * 8, 256, y);
    ctx.stroke();
  }
  return canvas;
}

/**
 * The wall: pale plaster at reading height, fading deliberately into the dark
 * above the frames so the open top reads as a decision rather than as a hole.
 */
export function paintWall() {
  const { canvas, ctx } = surface(8, 256);
  // Pale plaster through the whole reading height, so the frames hang on light
  // wall. The fade begins above the decade markers, around 3.5 metres, and is
  // deliberate: the room has no ceiling and the top must not read as a hole.
  const gradient = ctx.createLinearGradient(0, 256, 0, 0);
  gradient.addColorStop(0, '#d4c9b4');
  gradient.addColorStop(0.18, '#e3dccc');
  gradient.addColorStop(0.55, '#ded6c4');
  gradient.addColorStop(0.80, '#cdc2ab');
  gradient.addColorStop(0.86, '#8d8271');
  gradient.addColorStop(0.93, '#33291d');
  gradient.addColorStop(1, '#0b0806');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 8, 256);
  return canvas;
}
