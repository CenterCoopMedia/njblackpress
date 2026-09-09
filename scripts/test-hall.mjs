// Pure checks for the history hall: layout, date wording, state machine, routes.
// Plain node, real archive data, no Three.js and no browser.
//
// Run: node scripts/test-hall.mjs

import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const documents = new Map();
for (const name of ['publications', 'events', 'stories', 'clippings']) {
  documents.set(`data/${name}.json`, JSON.parse(await readFile(new URL(`docs/data/${name}.json`, root))));
}
// data.js fetches four relative URLs. The archive on disk answers them.
globalThis.fetch = async (url) => ({ ok: true, json: async () => documents.get(url) });

const { loadModel } = await import('../docs/js/woven/data.js');
const {
  HALL_CONFIG, buildHallLayout, boxesOverlap, pointInBox,
  formatDates, dateCase, recordCount, recordsLabel, clearedRecordCount,
  beginsBefore1880, storyEraNote, storyFirstDecade, matchingOrder
} = await import('../docs/js/hall/layout.js');
const { createHallState } = await import('../docs/js/hall/state.js');
const links = await import('../docs/js/hall/links.js');

const model = await loadModel();
const source = documents.get('data/publications.json').publications;
const stories = documents.get('data/stories.json').stories;
const layout = buildHallLayout(model);

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

assert.equal(layout.slots.length, source.length, 'every publication gets one slot');
assert.equal(new Set(layout.publicationOrder).size, source.length, 'slots are unique per publication');
for (const publication of source) {
  assert.ok(layout.slotByPublicationId.has(publication.id), `${publication.name} has a slot`);
}
assert.equal(layout.warnings.length, 0, 'no publication or story needs a placement decision today');

assert.equal(layout.bookSlots.length, stories.length, 'every story gets one book slot');
assert.equal(new Set(layout.bookSlots.map((b) => b.storyId)).size, stories.length, 'book slots are unique per story');
for (const story of stories) {
  const slot = layout.bookSlotByStoryId.get(story.id);
  assert.ok(slot, `${story.id} rests on a table`);
  assert.ok(layout.sectionById.has(slot.sectionId));
}

// The migration fixture from the specification, verified against the layout.
const STORY_SECTIONS = {
  'story-001': '1880s', 'story-002': '1880s', 'story-003': '1880s', 'story-010': '1880s',
  'story-004': '1900s',
  'story-005': '1930s', 'story-006': '1930s', 'story-007': '1930s',
  'story-008': '1930s', 'story-009': '1930s', 'story-012': '1930s',
  'story-011': '1970s', 'story-013': '1980s'
};
for (const [storyId, sectionId] of Object.entries(STORY_SECTIONS)) {
  assert.equal(layout.bookSlotByStoryId.get(storyId).sectionId, sectionId, `${storyId} sits in ${sectionId}`);
}
assert.equal(beginsBefore1880({ era: '1860s-1900s' }), true);
assert.equal(beginsBefore1880({ era: '1880s-1900s' }), false);
assert.equal(storyEraNote({ era: '1870s-1970s' }), 'Begins before 1880');
assert.equal(storyEraNote({ era: '1930s-1940s' }), '');
assert.equal(storyFirstDecade({ era: '1900s-1920s' }), 1900);
for (const id of ['story-001', 'story-010']) {
  assert.equal(layout.bookSlotByStoryId.get(id).note, 'Begins before 1880', `${id} keeps its real era wording`);
}

// Sections run in order, cover the whole hall, and keep an anchor when empty.
const expectedSections = [];
for (let decade = 1880; decade <= 2020; decade += 10) expectedSections.push(`${decade}s`);
expectedSections.push('undated');
assert.deepEqual(layout.sections.map((s) => s.id), expectedSections);
let previousEnd = 0;
for (const section of layout.sections) {
  assert.equal(section.startZ, previousEnd, `${section.id} starts where the last section ended`);
  assert.ok(section.endZ > section.startZ, `${section.id} has length`);
  assert.ok(section.entryAnchor && section.entryAnchor.position, `${section.id} has an entry anchor`);
  assert.ok(section.entryAnchor.position.z > section.startZ && section.entryAnchor.position.z < section.endZ);
  assert.equal(section.markerBounds.length, 2, `${section.id} keeps a marker on both walls`);
  previousEnd = section.endZ;
}
assert.equal(previousEnd, layout.length);

