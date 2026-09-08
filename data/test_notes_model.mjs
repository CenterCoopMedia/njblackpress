import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  loadModel,
  publicationYears,
  publishingAt,
  safeURL
} from '../docs/js/notes/data.js';
import {
  project,
  YEAR_MIN,
  YEAR_MAX,
  Y_NOW,
  yearToY
} from '../docs/js/notes/geo.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const sourceFiles = {
  'data/publications.json': 'docs/data/publications.json',
  'data/events.json': 'docs/data/events.json',
  'data/stories.json': 'docs/data/stories.json',
  'data/clippings.json': 'docs/data/clippings.json',
  'data/map-publications.json': 'docs/data/map-publications.json',
  'data/nj-outline.json': 'docs/data/nj-outline.json'
};

globalThis.fetch = async (url) => {
  const relative = sourceFiles[String(url)];
  if (!relative) return { ok: false, status: 404, json: async () => ({}) };
  const file = path.join(ROOT, relative);
  return {
    ok: true,
    status: 200,
    json: async () => JSON.parse(await readFile(file, 'utf8'))
  };
};

const model = await loadModel();

assert.equal(model.counts.total, 136);
assert.equal(model.counts.active, 17);
assert.equal(model.counts.stories, 13);
assert.equal(model.counts.clippings, 55);
assert.equal(model.counts.unrecordedYears, 3);
assert.equal(model.publications.length, model.byId.size);
assert.equal(model.events.length, 81);
assert.equal(model.marks.length, model.events.length);
assert.equal(model.outline.coordinates.length, 163);

const sourcePublications = JSON.parse(await readFile(path.join(ROOT, 'docs/data/publications.json'), 'utf8')).publications;
for (const source of sourcePublications) {
  const publication = model.byId.get(source.id);
  assert.ok(publication, `missing publication ${source.id}`);
  for (const [key, value] of Object.entries(source)) assert.deepEqual(publication[key], value);
  assert.ok(publication.clusterId);
  assert.equal(typeof publication.active, 'boolean');
  assert.equal(typeof publication.unsourced, 'boolean');
  assert.ok(Number.isFinite(publication.x));
  assert.ok(Number.isFinite(publication.z));
  assert.ok(Number.isFinite(publication.startY));
  assert.ok(Number.isFinite(publication.endY));
}

assert.equal(YEAR_MIN, 1880);
assert.equal(YEAR_MAX, 2026);
assert.equal(yearToY(YEAR_MIN), 0);
assert.equal(yearToY(YEAR_MAX), Y_NOW);
assert.equal(yearToY(1909.25), (1909.25 - YEAR_MIN) * 0.12);
assert.equal(yearToY(null), null);

const landscape = model.byId.get(34);
assert.equal(landscape.startKnown, true);
assert.equal(landscape.endKnown, true);
assert.equal(landscape.startY, yearToY(1881));
assert.equal(landscape.endY, yearToY(1901));
assert.equal(publishingAt(landscape, 1880), false);
assert.equal(publishingAt(landscape, 1881), true);
assert.equal(publishingAt(landscape, 1901), true);
assert.equal(publishingAt(landscape, 1902), false);
assert.equal(publicationYears(landscape), '1881–1901');

const activeWithoutStart = model.byId.get(14);
assert.equal(activeWithoutStart.startKnown, false);
assert.equal(activeWithoutStart.endKnown, true);
assert.equal(activeWithoutStart.active, true);
assert.equal(publishingAt(activeWithoutStart, 2020), false);
assert.equal(activeWithoutStart.endY, Y_NOW);
assert.equal(publicationYears(activeWithoutStart), 'Founding year unrecorded · still publishing');

const metadataOnly = model.byId.get(1);
assert.ok(metadataOnly.evidence.length > 0);
assert.equal(metadataOnly.unsourced, true);
assert.equal(model.byId.get(6).unsourced, false);

const newark = model.clusters.find((cluster) => cluster.id === 'newark-nj');
assert.ok(newark);
assert.equal(newark.members.length, 38);
const savedNewark = project(40.735657, -74.1723667);
assert.deepEqual(newark.trueXZ, savedNewark);

const shelfIds = new Set(model.clusters.filter((cluster) => cluster.shelf).map((cluster) => cluster.id));
assert.deepEqual(shelfIds, new Set(['chicago-il', 'fort-wayne-in', 'new-jersey-statewide', 'place-not-recorded']));
for (const cluster of model.clusters.filter((item) => item.shelf)) {
  assert.equal(cluster.trueXZ, null);
  assert.equal(cluster.displaced, false);
}
assert.deepEqual(
  model.clusters.find((cluster) => cluster.id === 'place-not-recorded').members.sort((a, b) => a - b),
  [127, 128]
);

for (let leftIndex = 0; leftIndex < model.clusters.length; leftIndex += 1) {
  for (let rightIndex = leftIndex + 1; rightIndex < model.clusters.length; rightIndex += 1) {
    const left = model.clusters[leftIndex];
    const right = model.clusters[rightIndex];
    const distance = Math.hypot(left.placedXZ.x - right.placedXZ.x, left.placedXZ.z - right.placedXZ.z);
    assert.ok(distance + 1e-6 >= left.radius + right.radius, `${left.id} overlaps ${right.id}`);
  }
}

const echoStory = model.stories.find((story) => story.id === 'story-004');
assert.deepEqual(echoStory.stops.map((stop) => stop.dateLabel), ['1904', '1909-03-05', '1921-04-09']);
const echoMove = echoStory.stops.find((stop) => stop.eventId === 'evt-019');
assert.equal(echoMove.publicationId, 31);
assert.equal(echoMove.clipping.status, 'publishable');
assert.equal(echoMove.clipping.webPath, 'images/evidence/asbury-park-press_1909-03-05_p2_echo-moves-red-bank.jpg');
assert.equal(echoStory.stops.find((stop) => stop.eventId === 'evt-022').clipping, null);

assert.equal(model.sourceRights('asbury-park-press_1909-03-05_p2_echo-moves-red-bank.json'), 'publishable');
assert.equal(model.sourceRights('other-paper_1909-03-05.json'), null);
assert.equal(model.citeSource('asbury-park-press_1909-03-05_p2_echo-moves-red-bank.json'), 'Asbury Park Press, 1909-03-05, p. 2.');
assert.ok(model.citeSource('new-york-tribune_1895-12-08_p14_herbert-profile.json'));

assert.equal(safeURL('images/evidence/example.jpg'), 'images/evidence/example.jpg');
assert.equal(safeURL('javascript:alert(1)'), '');
assert.equal(safeURL('images/evidence/../secret.jpg'), '');

console.log('PASS: notes model preserves archive records, dates, coordinates, clusters, and source rights');
