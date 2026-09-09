// History hall — the archive as the hall reads it.
//
// One place turns the loaded model into what a sheet, a plate, a cover, and a
// page actually show. It holds no DOM and no drawing code, so the wording it
// produces can be read and checked on its own.
//
// The woven model calls a publication record a thread. That word stops here.

import { formatDates, recordsLabel, storyEraNote } from './layout.js';
import { eraColor } from '../woven/records.js';

/** The first sentence of a record's own notes, used as an exhibit label. */
export function firstSentence(text) {
  const clean = String(text || '').trim();
  if (!clean) return '';
  const match = /^(.+?[.!?])(\s|$)/.exec(clean);
  const sentence = match ? match[1] : clean;
  return sentence.length > 220 ? `${sentence.slice(0, 217)}…` : sentence;
}

/** What each publication's sheet and plate show. */
export function buildPublicationViews(model, assets) {
  const views = new Map();
  for (const publication of model.threads) {
    const copy = assets.wallCopyForPublication(publication.id);
    views.set(publication.id, {
      id: publication.id,
      name: publication.name,
      city: publication.city,
      dateText: formatDates(publication),
      note: firstSentence(publication.historicalNotes),
      eraColor: eraColor(publication),
      recordsLabel: recordsLabel(publication),
      yearFounded: publication.yearFounded ?? null,
      active: publication.endState === 'still',
      wallPath: copy ? copy.wallPath : null,
      rightsStatus: copy ? copy.status : null,
      citation: copy ? copy.citation : ''
    });
  }
  return views;
}

/** What each guided story's volume, spread, and reader show. */
export function buildStoryViews(model, assets) {
  const views = new Map();
  for (const tour of model.tours) {
    const stops = tour.stops.map((stop, index) => buildStopView(model, assets, tour, stop, index));
    views.set(tour.id, {
      id: tour.id,
      title: tour.title,
      era: tour.era,
      note: storyEraNote(tour),
      summary: tour.thread,
      thinlySourced: tour.strength === 'weak',
      eraColor: eraColor({ bandKey: firstBand(tour) }),
      stopCount: stops.length,
      stops
    });
  }
  return views;
}

function firstBand(tour) {
  const first = tour.stops.find((stop) => stop.band);
  return first ? first.band : 'U';
}

export function buildStopView(model, assets, tour, stop, index) {
  const clip = stop.clipping;
  const copy = clip ? assets.wallCopyForPath(clip.webPath) : null;
  const citations = clip && clip.citation
    ? [clip.citation]
    : [...new Set((stop.event.sourceFiles || []).map((file) => model.citeSource(file)).filter(Boolean))];
  const rights = (stop.event.sourceFiles || []).map((file) => model.sourceRights(file));
  let rightsNote = '';
  if (clip && clip.rightsStatus === 'crop_first') rightsNote = 'Cropped detail. Full page not reproduced.';
  else if (clip && clip.rightsStatus === 'publishable_with_credit') rightsNote = `Required credit: ${clip.citation}`;
  else if (!clip && rights.length && rights.every((value) => value === 'metadata_only')) {
    rightsNote = 'The source is a printed bibliography. We quote it; we do not reproduce the page.';
  }
  const publications = (stop.event.publicationIds || [])
    .map((id) => model.byId.get(id))
    .filter(Boolean)
    .map((publication) => ({ id: publication.id, name: publication.name }));
  const label = `Stop ${index + 1} of ${tour.stops.length}`;
  return {
    index,
    key: stop.eventId,
    title: stop.event.title,
    date: stop.dateLabel,
    description: stop.event.description,
    confidence: stop.confidence,
    citations,
    rightsNote,
    publications,
    clipping: clip ? {
      path: copy ? copy.wallPath : clip.webPath,
      fullPath: clip.webPath,
      alt: clip.altText,
      caption: clip.caption,
      citation: clip.citation,
      rightsStatus: clip.rightsStatus,
      rightsNote
    } : null,
    // The left page carries the cleared clipping. A stop without one gets a
    // deliberate text page, never invented historical paper.
    left: clip ? {
      kind: 'clipping',
      path: copy ? copy.wallPath : clip.webPath,
      caption: clip.caption,
      rightsStatus: clip.rightsStatus,
      accent: '#e2662b'
    } : {
      kind: 'text',
      date: stop.dateLabel,
      title: '',
      note: 'No clipping is cleared for display at this stop. The source is cited in the reader.',
      footer: citations[0] || ''
    },
    right: { kind: 'text', date: stop.dateLabel, title: stop.event.title, note: '', footer: label }
  };
}
