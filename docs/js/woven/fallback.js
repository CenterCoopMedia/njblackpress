// Woven — the no-GPU route. three.js is never fetched on this path.

import { promoteTwin, announce, syncTwin } from './twin.js';

const NO_WEBGL = 'Your browser cannot draw the weave, so here it is as a list.';
const CONTEXT_LOST = 'The drawing stopped. Here is the same archive as a list.';

export function startFallback(model, reason) {
  promoteTwin(reason === 'lost' ? CONTEXT_LOST : NO_WEBGL);

  // Everything below keeps working with no canvas: tours read as text, the
  // ghost list is already in the DOM, panels open as disclosures.
  const api = {
    open(pubId) { openInTwin(pubId); },
    playStory(storyId) { playInTwin(model, storyId); },
    showGhost() { showGhostInTwin(model); },
    exit() { syncTwin({}); }
  };
  window.njbpWoven = api;

  const params = new URLSearchParams(location.search);
  if (params.get('pub')) openInTwin(+params.get('pub'));
  if (params.get('story')) playInTwin(model, params.get('story'));
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

function playInTwin(model, storyId) {
  const li = document.getElementById(`tour-${storyId}`);
  if (!li) return;
  const details = li.querySelector('details');
  if (details) details.open = true;
  li.scrollIntoView({ block: 'start' });
  const tour = model.tours.find((t) => t.id === storyId);
  if (tour) {
    syncTwin({ tourId: storyId, stopIndex: 0 });
    announce(`Guided thread: ${tour.title}. ${tour.stops.length} stops, ${tour.era}.`);
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
  announce(`${model.counts.ghost} titles survive only as a catalog entry. Their names follow.`);
}
