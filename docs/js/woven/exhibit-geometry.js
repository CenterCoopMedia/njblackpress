// A sculptural view of the existing timeline. Depth is an artistic treatment,
// not a claim about relationships, circulation, or a publication's influence.
import { YEAR_MIN, YEAR_MAX } from './layout.js';

export const THREAD_COLORS = ['#cb7857', '#d59c59', '#cfb37c', '#b1a0b8', '#83a69b', '#91b7c2', '#ead5af'];
export const EVIDENCE_FILTERS = new Set(['all', 'active', 'evidence', 'unillustrated']);

export function threadColor(thread) {
  const index = 'ABCDEFG'.indexOf(thread.bandKey);
  return index < 0 ? '#a7a4a0' : THREAD_COLORS[index];
}

export function publicationYears(thread) {
  if (thread.yearFounded == null) return 'Founding year unrecorded';
  if (thread.endState === 'still') return `${thread.yearFounded}–present`;
  if (thread.yearCeased != null) return `${thread.yearFounded}–${thread.yearCeased}`;
  return `${thread.yearFounded} · end date unrecorded`;
}

export function matchesFilters(thread, { city = '', evidence = 'all' } = {}) {
  if (city && String(thread.city || '') !== city) return false;
  if (evidence === 'active') return thread.endState === 'still';
  if (evidence === 'evidence') return !thread.ghost;
  if (evidence === 'unillustrated') return thread.ghost;
  return true;
}

export function clothPoint(year, row, bottom) {
  const u = (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN);
  const v = row - bottom / 2;
  return [
    (u - 0.5) * 80,
    v * 0.94 + Math.sin(u * Math.PI * 1.5 - 0.6) * 5.5,
    Math.sin(u * Math.PI * 1.5 + v * 0.065) * 7 + Math.cos(v * 0.2 + u * 4) * 1.2
  ];
}

// Undated publications are stitched fragments, not invented lifespans.
// An unknown end is drawn as a dashed continuation, never a present-day claim.
export function threadSpans(thread) {
  if (thread.unknownFounding) {
    return [1890, 1920, 1950, 1980, 2010].map((year) => [year, year + 5]);
  }
  const start = Math.max(YEAR_MIN, Math.min(YEAR_MAX, thread.yearFounded));
  const end = thread.endState === 'still' ? YEAR_MAX + 7 : (thread.yearCeased ?? YEAR_MAX);
  // A one-year record needs a visible mark. This half-year width is a glyph,
  // not an assertion that it published for another year.
  return [[start, Math.max(start + 0.5, Math.min(YEAR_MAX + 7, end))]];
}

export function distanceToSegment(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}