const decadeCounts = { '1880s': 3, '1890s': 0, '1900s': 2, '1910s': 2, '1920s': 2, '1930s': 13, '1940s': 3, '1950s': 9, '1960s': 10, '1970s': 29, '1980s': 21, '1990s': 25, '2000s': 0, '2010s': 8, '2020s': 6 };
for (const [id, count] of Object.entries(decadeCounts)) {
  assert.equal(layout.sectionById.get(id).count, count, `${id} holds ${count} titles`);
}
for (const id of ['1890s', '2000s']) {
  const section = layout.sectionById.get(id);
  assert.equal(section.empty, true, `${id} is an empty decade`);
  assert.ok(section.entryAnchor, `${id} keeps a navigation destination`);
  assert.ok(section.length >= HALL_CONFIG.section.minLength);
}

const undatedCount = source.filter((p) => p.yearFounded == null).length;
assert.equal(undatedCount, 3, 'the archive holds three undated titles');
assert.equal(layout.sectionById.get('undated').count, undatedCount, 'the undated section holds exactly the undated records');
assert.equal(layout.sectionById.get('undated').label, 'Date unrecorded');

// Same-year clusters keep one slot each. Seven titles were founded in 1972.
const byYear = new Map();
for (const publication of source) {
  if (publication.yearFounded == null) continue;
  if (!byYear.has(publication.yearFounded)) byYear.set(publication.yearFounded, []);
  byYear.get(publication.yearFounded).push(publication);
}
const cluster1972 = byYear.get(1972);
assert.equal(cluster1972.length, 7, '1972 is the largest same-year cluster');
const clusterSlots = cluster1972.map((p) => layout.slotByPublicationId.get(p.id));
assert.equal(new Set(clusterSlots.map((s) => `${s.wall}:${s.z}`)).size, 7, 'seven titles get seven separate slots');
for (const slot of clusterSlots) assert.equal(slot.sectionId, '1970s');
for (const [, group] of byYear) {
  assert.equal(new Set(group.map((p) => layout.slotByPublicationId.get(p.id).index)).size, group.length);
}

// Walls alternate, and slot order follows founding year then publication id.
const dated = source.filter((p) => p.yearFounded != null)
  .sort((a, b) => a.yearFounded - b.yearFounded || a.id - b.id);
const datedOrder = layout.publicationOrder.filter((id) => model.byId.get(id).yearFounded != null);
assert.deepEqual(datedOrder, dated.map((p) => p.id), 'dated publications sort by founding year, then id');
for (const section of layout.sections) {
  const sectionWalls = section.publicationIds.map((id) => layout.slotByPublicationId.get(id).wall);
  if (!sectionWalls.length) continue;
  assert.equal(sectionWalls[0], 'left', `${section.id} opens on the left wall`);
  for (let i = 1; i < sectionWalls.length; i += 1) {
    assert.notEqual(sectionWalls[i], sectionWalls[i - 1], `${section.id} alternates walls in founding order`);
  }
}
assert.equal(new Set(layout.slots.map((s) => s.wall)).size, 2, 'both walls are used');
assert.equal(new Set(layout.slots.map((s) => s.y)).size, 1, 'one primary reading row');

// Nothing overlaps: no frame, marker, table, or book shares volume with another.
for (let i = 0; i < layout.collisions.length; i += 1) {
  for (let j = i + 1; j < layout.collisions.length; j += 1) {
    const a = layout.collisions[i];
    const b = layout.collisions[j];
    assert.ok(!boxesOverlap(a.box, b.box), `${a.id} overlaps ${b.id}`);
  }
}

