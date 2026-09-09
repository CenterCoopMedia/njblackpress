// Woven — the no-GPU route. three.js is never fetched on this path.

import { promoteTwin, announce, syncTwin } from './twin.js';

const NO_WEBGL = 'Your browser cannot draw the timeline, so here it is as a list.';
const CONTEXT_LOST = 'The drawing stopped. Here is the same archive as a list, with what you were reading.';
const ASKED_FOR_TEXT = 'The complete archive, as a list. No drawing was loaded.';

const MESSAGES = { lost: CONTEXT_LOST, twin: ASKED_FOR_TEXT, nogl: NO_WEBGL };

/**
 * Promote the text archive and open whatever the visitor was reading in it.
 *
 * @param {object} model the loaded archive
 * @param {'nogl'|'twin'|'lost'} reason why the text archive is in front
 * @param {{pubId?: number, storyId?: string, stopId?: string, filters?: string[]}} [carry]
 *   state to preserve across the change. A lost context must not cost the
 *   visitor the record, the story, or the stop they were on.
 */
export function startFallback(model, reason, carry = {}) {
  const kept = (carry.filters || []).filter(Boolean);
  const filterLine = kept.length
    ? ` Your filters (${kept.join(', ')}) do not apply to this list, which holds every publication.`
    : '';
  promoteTwin((MESSAGES[reason] || NO_WEBGL) + filterLine);

  // Everything below keeps working with no canvas: tours read as text, the
  // ghost list is already in the DOM, panels open as disclosures.
  const api = {
    open(pubId) { openInTwin(pubId); },
    playStory(storyId, stopId) { playInTwin(model, storyId, stopId); },
    showGhost() { showGhostInTwin(model); },
    exit() { syncTwin({}); }
  };
  window.njbpWoven = api;

  // What the visitor was reading comes first; the link they arrived on is read
  // only when there is nothing to carry over.
  const params = new URLSearchParams(location.search);
  const pubId = carry.pubId ?? (params.get('pub') ? +params.get('pub') : null);
  const storyId = carry.storyId ?? params.get('story');
  const stopId = carry.stopId ?? params.get('stop');
  if (storyId) playInTwin(model, storyId, stopId);
  else if (pubId != null) openInTwin(pubId);
  if (params.get('ghost') === '1') showGhostInTwin(model);
  return api;
}

function openInTwin(pubId) {
  const btn = document.querySelector(`#thread-${pubId} .t-open`);
  const detail = document.getElementById(`thread-${pubId}-detail`);
  if (!btn || !detail) return;
  btn.setAttribute('aria-expanded', 'true');
  detail.hidden = false;
  btn.focus();
  syncTwin({ selectedId: pubId, scrollTwin: true });
}

function playInTwin(model, storyId, stopId) {
  const li = document.getElementById(`tour-${storyId}`);
  if (!li) return;
  const details = li.querySelector('details');
  if (details) details.open = true;
  li.scrollIntoView({ block: 'start' });
  const tour = model.tours.find((t) => t.id === storyId);
  const index = tour && stopId ? tour.stops.findIndex((stop) => stop.eventId === stopId) : 0;
  const stopIndex = index > 0 ? index : 0;
  if (tour) {
    syncTwin({ tourId: storyId, stopIndex });
    // The stop the visitor was on is marked in the list, so a lost drawing does
    // not cost them their place in the story.
    const stop = document.getElementById(`tour-${storyId}-stop-${tour.stops[stopIndex]?.eventId}`);
    if (stop) stop.setAttribute('aria-current', 'step');
    announce(`Guided story: ${tour.title}. ${tour.stops.length} stops, ${tour.era}. Stop ${stopIndex + 1}.`);
  }
  const summary = li.querySelector('summary');
  if (summary) summary.focus();
}

function showGhostInTwin(model) {
  const section = document.getElementById('woven-twin-ghost');
  if (!section) return;
  section.scrollIntoView({ block: 'start' });
  const h = document.getElementById('ghost-h');
  if (h) { h.setAttribute('tabindex', '-1'); h.focus(); }
  announce(`${model.counts.ghost} titles have no cleared evidence in this archive. Their names follow.`);
}
