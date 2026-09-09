import { matchesFilters, publicationYears, eraColor } from './records.js';
import { announce } from './twin.js';

// A real, keyboard-accessible index alongside either drawing. No second fetch,
// no synthetic stories, and no canvas-only route to a publication.
export function mountExplorer(app, { highlight, filter, focusEra, open }) {
  const model = app.model;
  if (new URLSearchParams(location.search).get('twin') === '1') {
    document.getElementById('woven-list-disclosure').open = true;
  }
  const root = document.getElementById('woven-browser');
  const city = document.getElementById('woven-city');
  const evidence = document.getElementById('woven-evidence');
  const list = document.getElementById('woven-publications');
  const status = document.getElementById('woven-browser-status');
  const clear = document.getElementById('woven-clear-filters');
  const panel = document.getElementById('woven-panel');
  const all = model.threads.slice().sort((a, b) => (a.yearFounded ?? Infinity) - (b.yearFounded ?? Infinity) || a.name.localeCompare(b.name));
  const cities = [...new Set(all.map((t) => String(t.city || '')).filter(Boolean))].sort((a, b) => a.localeCompare(b));
  cities.forEach((name) => city.add(new Option(name, name)));
  let current = all;
  let era = 'all';
  // A record reached by a deep link or by search can sit outside the filters the
  // visitor set. It is revealed for as long as it is selected, and the filters
  // are left exactly as they were: changing someone's filters without being
  // asked is worse than showing one extra row.
  let revealed = null;
  const eraChoices = document.getElementById('woven-era-choices');
  for (const band of [{ key: 'all', count: all.length }, ...model.bands.filter((b) => b.count)]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'woven-era-choice';
    button.dataset.era = band.key;
    if (band.threads?.length) button.style.setProperty('--thread-color', eraColor(band.threads[0]));
    button.append(band.key === 'all' ? 'All years' : band.from == null ? 'Undated' : `${band.from}–${band.to}`);
    const count = document.createElement('span');
    count.textContent = band.count;
    button.append(count);
    button.addEventListener('click', () => {
      if (app.tour?.isPlaying) app.tour.exit();
      if (app.ghost?.isPlaying) app.ghost.exit();
      era = band.key;
      changed();
      focusEra(era);
    });
    eraChoices.append(button);
  }

  function render() {
    const selection = { city: city.value, evidence: evidence.value };
    const matched = all.filter((thread) => matchesFilters(thread, selection) && (era === 'all' || thread.bandKey === era));
    const filtered = era !== 'all' || !!city.value || evidence.value !== 'all';
    const outside = revealed != null && filtered && !matched.some((thread) => thread.id === revealed);
    const extra = outside ? all.filter((thread) => thread.id === revealed) : [];
    current = extra.length ? [...extra, ...matched] : matched;
    const fragment = document.createDocumentFragment();
    current.forEach((thread) => {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'woven-publication';
      button.dataset.pub = String(thread.id);
      button.style.setProperty('--thread-color', eraColor(thread));
      button.setAttribute('aria-pressed', String(app.state.selectedId === thread.id));
      if (extra.length && thread.id === revealed) button.dataset.revealed = 'true';
      const name = document.createElement('strong');
      name.textContent = thread.name;
      const meta = document.createElement('span');
      meta.textContent = `${thread.city || 'City unrecorded'} · ${publicationYears(thread)}`;
      button.append(name, meta);
      if (extra.length && thread.id === revealed) {
        const note = document.createElement('span');
        note.className = 'woven-revealed-note';
        note.textContent = 'Outside the current filters. Shown because it was opened directly.';
        button.append(note);
      }
      item.append(button);
      fragment.append(item);
    });
    list.replaceChildren(fragment);
    // The count is the count of matches. A revealed record is named separately
    // rather than folded into a number that would then be wrong.
    status.textContent = matched.length === 0 && filtered
      ? `No publications match these filters. ${all.length} publications in the archive.`
      : `${matched.length} of ${all.length} publications`;
    const empty = document.getElementById('woven-browser-empty');
    empty.hidden = matched.length !== 0;
    eraChoices.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.era === era)));
    clear.disabled = !filtered;
    filter(filtered ? new Set(current.map((thread) => thread.id)) : null, {
      matchCount: matched.length,
      filtered,
      revealed: outside ? revealed : null
    });
  }

  function changed() {
    app.three.panel.closePanel();
    render();
    announce(`${status.textContent}. Other publications are dimmed.`);
  }
  city.addEventListener('change', changed);
  evidence.addEventListener('change', changed);
  // The index's own button also takes the visitor back to the whole span, which
  // is what "clear" means there. Cleared from a notice beside a record they just
  // opened, the view stays where it is; being thrown back to 1880 would be a
  // second surprise on top of the first.
  function clearFilters(options) {
    era = 'all';
    city.value = '';
    evidence.value = 'all';
    changed();
    if (!options || options.move !== false) focusEra(era);
  }
  clear.addEventListener('click', clearFilters);
  list.addEventListener('click', (event) => {
    const button = event.target.closest('[data-pub]');
    if (button) open(Number(button.dataset.pub));
  });
  list.addEventListener('pointerover', (event) => {
    const button = event.target.closest('[data-pub]');
    if (button) highlight(Number(button.dataset.pub));
  });
  list.addEventListener('pointerleave', () => highlight(null));
  list.addEventListener('focusin', (event) => {
    const button = event.target.closest('[data-pub]');
    if (button) highlight(Number(button.dataset.pub));
  });
  list.addEventListener('focusout', (event) => { if (!list.contains(event.relatedTarget)) highlight(null); });
  document.getElementById('woven-find-title').addEventListener('click', () => {
    app.three.panel.closePanel();
    queueMicrotask(() => document.getElementById('woven-search')?.focus());
  });
  // The record occupies the index dock, never the drawing. Hide the underlying
  // index from both pointer and keyboard users until the record is closed.
  const panelObserver = new MutationObserver(() => {
    root.inert = !panel.hidden;
    root.setAttribute('aria-hidden', String(!panel.hidden));
    syncSelected();
  });
  panelObserver.observe(panel, { attributes: true, attributeFilter: ['hidden'] });

  function syncSelected() {
    for (const button of list.querySelectorAll('[data-pub]')) {
      button.setAttribute('aria-pressed', String(Number(button.dataset.pub) === app.state.selectedId));
    }
  }
  function reset() {
    era = 'all';
    city.value = '';
    evidence.value = 'all';
    revealed = null;
    render();
  }
  render();

  const stories = document.getElementById('woven-story-list');
  const available = model.tours.filter((tour) => tour.stops.length);
  const featured = [...new Set([available[0], available[Math.floor(available.length / 2)], available.at(-1)])].filter(Boolean);
  for (const tour of featured) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    const title = document.createElement('strong');
    title.textContent = tour.title;
    const meta = document.createElement('span');
    meta.textContent = `${tour.era} · ${tour.stops.length} stop${tour.stops.length === 1 ? '' : 's'}${tour.strength === 'weak' ? ' · thinly sourced' : ''}`;
    button.append(title, meta);
    button.addEventListener('click', () => {
      app.playStory(tour.id);
      document.getElementById('woven-stage')?.scrollIntoView({ block: 'start', behavior: 'instant' });
    });
    item.append(button);
    stories.append(item);
  }
  document.getElementById('woven-all-stories').addEventListener('click', () => {
    document.getElementById('woven-stage').scrollIntoView({ block: 'start', behavior: 'instant' });
    document.getElementById('btn-tours').click();
  });
  document.getElementById('woven-stories').hidden = !model.tours.some((tour) => tour.stops.length);
  return {
    reset,
    clearFilters,
    /**
     * Show a record the filters exclude, without touching the filters. Returns
     * true when the record really was outside them, so the caller can explain
     * the mismatch and offer to clear them.
     */
    reveal: (id) => {
      if (current.some((thread) => thread.id === id)) {
        // Already listed. A record revealed earlier is no longer needed.
        if (revealed != null && revealed !== id) { revealed = null; render(); }
        return false;
      }
      revealed = id;
      render();
      return true;
    },
    scope: (key) => { era = key; changed(); },
    era: () => era,
    syncSelected,
    records: () => current,
    dispose: () => { panelObserver.disconnect(); document.getElementById('woven-stories').hidden = true; }
  };
}