// Every camera anchor stands in the corridor and inside nothing.
const anchors = [
  ...layout.sections.map((s) => ({ id: s.id, pose: s.entryAnchor })),
  ...layout.slots.map((s) => ({ id: `frame-${s.publicationId}`, pose: s.camera })),
  ...layout.bookSlots.map((s) => ({ id: `book-${s.storyId}`, pose: s.camera })),
  ...layout.bays.map((b) => ({ id: b.id, pose: b.anchor }))
];
for (const anchor of anchors) {
  const point = anchor.pose.position;
  assert.ok(Math.abs(point.x) <= HALL_CONFIG.corridorHalfWidth, `${anchor.id} stands in the corridor`);
  assert.ok(point.z >= 0 && point.z <= layout.length, `${anchor.id} stands inside the hall`);
  for (const item of layout.collisions) {
    assert.ok(!pointInBox(point, item.box), `${anchor.id} stands inside ${item.id}`);
  }
}
// Table bays sit outside the corridor the visitor walks along.
for (const bay of layout.bays) {
  const nearest = Math.min(Math.abs(bay.bounds.minX), Math.abs(bay.bounds.maxX));
  assert.ok(nearest >= HALL_CONFIG.corridorHalfWidth, `${bay.id} is outside the corridor`);
}

// The same data must produce the same hall, byte for byte in its serialised form.
const serialise = (l) => JSON.stringify({
  sections: l.sections, slots: l.slots, bays: l.bays, bookSlots: l.bookSlots,
  collisions: l.collisions, corridor: l.corridor, length: l.length
});
assert.equal(serialise(buildHallLayout(model)), serialise(buildHallLayout(model)), 'the layout is deterministic');

// Section length grows with the slots a section holds.
const dense = layout.sectionById.get('1970s');
const sparse = layout.sectionById.get('1910s');
assert.ok(dense.length > sparse.length, 'a dense decade is longer than a sparse one');
assert.ok(layout.sectionById.get('1950s').length > sparse.length, 'nine titles need more room than two');
assert.ok(sparse.length >= layout.sectionById.get('1890s').length, 'an empty decade is never longer than an occupied one');

// ---------------------------------------------------------------------------
// Stepping between publications under a filter
// ---------------------------------------------------------------------------

// No filter: Previous and Next walk the whole gallery in its own order.
assert.deepEqual(matchingOrder(layout, null), layout.publicationOrder);
// A filter narrows that order without reordering it: the result is always a
// subsequence of the gallery, never a new sort.
const newarkIds = new Set(source.filter((p) => p.city === 'Newark').map((p) => p.id));
const newarkOrder = matchingOrder(layout, newarkIds);
assert.ok(newarkOrder.length > 1 && newarkOrder.length < source.length, 'Newark is a real subset');
assert.deepEqual(newarkOrder, layout.publicationOrder.filter((id) => newarkIds.has(id)));
for (const id of newarkOrder) assert.ok(newarkIds.has(id));
// One match, and no match at all.
const oneMatch = new Set([layout.publicationOrder[7]]);
assert.deepEqual(matchingOrder(layout, oneMatch), [layout.publicationOrder[7]]);
assert.deepEqual(matchingOrder(layout, new Set()), [], 'a filter that matches nothing has nothing to step through');
// A record revealed past the filters can be stepped away from, and it keeps its
// own place in the gallery rather than being pushed to either end.
const outsider = layout.publicationOrder.find((id) => !newarkIds.has(id));
const revealedOrder = matchingOrder(layout, newarkIds, outsider);
assert.ok(revealedOrder.includes(outsider), 'a revealed record is reachable');
assert.deepEqual(revealedOrder, layout.publicationOrder.filter((id) => newarkIds.has(id) || id === outsider));
assert.equal(matchingOrder(layout, new Set(), outsider).length, 1, 'a revealed record survives a zero-result filter');

// ---------------------------------------------------------------------------
// Date wording and record counts
// ---------------------------------------------------------------------------

