// Woven — layout constants and coordinate maths.
// Spec: data/research/design/WOVEN_SPEC.md section 2.1.

export const YEAR_MIN = 1880;
export const YEAR_MAX = 2026;
export const YEAR_SPAN = YEAR_MAX - YEAR_MIN; // 146
export const X_PER_YEAR = 0.5;
export const PITCH = 0.16;
export const BAND_GAP = 0.7;
export const BAND_TOP_A = -0.6;
export const WEAVE_AMP = 0.035;

export const BAND_DEFS = [
  { key: 'A', from: 1880, to: 1899, label: '1880 to 1899' },
  { key: 'B', from: 1900, to: 1929, label: '1900 to 1929' },
  { key: 'C', from: 1930, to: 1949, label: '1930 to 1949' },
  { key: 'D', from: 1950, to: 1969, label: '1950 to 1969' },
  { key: 'E', from: 1970, to: 1989, label: '1970 to 1989' },
  { key: 'F', from: 1990, to: 2009, label: '1990 to 2009' },
  { key: 'G', from: 2010, to: 2026, label: '2010 to 2026' },
  { key: 'U', from: null, to: null, label: 'founding year unrecorded' }
];

export function bandKeyFor(year) {
  if (!year) return 'U';
  for (const b of BAND_DEFS) {
    if (b.from !== null && year >= b.from && year <= b.to) return b.key;
  }
  return 'U';
}

export function x(year) {
  return (year - YEAR_MIN) * X_PER_YEAR;
}

// Events predate the loom in eight cases (earliest is 1843). The warp starts at
// 1880 and we do not invent warp threads for years the cloth does not cover, so
// off-loom marks clamp to the left post and are labelled with their true date.
export function xClamped(year) {
  return Math.max(0, Math.min(x(YEAR_MAX), x(year)));
}

export function fractionalYear(d) {
  const m = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/.exec(String(d || ''));
  if (!m) return { year: null, value: null, precision: 'none' };
  const y = +m[1];
  const mo = m[2] ? +m[2] : null;
  const da = m[3] ? +m[3] : null;
  const value = y + ((mo ?? 6.5) - 1) / 12 + ((da ?? 15) - 1) / 365;
  return { year: y, value, precision: da ? 'day' : mo ? 'month' : 'year' };
}

// Seeded PRNG (mulberry32) so fray seeds and knot rolls are stable across reloads.
export function seededRandom(seed) {
  let a = seed >>> 0;
  return function () {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Assign every publication a band and a Y slot. Mutates nothing; returns a
 * layout object holding the band table, the slot table, and the cloth bounds.
 */
export function buildLayout(threads) {
  const byBand = new Map(BAND_DEFS.map((b) => [b.key, []]));
  for (const t of threads) byBand.get(t.bandKey).push(t);

  for (const list of byBand.values()) {
    list.sort((a, b) => {
      const ay = a.yearFounded ?? 99999;
      const by = b.yearFounded ?? 99999;
      if (ay !== by) return ay - by;
      return a.name.localeCompare(b.name);
    });
  }

  const bands = [];
  let top = BAND_TOP_A;
  for (const def of BAND_DEFS) {
    const list = byBand.get(def.key);
    const height = list.length * PITCH;
    const band = { ...def, top, height, count: list.length, threads: list };
    bands.push(band);
    list.forEach((t, j) => {
      t.band = def.key;
      t.slotIndex = j;
      t.y = top - (j + 0.5) * PITCH;
    });
    top = top - height - BAND_GAP;
  }

  // Flat slot table sorted by descending Y, for the binary search in picking.
  const slots = threads.slice().sort((a, b) => b.y - a.y);
  slots.forEach((t, i) => { t.globalIndex = i; });

  const bottom = top + BAND_GAP;
  return {
    bands,
    slots,
    bounds: { minX: 0, maxX: x(YEAR_MAX), minY: bottom, maxY: BAND_TOP_A },
    slotAtY
  };

  // Nearest slot to a world Y. O(log n) over the descending-Y slot table.
  function slotAtY(worldY) {
    let lo = 0;
    let hi = slots.length - 1;
    if (!slots.length) return null;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (slots[mid].y > worldY) lo = mid + 1; else hi = mid;
    }
    // Compare the candidate and its predecessor.
    const a = slots[lo];
    const b = lo > 0 ? slots[lo - 1] : null;
    if (b && Math.abs(b.y - worldY) < Math.abs(a.y - worldY)) return b;
    return a;
  }
}

/** Distance at which a bounding box fits the frustum with `margin` slack. */
export function fitDistance(box, margin, camera) {
  const w = (box.maxX - box.minX) * (1 + margin * 2);
  const h = (box.maxY - box.minY) * (1 + margin * 2);
  const vFov = (camera.fov * Math.PI) / 180;
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
  const dV = h / 2 / Math.tan(vFov / 2);
  const dH = w / 2 / Math.tan(hFov / 2);
  return Math.max(dV, dH, 8);
}

export function boxCenter(box) {
  return [(box.minX + box.maxX) / 2, (box.minY + box.maxY) / 2, 0];
}

export const easeInOutCubic = (t) =>
  t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
