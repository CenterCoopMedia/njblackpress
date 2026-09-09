// Both views preserve publication dates. Bars sit on separate rows in a curved gallery.
import { YEAR_MIN, YEAR_MAX } from './layout.js';

export function timelinePoint(year, row, bottom) {
  const u = (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN);
  const v = row - bottom / 2;
  // Depth varies only by row. Each publication stays straight along the year axis.
  return [(u - 0.5) * 80, v * 1.18, Math.cos(v * 0.065) * 8 - 4];
}

// Undated fragments are status marks in the separate undated band, not dates.
// A same-year record gets a small mark so it remains visible and selectable.
export function threadSpans(thread) {
  if (thread.unknownFounding) {
    const fragments = [1880, 1910, 1940, 1970, 2000].map((position) => [position, position + 20]);
    if (thread.endState === 'still') fragments.push([YEAR_MAX, YEAR_MAX + 7]);
    return fragments;
  }
  const start = thread.yearFounded;
  const end = thread.endState === 'still' ? YEAR_MAX + 7 : thread.yearCeased ?? YEAR_MAX;
  return [[start, Math.max(start + 0.25, end)]];
}

export function distanceToSegment(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}
