import assert from 'node:assert/strict';
import fs from 'node:fs';
import { clothPoint, distanceToSegment, matchesFilters, publicationYears, threadColor, threadSpans } from '../docs/js/woven/exhibit-geometry.js';
import { buildLayout, bandKeyFor } from '../docs/js/woven/layout.js';

const doc = JSON.parse(fs.readFileSync(new URL('../docs/data/publications.json', import.meta.url)));
const allowed = new Set(['publishable', 'publishable_with_credit', 'crop_first']);
const threads = (doc.publications || doc).map(p => ({
  ...p, bandKey: bandKeyFor(p.yearFounded ?? null), unknownFounding: p.yearFounded == null, endState: p.isActive ? 'still' : 'ceased',
  ghost: !(p.evidence || []).some(e => allowed.has(e.rightsStatus)),
  startYear: p.yearFounded ?? 2026, endYear: p.yearCeased ?? 2026
}));
buildLayout(threads);
assert(threads.length > 100);
for (const t of threads) {
  assert.match(threadColor(t), /^#[a-f0-9]{6}$/);
  assert(publicationYears(t).length > 0);
  for (const [a,b] of threadSpans(t)) {
    assert(Number.isFinite(a) && Number.isFinite(b) && b > a, `Invalid span for ${t.id}`);
    const point = clothPoint(a, t.y, -30);
    assert(point.every(Number.isFinite));
  }
  assert.equal(matchesFilters(t), true);
  assert.equal(matchesFilters(t, {city: String(t.city || '')}), true);
  assert.equal(matchesFilters(t, {city: 'not a municipality'}), false);
  assert.equal(matchesFilters(t, {evidence: 'active'}), !!t.isActive);
  assert.equal(matchesFilters(t, {evidence: 'evidence'}), !t.ghost);
  assert.equal(matchesFilters(t, {evidence: 'unillustrated'}), t.ghost);
  if (t.yearFounded != null && t.yearCeased == null && !t.isActive) {
    assert(publicationYears(t).includes('end date unrecorded'));
    assert(!publicationYears(t).includes('present'));
  }
  if (t.unknownFounding) assert.equal(threadSpans(t).length, 5);
}
assert.equal(distanceToSegment(5,3,0,0,10,0),3);
assert.equal(distanceToSegment(4,3,0,0,0,0),5);
assert.equal(distanceToSegment(15,0,0,0,10,0),5);
assert.deepEqual(threadSpans({yearFounded:1900,yearCeased:1900}), [[1900,1900.5]]);
assert.equal(threads.filter(t => matchesFilters(t,{evidence:'active'})).length, threads.filter(t=>t.isActive).length);
console.log(`PASS: ${threads.length} publication spans, dates, colors, combined filters, and hit-distance geometry`);
