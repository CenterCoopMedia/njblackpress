// Woven — data adapter. Fetches the four JSON files and derives the thread
// model, the event index, and the 13 tours. No visual code here.

import {
  BAND_DEFS, bandKeyFor, buildLayout, fractionalYear, seededRandom, x, xClamped
} from './layout.js';

const CLEARED = new Set(['publishable', 'publishable_with_credit', 'crop_first']);

// Era dye, band A (oldest, wood-toned) through band G (linen). Band U is thread-400.
const ERA_DYE = ['#a89179', '#b09a80', '#bda98e', '#c9b89e', '#d8cbb2', '#e8dfca', '#f3eee2'];
const DYE_U = '#a89c85';

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}

async function getJSON(url, fallback) {
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(r.status);
    return await r.json();
  } catch (e) {
    if (fallback === undefined) throw e;
    return fallback;
  }
}

export async function loadModel() {
  const [pubDoc, evDoc, stDoc, clDoc] = await Promise.all([
    getJSON('data/publications.json'),
    getJSON('data/events.json', { events: [] }),
    getJSON('data/stories.json', { stories: [] }),
    getJSON('data/clippings.json', { clippings: [] })
  ]);

  const pubs = pubDoc.publications || pubDoc;
  const events = evDoc.events || [];
  const stories = stDoc.stories || [];
  const clippings = clDoc.clippings || [];

  const threads = pubs.map(buildThread);
  const layout = buildLayout(threads);
  threads.sort((a, b) => a.id - b.id);

  // The merged weft geometry draws solid threads first, ghosts second, so the
  // ghost pass can be a single drawRange split.
  const order = threads.slice().sort((a, b) => (a.ghost - b.ghost) || (a.id - b.id));
  order.forEach((t, i) => { t.threadIndex = i; });
  const solidCount = order.filter((t) => !t.ghost).length;

  const byId = new Map(threads.map((t) => [t.id, t]));
  const clipsByPub = new Map();
  for (const c of clippings) {
    for (const pid of c.publicationIds || []) {
      if (!clipsByPub.has(pid)) clipsByPub.set(pid, []);
      clipsByPub.get(pid).push(normaliseClip(c));
    }
  }

  // Citation index, keyed on the scan file stem. A source file name is not a
  // citation and must never reach the reader.
  const citationByStem = new Map();
  for (const c of clippings) {
    for (const path of [c.webPath, c.sourcePath]) {
      const stem = fileStem(path);
      if (stem && c.citation && !citationByStem.has(stem)) citationByStem.set(stem, c.citation);
    }
  }
  const citeSource = (file) => citationFor(file, citationByStem);

  const knots = buildKnots(events, byId, layout);
  const eventById = new Map(events.map((e) => [e.id, e]));
  const tours = stories.map((s) => buildTour(s, eventById, byId, clipsByPub));

  // Events attached to each thread, date-sorted, for the twin and the arrow keys.
  for (const k of knots) {
    if (!k.thread) continue;
    (k.thread.events || (k.thread.events = [])).push(k);
  }
  for (const t of threads) if (t.events) t.events.sort((a, b) => a.value - b.value);

  // Stories touching each thread.
  for (const tour of tours) {
    for (const id of tour.threadIds) {
      const t = byId.get(id);
      if (t) (t.stories || (t.stories = [])).push({ id: tour.id, title: tour.title });
    }
  }

  const counts = {
    total: threads.length,
    stillPublishing: threads.filter((t) => t.endState === 'still').length,
    ceased: threads.filter((t) => t.endState === 'ceased').length,
    ghost: threads.filter((t) => t.ghost).length,
    events: events.length,
    tours: tours.length,
    clippings: clippings.length
  };

  return {
    threads, order, solidCount, byId, layout, knots, tours, counts,
    bands: layout.bands, clipsByPub, rawEvents: events, citeSource
  };

  function buildThread(p) {
    const rnd = seededRandom(p.id * 2654435761);
    const evidence = p.evidence || [];
    const n = evidence.length;
    const yearFounded = p.yearFounded ?? null;
    const cleared = evidence.some((e) => CLEARED.has(e.rightsStatus));
    // One definition of "still publishing" across the whole site: the dataset's
    // own isActive flag, the same one the archive and the wiki count. Woven had
    // a second, narrower rule; two answers to one question is worse than either.
    const endState = p.isActive ? 'still' : 'ceased';

    const bandKey = bandKeyFor(yearFounded);
    const bandIdx = BAND_DEFS.findIndex((b) => b.key === bandKey);
    const dye = bandKey === 'U' ? DYE_U : ERA_DYE[Math.min(bandIdx, ERA_DYE.length - 1)];

    const endYear = p.yearCeased ?? 2026;
    return {
      id: p.id,
      name: p.name,
      alternateName: p.alternateName,
      city: p.city,
      publishers: p.publishers,
      yearFounded,
      yearCeased: p.yearCeased ?? null,
      startYear: yearFounded ?? 2026,
      endYear,
      frequency: p.frequency,
      format: p.format,
      medium: p.medium,
      languages: p.languages,
      primaryFocus: p.primaryFocus,
      missionStatement: p.missionStatement,
      historicalNotes: p.historicalNotes,
      targetAudience: p.targetAudience,
      keyStaff: p.keyStaff,
      archiveUrl: p.archiveUrl,
      websiteUrl: p.websiteUrl,
      evidence,
      evidenceCount: n,
      width: Math.min(0.1, Math.max(0.03, 0.03 + 0.026 * Math.log(1 + n))),
      ghost: !cleared,
      endState,
      bandKey,
      dye,
      dyeRgb: hexToRgb(dye),
      fraySeed: rnd(),
      unknownFounding: yearFounded === null,
      x0: x(yearFounded ?? 2020),
      x1: x(endYear)
    };
  }

  function normaliseClip(c) {
    // clippings.json ships `status` for `rightsStatus` and `alt` for `altText`.
    // The transcribed caption is the last resort, so we never render an empty
    // alt, and never render a panel with neither.
    const alt = c.altText || c.alt || c.caption || '';
    return {
      webPath: c.webPath || '',
      width: c.width,
      height: c.height,
      rightsStatus: c.rightsStatus || c.status || 'metadata_only',
      citation: c.citation || '',
      caption: c.caption || '',
      altText: alt,
      altFromCaption: !c.altText && !c.alt && !!c.caption,
      publicationIds: c.publicationIds || []
    };
  }
}

