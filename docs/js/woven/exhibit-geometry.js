// Sculpture coordinates are artistic, not dates or publication relationships.
// The separate timeline preserves the archive's recorded publication spans.
import { YEAR_MIN, YEAR_MAX } from './layout.js';

export const THREAD_COLORS = ['#cb7857', '#d59c59', '#cfb37c', '#b1a0b8', '#83a69b', '#91b7c2', '#ead5af'];

export function threadColor(thread) {
  const index = 'ABCDEFG'.indexOf(thread.bandKey);
  return index < 0 ? '#a89c85' : THREAD_COLORS[index];
}

export function publicationYears(thread) {
  if (thread.yearFounded == null) {
    const end = thread.endState === 'still' ? 'still publishing'
      : thread.yearCeased != null ? `ceased ${thread.yearCeased}` : 'end date unrecorded';
    return `Founding year unrecorded · ${end}`;
  }
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
    v * 1.18 + Math.sin(u * Math.PI * 1.8 - 0.6) * 4.5,
    Math.sin(u * Math.PI * 2 + v * 0.055) * 10 + Math.cos(v * 0.2 + u * 4) * 1.6
  ];
}

// Every title crosses the sculpture. Length is not a lifespan: only the
// separate Timeline view encodes dates. The year constants are parameters for
// the surface function, not an axis in this scene. Undated titles use fragments
// and active titles have loose ends; neither implies an invented chronology.
export function threadSpans(thread) {
  if (thread.unknownFounding) {
    return [1880, 1910, 1940, 1970, 2000].map((position) => [position, position + 20]);
  }
  return [[YEAR_MIN, YEAR_MAX + (thread.endState === 'still' ? 7 : 0)]];
}

export function distanceToSegment(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}