const DATE_CASES = [
  [{ yearFounded: 1934, yearCeased: 1966, isActive: false }, 'range', '1934–1966'],
  [{ yearFounded: 1990, yearCeased: null, isActive: true }, 'active', '1990–present'],
  [{ yearFounded: 1955, yearCeased: null, isActive: false }, 'end-unrecorded', '1955, end unrecorded'],
  [{ yearFounded: null, yearCeased: null, isActive: false }, 'undated', 'Date unrecorded'],
  [{ yearFounded: 1940, yearCeased: 1940, isActive: false }, 'single-year', '1940'],
  [{ yearFounded: null, yearCeased: null, isActive: true }, 'undated-active', 'Date unrecorded, still publishing'],
  [{ yearFounded: null, yearCeased: 1979, isActive: false }, 'undated-ceased', 'Date unrecorded, ceased 1979']
];
for (const [record, expectedCase, expectedText] of DATE_CASES) {
  assert.equal(dateCase(record), expectedCase);
  assert.equal(formatDates(record), expectedText);
}
// The woven model reports status through endState; both spellings agree.
assert.equal(formatDates({ yearFounded: 1990, yearCeased: null, endState: 'still' }), '1990–present');
for (const publication of source) {
  const text = formatDates(publication);
  assert.ok(text.length > 0, `${publication.name} has date wording`);
  if (publication.yearFounded == null) assert.ok(text.startsWith('Date unrecorded'), `${publication.name} says its date is unrecorded`);
  else assert.ok(text.startsWith(String(publication.yearFounded)), `${publication.name} keeps its founding year`);
  if (publication.isActive && publication.yearFounded != null) assert.ok(text.endsWith('present'));
  assert.ok(!text.includes('undefined') && !text.includes('null'));
}

assert.equal(recordsLabel({ evidence: [{ rightsStatus: 'publishable' }] }), '1 record');
assert.equal(recordsLabel({ evidence: [{}, {}, {}] }), '3 records');
assert.equal(recordsLabel({ evidence: [] }), 'No records');
assert.equal(recordsLabel({}), 'No records');
const totalRecords = source.reduce((sum, p) => sum + recordCount(p), 0);
assert.equal(totalRecords, source.reduce((sum, p) => sum + (p.evidence || []).length, 0), 'the count follows the archive policy');
const cleared = source.filter((p) => clearedRecordCount(p) > 0).length;
assert.equal(cleared, 39, '39 publications hold a cleared record');

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------

const stopsById = new Map(model.tours.map((tour) => [tour.id, tour.stops.map((s) => s.eventId)]));
const newState = () => createHallState({ stopsForStory: (id) => stopsById.get(id) || [] });

{
  const store = newState();
  const seen = [];
  const off = store.subscribe((s) => seen.push(s.mode));
  store.selectPublication(9);
  assert.equal(store.getState().mode, 'publication');
  assert.equal(store.getState().selectedPublicationId, 9);
  // A repeated command changes nothing and stacks nothing.
  const before = store.getState();
  store.selectPublication(9);
  assert.equal(store.getState(), before, 'selecting the open sheet again is not a new state');
  store.selectPublication(16);
  assert.equal(store.getState().returnStack.length, 1, 'moving between sheets does not stack a second way back');
  store.close();
  assert.equal(store.getState().mode, 'browse');
  assert.equal(store.getState().returnStack.length, 0);
  off();
  assert.ok(seen.length >= 3);
  const quiet = seen.length;
  store.selectPublication(9);
  assert.equal(seen.length, quiet, 'unsubscribed listeners stop hearing');
}

{
  // Nested return contexts: story from a publication, clipping from that story.
  const store = newState();
  store.moveTo({ kind: 'section', id: '1930s' });
  store.selectPublication(9);
  store.openStory('story-006');
  assert.equal(store.getState().mode, 'story');
  assert.equal(store.getState().stopId, stopsById.get('story-006')[0]);
  store.nextStop();
  const secondStop = stopsById.get('story-006')[1];
  assert.equal(store.getState().stopId, secondStop);
  store.openClipping({ webPath: 'images/evidence/x.jpg', citation: 'A citation.' });
  assert.equal(store.getState().mode, 'clipping');
  store.close();
  assert.equal(store.getState().mode, 'story', 'closing the clipping returns to the story');
  assert.equal(store.getState().stopId, secondStop, 'and to the stop it was opened from');
  store.close();
  assert.equal(store.getState().mode, 'publication', 'closing the story returns to the publication');
  assert.equal(store.getState().selectedPublicationId, 9);
  store.close();
  assert.equal(store.getState().mode, 'browse');
  assert.equal(store.getState().anchor.id, '1930s', 'browse returns to the rail anchor it left');
  assert.equal(store.getState().storyId, null);
}

