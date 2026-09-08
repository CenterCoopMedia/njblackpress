// Historical notes data adapter. It preserves the archive records and adds
// only the fields required by the time map and its text views.

import {
  buildClusters,
  eraColorFor,
  YEAR_MAX,
  Y_NOW,
  yearToY
} from './geo.js';

export const CLEARED = new Set([
  'publishable',
  'publishable_with_credit',
  'crop_first'
]);

const SOURCE_NAME = /^(.+?)_(\d{4}(?:-\d{2}){0,2})(?:_p(\d+[a-z]?))?/i;
const PUBLIC_IMAGE_PATH = /^images\/evidence\/[A-Za-z0-9._~!$&'()*+,;=@/-]+$/;

async function readJSON(url, fallback) {
  const optional = arguments.length > 1;
  try {
    const response = await fetch(url);
    if (!response || response.ok === false) {
      throw new Error(`Could not load ${url}`);
    }
    return await response.json();
  } catch (error) {
    if (optional) return fallback;
    throw error;
  }
}

function recordsFrom(document, key) {
  if (Array.isArray(document)) return document;
  return Array.isArray(document?.[key]) ? document[key] : [];
}

/** Load the six archive documents used by the time map. */
export async function loadModel() {
  const [publicationDocument, eventDocument, storyDocument, clippingDocument, mapDocument, outlineDocument] = await Promise.all([
    readJSON('data/publications.json'),
    readJSON('data/events.json', { events: [] }),
    readJSON('data/stories.json', { stories: [] }),
    readJSON('data/clippings.json', { clippings: [] }),
    readJSON('data/map-publications.json', null),
    readJSON('data/nj-outline.json', null)
  ]);

  const rawPublications = recordsFrom(publicationDocument, 'publications');
  const events = recordsFrom(eventDocument, 'events');
  const rawStories = recordsFrom(storyDocument, 'stories');
  const rawClippings = recordsFrom(clippingDocument, 'clippings');
  const publications = rawPublications.map(normalisePublication);

  const clusters = buildClusters(publications, mapDocument);
  const byId = new Map(publications.map((publication) => [publication.id, publication]));

  const clipIndex = buildClipIndex(rawClippings);
  const clipsByPub = clipIndex.clipsByPub;
  const citeSource = (file) => citationFor(file, clipIndex.citationByStem);
  const sourceRights = (file) => clipIndex.rightsByStem.get(fileStem(file)) || null;
  const eventById = new Map(events.map((event) => [event.id, event]));
  const stories = rawStories.map((story) => buildStory(story, eventById, byId, clipIndex.byStem));
  const marks = events.map((event) => buildMark(event, byId));

  return {
    publications,
    mapAvailable: Array.isArray(mapDocument?.locations) && mapDocument.locations.length > 0,
    byId,
    marks,
    stories,
    events,
    clusters,
    counts: {
      total: publications.length,
      active: publications.filter((publication) => publication.active).length,
      stories: stories.length,
      clippings: rawClippings.length,
      unrecordedYears: publications.filter((publication) => !publication.startKnown || !publication.endKnown).length
    },
    clipsByPub,
    citeSource,
    sourceRights,
    outline: validOutline(outlineDocument)
  };
}

/** Format a publication's recorded lifespan without filling missing years. */
export function publicationYears(publication) {
  if (publication?.yearFounded == null) {
    const end = publication?.active
      ? 'still publishing'
      : publication?.yearCeased != null
        ? `ceased ${publication.yearCeased}`
        : 'end date unrecorded';
    return `Founding year unrecorded · ${end}`;
  }
  if (publication.active) return `${publication.yearFounded}–present`;
  if (publication.yearCeased != null) return `${publication.yearFounded}–${publication.yearCeased}`;
  return `${publication.yearFounded} · end date unrecorded`;
}

/**
 * Return whether a title is documented as publishing in the requested year.
 * Missing founding or cessation years never create an inferred interval.
 */
export function publishingAt(publication, year) {
  if (!publication || !publication.startKnown) return false;
  const value = Number(year);
  const start = Number(publication.yearFounded);
  if (!Number.isFinite(value) || !Number.isFinite(start) || value < start || value > YEAR_MAX) return false;
  if (publication.active) return true;
  if (!publication.endKnown) return false;
  return value <= Number(publication.yearCeased);
}

/** Escape archive text before it enters a generated HTML fragment. */
export function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Accept only the site's local public evidence paths. External source URLs
 * remain links in their source records and are not image paths for the scene.
 */
export function safeURL(value) {
  let path = String(value ?? '').trim();
  if (!path || path.includes('\\') || /[\u0000-\u001f\u007f]/.test(path)) return '';
  path = path.replace(/^\.\//, '').replace(/^\//, '');
  if (!PUBLIC_IMAGE_PATH.test(path)) return '';
  if (path.split('/').some((segment) => !segment || segment === '.' || segment === '..')) return '';
  return path;
}

/** Normalize a clipping record without exposing its source filesystem path. */
export function normaliseClip(clipping) {
  const source = clipping || {};
  const status = String(source.status || source.rightsStatus || 'metadata_only');
  return {
    webPath: safeURL(source.webPath),
    citation: String(source.citation || ''),
    caption: String(source.caption || ''),
    alt: String(source.alt || source.altText || source.caption || ''),
    status,
    publicationIds: Array.isArray(source.publicationIds) ? source.publicationIds.map(normaliseId).filter((id) => id !== null) : [],
    width: source.width,
    height: source.height
  };
}

function normalisePublication(source) {
  const publication = source || {};
  const evidence = Array.isArray(publication.evidence) ? publication.evidence : [];
  const active = Boolean(publication.isActive);
  const startKnown = knownYear(publication.yearFounded);
  const endKnown = active || knownYear(publication.yearCeased);
  const endState = active ? 'still' : publication.yearCeased != null ? 'ceased' : 'unrecorded';
  const exactStartY = startKnown ? yearToY(publication.yearFounded) : null;
  const exactEndY = active
    ? Y_NOW
    : knownYear(publication.yearCeased)
      ? yearToY(publication.yearCeased)
      : null;

  // Render anchors stay finite while the flags keep the uncertainty explicit.
  // The anchors are visual bounds, never replacement dates in the record.
  let startY = exactStartY;
  let endY = exactEndY;
  if (!startKnown && endKnown) startY = Math.max(0, endY - 1.2);
  if (startKnown && !endKnown) endY = startY + 1.2;
  if (!startKnown && !endKnown) startY = endY = 0;

  return {
    ...publication,
    evidence,
    active,
    endState,
    unsourced: !evidence.some(hasClearedEvidence),
    eraColor: eraColorFor(publication.yearFounded),
    startY,
    endY,
    startKnown,
    endKnown,
    x: null,
    z: null,
    clusterId: null
  };
}

function buildClipIndex(rawClippings) {
  const clipsByPub = new Map();
  const byStem = new Map();
  const citationByStem = new Map();
  const rightsByStem = new Map();

  for (const rawClipping of rawClippings) {
    const clip = normaliseClip(rawClipping);
    const stems = [...new Set([rawClipping?.sourcePath, rawClipping?.webPath].map(fileStem).filter(Boolean))];
    for (const stem of stems) {
      const stemClips = byStem.get(stem) || [];
      if (!stemClips.includes(clip)) stemClips.push(clip);
      byStem.set(stem, stemClips);
      if (clip.citation && !citationByStem.has(stem)) citationByStem.set(stem, clip.citation);
      const previous = rightsByStem.get(stem);
      if (!previous || (!CLEARED.has(previous) && CLEARED.has(clip.status))) rightsByStem.set(stem, clip.status);
    }
    for (const publicationId of clip.publicationIds) {
      const publicationClips = clipsByPub.get(publicationId) || [];
      if (!publicationClips.includes(clip)) publicationClips.push(clip);
      clipsByPub.set(publicationId, publicationClips);
    }
  }

  return { clipsByPub, byStem, citationByStem, rightsByStem };
}

function buildStory(source, eventById, byId, clipsByStem) {
  const story = source || {};
  const publicationIds = Array.isArray(story.publicationIds)
    ? story.publicationIds.map(normaliseId).filter((id) => id !== null)
    : [];
  const events = (Array.isArray(story.eventIds) ? story.eventIds : [])
    .map((eventId) => eventById.get(eventId))
    .filter(Boolean)
    .sort(compareEvents);

  return {
    ...story,
    summary: story.thread || '',
    publicationIds,
    stops: events.map((event) => {
      const publicationId = primaryPublicationId(event, publicationIds, byId);
      const publication = publicationId === null ? null : byId.get(publicationId);
      const date = fractionalDate(event.date);
      return {
        eventId: event.id,
        event,
        dateLabel: event.date == null ? '' : String(event.date),
        publicationId,
        position: positionFor(publication, date.value),
        clipping: clippingForEvent(event, clipsByStem)
      };
    })
  };
}

function buildMark(event, byId) {
  const publicationId = primaryPublicationId(event, [], byId);
  const publication = publicationId === null ? null : byId.get(publicationId);
  const date = fractionalDate(event.date);
  return {
    eventId: event.id,
    event,
    dateLabel: event.date == null ? '' : String(event.date),
    precision: date.precision,
    publicationId,
    position: positionFor(publication, date.value),
    confidence: event.confidence || 'high'
  };
}

function primaryPublicationId(event, preferredIds, byId) {
  const eventIds = Array.isArray(event?.publicationIds) ? event.publicationIds : [];
  const preferred = new Set(preferredIds || []);
  for (const value of eventIds) {
    const id = normaliseId(value);
    if (id !== null && preferred.has(id) && byId.has(id)) return id;
  }
  for (const value of eventIds) {
    const id = normaliseId(value);
    if (id !== null && byId.has(id)) return id;
  }
  return null;
}

function positionFor(publication, fractionalValue) {
  if (!publication || fractionalValue == null || !Number.isFinite(publication.x) || !Number.isFinite(publication.z)) return null;
  return {
    x: publication.x,
    y: Math.max(0, yearToY(fractionalValue)),
    z: publication.z
  };
}

function clippingForEvent(event, clipsByStem) {
  for (const source of Array.isArray(event?.sourceFiles) ? event.sourceFiles : []) {
    const candidates = clipsByStem.get(fileStem(source)) || [];
    const clipping = candidates.find((candidate) => CLEARED.has(candidate.status) && candidate.webPath);
    if (clipping) return clipping;
  }
  return null;
}

function compareEvents(left, right) {
  const leftDate = fractionalDate(left.date).value;
  const rightDate = fractionalDate(right.date).value;
  if (leftDate == null && rightDate != null) return 1;
  if (leftDate != null && rightDate == null) return -1;
  return (leftDate ?? 0) - (rightDate ?? 0) || String(left.id).localeCompare(String(right.id));
}

function fractionalDate(date) {
  const match = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/.exec(String(date ?? ''));
  if (!match) return { year: null, value: null, precision: 'none' };
  const year = Number(match[1]);
  const month = match[2] ? Number(match[2]) : null;
  const day = match[3] ? Number(match[3]) : null;
  return {
    year,
    value: year + ((month ?? 6.5) - 1) / 12 + ((day ?? 15) - 1) / 365,
    precision: day ? 'day' : month ? 'month' : 'year'
  };
}

function hasClearedEvidence(evidence) {
  return CLEARED.has(evidence?.rightsStatus || evidence?.status);
}

function knownYear(value) {
  if (value === null || value === undefined || String(value).trim() === '') return false;
  const year = Number(value);
  return Number.isInteger(year) && Number.isFinite(year);
}

function normaliseId(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null;
  const id = Number(value);
  return Number.isInteger(id) ? id : null;
}

function fileStem(path) {
  const value = String(path ?? '').split(/[?#]/, 1)[0];
  const basename = value.split('/').pop() || '';
  return basename.replace(/\.[a-z0-9]+$/i, '');
}

function citationFor(sourceFile, citationByStem) {
  const stem = fileStem(sourceFile);
  if (!stem) return '';
  const known = citationByStem.get(stem);
  if (known) return known;
  const match = SOURCE_NAME.exec(stem);
  if (!match) return '';
  const title = match[1].split('-')
    .map((word) => word ? word[0].toUpperCase() + word.slice(1) : word)
    .join(' ');
  return `${title}, ${match[2]}${match[3] ? `, p. ${match[3]}` : ''}.`;
}

function validOutline(outline) {
  if (!outline || !Array.isArray(outline.coordinates) || outline.coordinates.length < 3) return null;
  if (!outline.coordinates.every((point) => Array.isArray(point) && point.length >= 2
    && Number.isFinite(Number(point[0])) && Number.isFinite(Number(point[1])))) return null;
  return outline;
}