function buildKnots(events, byId, layout) {
  const out = [];
  for (const e of events) {
    const fy = fractionalYear(e.date);
    const rnd = seededRandom(hashString(e.id));
    const ids = (e.publicationIds || []).slice(0, 3);
    if (!ids.length) {
      out.push({
        eventId: e.id, event: e, thread: null, context: true,
        value: fy.value ?? 1880, precision: fy.precision,
        x: xClamped(fy.value ?? 1880), y: 0.35, roll: rnd() * Math.PI * 2,
        confidence: e.confidence || 'high'
      });
      continue;
    }
    for (const pid of ids) {
      const t = byId.get(pid);
      if (!t) continue;
      out.push({
        eventId: e.id, event: e, thread: t, context: false,
        value: fy.value ?? t.startYear, precision: fy.precision,
        x: xClamped(fy.value ?? t.startYear), y: t.y, roll: rnd() * Math.PI * 2,
        confidence: e.confidence || 'high'
      });
    }
  }
  out.forEach((k, i) => { k.index = i; });
  return out;
}

function buildTour(story, eventById, byId, clipsByPub) {
  const threadIds = (story.publicationIds || []).filter((id) => byId.has(id));
  const evs = (story.eventIds || [])
    .map((id) => eventById.get(id))
    .filter(Boolean)
    .map((e) => ({ e, fy: fractionalYear(e.date) }))
    .sort((a, b) => (a.fy.value ?? 0) - (b.fy.value ?? 0) || a.e.id.localeCompare(b.e.id));

  const stops = evs.map(({ e, fy }) => {
    let primary = (e.publicationIds || []).find((id) => threadIds.includes(id));
    if (primary === undefined) primary = (e.publicationIds || [])[0];
    const t = primary !== undefined ? byId.get(primary) : null;
    const meanY = threadIds.length
      ? threadIds.reduce((s, id) => s + byId.get(id).y, 0) / threadIds.length
      : 0;
    // A clipping only attaches to a stop when it is evidence *for that stop*.
    // clippings.json carries no eventId, so we match on the date in the
    // citation. A publication's clipping from 1893 must never illustrate a
    // 1901 event just because it belongs to the same title.
    const clip = t ? pickClipping(clipsByPub.get(t.id), e.date) : null;
    return {
      kind: 'event',
      eventId: e.id,
      event: e,
      dateLabel: e.date,
      precision: fy.precision,
      tx: xClamped(fy.value ?? 1880),
      ty: t ? t.y : meanY,
      distance: (e.publicationIds || []).filter((id) => threadIds.includes(id)).length > 1 ? 22 : 14,
      threadId: t ? t.id : null,
      band: t ? t.bandKey : null,
      clipping: clip || null,
      confidence: e.confidence || 'high'
    };
  });

  return {
    id: story.id,
    title: story.title,
    era: story.era,
    strength: story.strength || null,
    people: story.people || [],
    thread: story.thread,
    threadIds,
    stops
  };
}

function pickClipping(list, eventDate) {
  if (!list || !list.length) return null;
  const m = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/.exec(String(eventDate || ''));
  if (!m) return null;
  const iso = [m[1], m[2], m[3]].filter(Boolean).join('-');
  const usable = list.filter((c) => c.webPath && c.altText);
  // Exact date first, then same year. Never a loose title match.
  const exact = usable.find((c) => (c.citation + ' ' + c.webPath).includes(iso));
  if (exact) return exact;
  if (m[2]) {
    const ym = `${m[1]}-${m[2]}`;
    const monthMatch = usable.find((c) => (c.citation + ' ' + c.webPath).includes(ym));
    if (monthMatch) return monthMatch;
  }
  return usable.find((c) => (c.citation + ' ' + c.webPath).includes(m[1])) || null;
}

function fileStem(path) {
  return String(path || '').split('/').pop().replace(/\.[a-z0-9]+$/i, '');
}

// Scan files are named `<publication-slug>_<date>_p<page>_<slug>`. When
// clippings.json holds no citation for the same scan, read the publication, the
// date, and the page back out of the name the researcher recorded them in.
const SOURCE_NAME = /^(.+?)_(\d{4}(?:-\d{2}){0,2})(?:_p(\d+[a-z]?))?/i;

function citationFor(sourceFile, citationByStem) {
  const stem = fileStem(sourceFile);
  if (!stem) return '';
  const known = citationByStem.get(stem);
  if (known) return known;
  const m = SOURCE_NAME.exec(stem);
  if (!m) return '';
  const title = m[1].split('-')
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(' ');
  return `${title}, ${m[2]}${m[3] ? `, p. ${m[3]}` : ''}.`;
}

function hashString(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