{
  // A sheet focus opened from a story carries no story state, and closing it
  // gives the story back.
  const store = newState();
  const stops = stopsById.get('story-006');
  store.openStory('story-006', stops[2]);
  store.selectPublication(16);
  assert.equal(store.getState().mode, 'publication');
  assert.equal(store.getState().storyId, null, 'a publication focus clears the story');
  assert.equal(store.getState().stopId, null, 'and its stop');
  assert.equal(links.format(store.getState()), '?view=hall&pub=16', 'so a copied link is a publication link');
  store.close();
  assert.equal(store.getState().mode, 'story');
  assert.equal(store.getState().storyId, 'story-006', 'closing restores the story');
  assert.equal(store.getState().stopId, stops[2], 'and the stop it was left at');
}

{
  // Stale asynchronous work is rejected, and a close during a pending load is safe.
  const store = newState();
  store.openStory('story-005');
  const token = store.generation();
  assert.equal(store.isCurrent(token), true);
  store.nextStop();
  assert.equal(store.isCurrent(token), false, 'a stop change rejects work started before it');
  const midToken = store.generation();
  store.close();
  assert.equal(store.getState().mode, 'browse');
  assert.equal(store.isCurrent(midToken), false, 'closing during a pending load rejects that work too');
  store.openStory('story-005');
  assert.equal(store.getState().mode, 'story');
}

{
  const store = newState();
  const stops = stopsById.get('story-006');
  store.openStory('story-006', stops[3]);
  assert.equal(store.getState().stopId, stops[3], 'a stop link opens that stop');
  store.openStory('story-006', 'evt-nope');
  assert.equal(store.getState().stopId, stops[0], 'an unknown stop opens the first stop');
  assert.equal(store.getState().unknownStop, true, 'and says so');
  store.gotoStop(stops[stops.length - 1]);
  const atEnd = store.generation();
  store.nextStop();
  assert.equal(store.generation(), atEnd, 'the last stop does not wrap');
  store.gotoStop(stops[0]);
  const atStart = store.generation();
  store.prevStop();
  assert.equal(store.generation(), atStart, 'the first stop does not wrap');
  store.gotoStop('evt-nope');
  assert.equal(store.getState().stopId, stops[0], 'an unknown stop request is ignored');
  // Rail movement is suspended while a story is open.
  store.moveTo({ kind: 'section', id: '1950s' });
  assert.notEqual(store.getState().anchor.id, '1950s');
}

{
  const store = newState();
  const generationBefore = store.generation();
  store.setFilters({ city: 'Newark' });
  assert.equal(store.getState().filters.city, 'Newark');
  assert.equal(store.generation(), generationBefore, 'a filter change does not reject in-flight work');
  store.setFilters({ city: 'Newark' });
  assert.equal(store.generation(), generationBefore);
  store.setView('timeline');
  assert.equal(store.generation(), generationBefore + 1, 'a view change rejects in-flight work');
  store.setView('nowhere');
  assert.equal(store.getState().view, 'timeline', 'an unknown view is ignored');
  store.setTier('simplified');
  store.setMotion('reduced');
  store.setLoading(true);
  store.setRendererFailed(true);
  const s = store.getState();
  assert.equal(s.tier, 'simplified');
  assert.equal(s.motion, 'reduced');
  assert.equal(s.loading, true);
  assert.equal(s.rendererFailed, true);
  assert.equal(s.view, 'timeline', 'a renderer failure does not discard the requested view');
  store.close();
  assert.equal(store.getState().mode, 'browse', 'closing from browse is harmless');
}

// ---------------------------------------------------------------------------
// Quality tiers
// ---------------------------------------------------------------------------

