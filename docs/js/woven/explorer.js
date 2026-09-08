import { matchesFilters, publicationYears, threadColor } from './exhibit-geometry.js';
import { announce } from './twin.js';

// A real, keyboard-accessible index alongside either drawing. No second fetch,
// no synthetic stories, and no canvas-only route to a publication.
export function mountExplorer(app, { highlight, filter, open }) {
  const model = app.model;
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

  function render() {
    const selection = { city: city.value, evidence: evidence.value };
    current = all.filter((thread) => matchesFilters(thread, selection));
    const fragment = document.createDocumentFragment();
    current.forEach((thread) => {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'woven-publication';
      button.dataset.pub = String(thread.id);
      button.style.setProperty('--thread-color', threadColor(thread));
      button.setAttribute('aria-pressed', String(app.state.selectedId === thread.id));
      const name = document.createElement('strong');
      name.textContent = thread.name;
      const meta = document.createElement('span');
      meta.textContent = `${thread.city || 'City unrecorded'} · ${publicationYears(thread)}`;
      button.append(name, meta);
      item.append(button);
      fragment.append(item);
    });
    list.replaceChildren(fragment);
    status.textContent = `${current.length} of ${all.length} publications`;
    const empty = document.getElementById('woven-browser-empty');
    empty.hidden = current.length !== 0;
    const filtered = !!city.value || evidence.value !== 'all';
    clear.disabled = !filtered;
    filter(filtered ? new Set(current.map((thread) => thread.id)) : null);
  }

  function changed() {
    app.three.panel.closePanel();
    render();
    announce(`${status.textContent}. Other threads are dimmed, not removed.`);
  }
  city.addEventListener('change', changed);
  evidence.addEventListener('change', changed);
  clear.addEventListener('click', () => { city.value = ''; evidence.value = 'all'; changed(); });
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
    document.getElementById('woven-search').focus();
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
    city.value = '';
    evidence.value = 'all';
    render();
  }
  render();

  const stories = document.getElementById('woven-story-list');
  for (const tour of model.tours.filter((tour) => tour.stops.length).slice(0, 3)) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    const title = document.createElement('strong');
    title.textContent = tour.title;
    const meta = document.createElement('span');
    meta.textContent = `${tour.era} · ${tour.stops.length} stops${tour.strength === 'weak' ? ' · thinly sourced' : ''}`;
    button.append(title, meta);
    button.addEventListener('click', () => {
      app.playStory(tour.id);
      document.getElementById('woven-stage').scrollIntoView({ block: 'start', behavior: 'instant' });
    });
    item.append(button);
    stories.append(item);
  }
  document.getElementById('woven-all-stories').addEventListener('click', () => {
    document.getElementById('woven-stage').scrollIntoView({ block: 'start', behavior: 'instant' });
    document.getElementById('btn-tours').click();
  });
  document.getElementById('woven-stories').hidden = !model.tours.some((tour) => tour.stops.length);
  return { reset, syncSelected, records: () => current, dispose: () => panelObserver.disconnect() };
}