{
  const { createTiers, SAMPLE_WINDOW, TIERS } = await import('../docs/js/hall/tiers.js');
  assert.deepEqual(Object.keys(TIERS), ['standard', 'simplified'], 'two named tiers, and no third');
  assert.ok(TIERS.simplified.pixelRatio < TIERS.standard.pixelRatio, 'simplified lowers the device pixel ratio');
  assert.equal(TIERS.simplified.fill, false, 'simplified drops the optional fill light');
  assert.equal(TIERS.simplified.bend, false, 'simplified drops the page bend');
  for (const settings of Object.values(TIERS)) {
    assert.ok(!('shadows' in settings), 'the hall has no shadows, so they are not in the ladder');
  }

  const applied = [];
  const said = [];
  let click = null;
  const toggle = { setAttribute() {} };
  const note = { textContent: '' };
  const tiers = createTiers({
    toggle,
    note,
    listen: (target, type, handler) => { click = handler; },
    announce: (text) => said.push(text),
    apply: (settings, tier) => applied.push(tier)
  });
  const feed = (ms, windows) => {
    for (let i = 0; i < SAMPLE_WINDOW * windows; i += 1) tiers.sample(ms);
  };

  assert.equal(tiers.tier, 'standard', 'the hall starts at the standard tier');
  feed(25, 1);
  assert.equal(tiers.tier, 'standard', 'one slow window is not enough to change the tier');
  feed(25, 1);
  assert.equal(tiers.tier, 'simplified', 'two sustained slow windows fall back');
  assert.deepEqual(applied, ['simplified']);
  assert.ok(said.some((text) => text.includes('Simplified view')), 'the change is announced');
  assert.ok(note.textContent.startsWith('Simplified view'), 'and explained in the control');

  feed(10, 3);
  assert.equal(tiers.tier, 'simplified', 'three fast windows are not enough to go back');
  feed(10, 1);
  assert.equal(tiers.tier, 'standard', 'four sustained fast windows restore the standard tier');

  // A window between the two thresholds clears both counts, so a hall hovering
  // around the boundary never oscillates.
  feed(25, 1);
  feed(16, 1);
  feed(25, 1);
  assert.equal(tiers.tier, 'standard', 'a middling window resets the count toward simplified');

  click();
  assert.equal(tiers.tier, 'simplified', 'the control pins the other tier');
  assert.equal(tiers.pinned, 'simplified');
  assert.ok(note.textContent.includes('You chose this view.'));
  feed(10, 10);
  assert.equal(tiers.tier, 'simplified', 'measurement never overrides a pinned choice');
  click();
  assert.equal(tiers.tier, 'standard', 'and the visitor can pin the standard tier back');
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

const firstStory = model.tours[0];
const firstStop = firstStory.stops[0].eventId;

const routes = [
  ['?view=3d&pub=9', { view: 'hall', kind: 'publication', id: 9 }],
  ['?view=hall&pub=9', { view: 'hall', kind: 'publication', id: 9 }],
  ['?view=woven&pub=9', { view: 'hall', kind: 'publication', id: 9 }],
  ['?pub=9', { view: 'hall', kind: 'publication', id: 9 }],
  ['?view=timeline', { view: 'timeline', kind: 'none', id: null }],
  [`?story=${firstStory.id}`, { view: 'hall', kind: 'story', id: firstStory.id }],
  [`?story=${firstStory.id}&stop=${firstStop}`, { view: 'hall', kind: 'story', id: firstStory.id }],
  ['?decade=1930s', { view: 'hall', kind: 'decade', id: '1930s' }],
  ['?decade=undated', { view: 'hall', kind: 'decade', id: 'undated' }]
];
for (const [search, expected] of routes) {
  const parsed = links.parse(search);
  const resolved = links.resolveView(parsed, {});
  assert.equal(resolved, expected.view, `${search} opens the ${expected.view}`);
  assert.equal(parsed.target.kind, expected.kind, `${search} targets a ${expected.kind}`);
  assert.equal(parsed.target.id, expected.id, `${search} targets ${expected.id}`);
  const checked = links.validate(parsed, model, layout);
  assert.deepEqual(checked.issues, [], `${search} is a valid route`);
}
assert.equal(links.parse(`?story=${firstStory.id}&stop=${firstStop}`).target.stop, firstStop);

// Forced text overrides every visual mode and keeps the requested record.
for (const search of ['?twin=1&pub=9', '?nogl=1&pub=9']) {
  const parsed = links.parse(search);
  assert.equal(parsed.forcedText, true);
  assert.equal(links.resolveView(parsed, {}), 'text');
  assert.equal(parsed.target.kind, 'publication');
  assert.equal(parsed.target.id, 9);
}
assert.equal(links.parse('?nogl=1&view=hall').forcedText, true);
assert.equal(links.resolveView(links.parse('?nogl=1&view=hall'), {}), 'text');
assert.equal(links.parse('?ghost=1').ghost, true);

// The flat timeline is the fallback when the hall cannot be drawn.
assert.equal(links.resolveView(links.parse(`?story=${firstStory.id}`), { canRenderHall: false }), 'timeline');
assert.equal(links.resolveView(links.parse(''), { sessionView: 'timeline' }), 'timeline', 'the visitor keeps the view they chose');
assert.equal(links.resolveView(links.parse(''), {}), 'hall', 'the hall is the default');

// Precedence: story, then publication, then decade.
const conflict = links.parse(`?story=${firstStory.id}&pub=9&decade=1930s`);
assert.equal(conflict.target.kind, 'story');
assert.equal(links.parse('?pub=9&decade=1930s').target.kind, 'publication');
assert.equal(links.parse('?decade=1930s').target.kind, 'decade');

// Invalid values are reported, never thrown.
const unknownPub = links.validate(links.parse('?pub=99999'), model, layout);
assert.equal(unknownPub.target.kind, 'none');
assert.equal(unknownPub.issues[0].reason, 'unknown-publication');
const unknownStory = links.validate(links.parse('?story=story-999'), model, layout);
assert.equal(unknownStory.issues[0].reason, 'unknown-story');
const unknownStop = links.validate(links.parse(`?story=${firstStory.id}&stop=evt-nope`), model, layout);
assert.equal(unknownStop.target.kind, 'story');
assert.equal(unknownStop.target.stop, firstStop, 'an unknown stop falls back to the first stop');
assert.equal(unknownStop.issues[0].reason, 'unknown-stop');
assert.equal(links.parse('?pub=abc').issues[0].reason, 'malformed-id');
assert.equal(links.parse('?decade=1800s').issues[0].reason, 'malformed-decade');
assert.equal(links.parse('?decade=nineteen-thirties').issues[0].reason, 'malformed-decade');
assert.equal(links.parse('?view=banana').issues[0].reason, 'unknown-view');
assert.equal(links.parse('?stop=evt-001').issues[0].reason, 'stop-without-story');
assert.equal(links.validate(links.parse('?decade=1930s'), model, layout).target.id, '1930s');

// Copy link round trips, and never carries a camera.
const formatted = [
  [{ view: 'hall', selectedPublicationId: 9 }, '?view=hall&pub=9'],
  [{ view: 'hall', storyId: firstStory.id, stopId: firstStop }, `?view=hall&story=${firstStory.id}&stop=${firstStop}`],
  [{ view: 'hall', storyId: firstStory.id }, `?view=hall&story=${firstStory.id}`],
  [{ view: 'hall', anchor: { kind: 'section', id: '1930s' } }, '?view=hall&decade=1930s'],
  [{ view: 'timeline' }, '?view=timeline']
];
for (const [state, expected] of formatted) {
  assert.equal(links.format(state), expected);
  const back = links.parse(expected);
  assert.equal(links.format({
    view: back.view,
    selectedPublicationId: back.pub,
    storyId: back.story,
    stopId: back.stop,
    anchor: back.decade ? { kind: 'section', id: back.decade } : null
  }), expected, `${expected} round trips`);
  assert.ok(!expected.includes('x=') && !expected.includes('z='), 'no camera numbers in a shared link');
}
// A story link wins over a publication in the same state, matching the parser.
assert.equal(links.format({ view: 'hall', selectedPublicationId: 9, storyId: firstStory.id }), `?view=hall&story=${firstStory.id}`);

// The deep-link list guide.js reads must include the two new parameters.
assert.deepEqual(links.DEEP_LINK_PARAMS, ['pub', 'story', 'stop', 'decade', 'ghost', 'nogl', 'twin']);
for (const search of ['?pub=9', '?story=story-001', '?stop=evt-001', '?decade=1930s', '?ghost=1', '?nogl=1', '?twin=1']) {
  assert.equal(links.hasDeepLink(search), true, `${search} is a deep link`);
}
assert.equal(links.hasDeepLink('?view=hall'), false, 'a bare view is not a deep link');

console.log(`PASS: ${layout.slots.length} publication slots, ${layout.bookSlots.length} volumes, ${layout.sections.length} sections, no overlaps, date wording, state machine, filtered stepping, quality tiers, and every route`);
