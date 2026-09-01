// Woven — first-visit guidance, explicit search results, and mobile story balance.
const stage = document.getElementById('woven-stage');
const canvas = document.getElementById('woven-canvas');
const startCard = document.getElementById('woven-start-card');
const startButton = document.getElementById('btn-start');
const toursButton = document.getElementById('btn-tours');
const searchForm = document.getElementById('woven-searchform');
const searchInput = document.getElementById('woven-search');
const searchCount = document.getElementById('woven-search-count');
const searchResults = document.getElementById('woven-search-results');
const moreTools = document.getElementById('woven-more-tools');
const coach = document.getElementById('woven-coach');
const tourbar = document.getElementById('woven-tourbar');
const params = new URLSearchParams(location.search);
const narrow = window.matchMedia('(max-width: 700px)');
const START_KEY = 'njbp.woven.start.v2';
const COACH_KEY = 'njbp.woven.coach.v2';
const hasDeepLink = ['pub', 'story', 'ghost', 'nogl', 'twin'].some((key) => params.has(key));
let records = [];
let recordsReady = false;
let recordsFailed = false;
let matches = [];
let activeResult = -1;
function readSession(key) {
  try { return sessionStorage.getItem(key) === '1'; } catch { return false; }
}
function writeSession(key) {
  try { sessionStorage.setItem(key, '1'); } catch { /* storage can be blocked */ }
}
function openStartCard() {
  if (!startCard || !startCard.hidden) return;
  if (moreTools) moreTools.open = false;
  closeSearchResults();
  hideCoach(false);
  startCard.hidden = false;
  document.body.classList.add('woven-guide-open');
  requestAnimationFrame(() => startCard.querySelector('[data-guide-action]')?.focus({ preventScroll: true }));
}
function closeStartCard({ showCoach = true, restoreFocus = true } = {}) {
  if (!startCard || startCard.hidden) return;
  startCard.hidden = true;
  document.body.classList.remove('woven-guide-open');
  writeSession(START_KEY);
  if (showCoach) maybeShowCoach();
  if (restoreFocus) startButton?.focus({ preventScroll: true });
}
startButton?.addEventListener('click', openStartCard);
startCard?.querySelector('[data-guide-close]')?.addEventListener('click', () => closeStartCard());
startCard?.addEventListener('click', (event) => {
  if (event.target === startCard) closeStartCard();
});
startCard?.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  event.preventDefault();
  event.stopPropagation();
  closeStartCard();
});
startCard?.querySelectorAll('[data-guide-action]').forEach((button) => {
  button.addEventListener('click', () => {
    const action = button.dataset.guideAction;
    closeStartCard({ showCoach: action === 'explore', restoreFocus: false });
    if (action === 'story') {
      hideCoach(false);
      requestAnimationFrame(() => toursButton?.click());
    } else if (action === 'search') {
      hideCoach(false);
      searchInput?.focus({ preventScroll: true });
      if (searchCount) searchCount.textContent = 'Type at least 2 letters, then choose a result.';
    } else {
      canvas?.focus({ preventScroll: true });
    }
  });
});
function maybeShowCoach() {
  if (!coach || readSession(COACH_KEY) || !startCard?.hidden || hasDeepLink) return;
  if (tourbar && !tourbar.hidden) return;
  coach.hidden = false;
}
function hideCoach(remember = true) {
  if (!coach) return;
  coach.hidden = true;
  if (remember) writeSession(COACH_KEY);
}
coach?.querySelector('button')?.addEventListener('click', () => hideCoach());
canvas?.addEventListener('pointerdown', () => hideCoach(), { passive: true });
canvas?.addEventListener('wheel', () => hideCoach(), { passive: true });
canvas?.addEventListener('keydown', (event) => {
  if (/^(Arrow|Page|Home|End|Enter| |\+|-|0)/.test(event.key)) hideCoach();
});
toursButton?.addEventListener('click', () => {
  hideCoach(false);
  requestAnimationFrame(enhanceTourPicker);
});
document.getElementById('btn-ghost')?.addEventListener('click', () => hideCoach(false));
function enhanceTourPicker() {
  const picker = document.getElementById('woven-tourpicker');
  if (!picker || picker.hidden) return;
  const heading = picker.querySelector('h3');
  const intro = picker.querySelector('.card-scroll > p');
  if (heading) heading.textContent = 'Guided stories';
  if (intro) intro.textContent = 'Choose a story to follow documented events and evidence across the timeline.';
  picker.querySelectorAll('[data-play]').forEach((button) => { button.textContent = 'Start this story'; });
}
let loomReadyHandled = false;
function handleLoomReady() {
  if (loomReadyHandled) return;
  const legend = document.getElementById('woven-legend');
  if (!legend) return;
  loomReadyHandled = true;
  enhanceLegend(legend);
  if (!hasDeepLink && !readSession(START_KEY)) openStartCard();
  else if (!hasDeepLink) maybeShowCoach();
}
function enhanceLegend(legend) {
  if (legend.dataset.guideEnhanced === 'true') return;
  legend.dataset.guideEnhanced = 'true';
  legend.setAttribute('aria-label', 'How to read the loom');
  const body = legend.querySelector('.lg-body');
  if (!body) return;
  const title = document.createElement('h2');
  title.className = 'lg-title';
  title.textContent = 'How to read the loom';
  body.prepend(title);
  const lede = body.querySelector('.lg-lede');
  if (lede) lede.textContent = 'One horizontal thread equals one publication. Left to right is 1880 to 2026.';
  const rows = body.querySelectorAll('.lg-rows');
  if (rows[0]) rows[0].textContent = 'Rows are grouped by founding decade. Names appear as you zoom in.';
  if (rows[1]) rows[1].textContent = 'Drag to move, scroll or pinch to zoom, then select a thread to open the record.';
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'woven-btn lg-cta';
  button.textContent = 'Start a guided story';
  button.addEventListener('click', () => toursButton?.click());
  body.appendChild(button);
}
if (stage) {
  const legendObserver = new MutationObserver(() => handleLoomReady());
  legendObserver.observe(stage, { childList: true });
  handleLoomReady();
}
fetch('data/publications.json')
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then((data) => {
    records = Array.isArray(data.publications) ? data.publications : [];
    recordsReady = true;
    if ((searchInput?.value || '').trim().length >= 2) renderSearchResults();
  })
  .catch(() => {
    recordsFailed = true;
    if ((searchInput?.value || '').trim().length >= 2 && searchCount) {
      searchCount.textContent = 'Search is unavailable. Open the full archive instead.';
    }
  });
function normalize(value) {
  return (Array.isArray(value) ? value.join(' ') : String(value || '')).toLowerCase();
}
function scoreRecord(record, needle) {
  const name = normalize(record.name);
  const alternate = normalize(record.alternateName);
  const city = normalize(record.city);
  if (name === needle) return 0;
  if (name.startsWith(needle)) return 1;
  if (alternate.startsWith(needle)) return 2;
  if (city.startsWith(needle)) return 3;
  if (name.includes(needle)) return 4;
  if (alternate.includes(needle)) return 5;
  if (city.includes(needle)) return 6;
  return Infinity;
}
function renderSearchResults() {
  if (!searchInput || !searchResults || !searchCount) return;
  const needle = searchInput.value.trim().toLowerCase();
  activeResult = -1;
  searchInput.removeAttribute('aria-activedescendant');
  if (needle.length < 2) {
    matches = [];
    searchCount.textContent = '';
    closeSearchResults(false);
    return;
  }
  if (recordsFailed) {
    closeSearchResults(false);
    searchCount.textContent = 'Search is unavailable. Open the full archive instead.';
    return;
  }
  if (!recordsReady) {
    closeSearchResults(false);
    searchCount.textContent = 'Loading publications…';
    return;
  }
  matches = records
    .map((record) => ({ record, score: scoreRecord(record, needle) }))
    .filter((item) => Number.isFinite(item.score))
    .sort((a, b) => itemOrder(a, b))
    .map((item) => item.record);
  searchResults.textContent = '';
  if (!matches.length) {
    searchCount.textContent = 'No matching publications.';
    closeSearchResults(false);
    return;
  }
  const visible = matches.slice(0, 8);
  visible.forEach((record, index) => searchResults.appendChild(makeResult(record, index)));
  if (matches.length > visible.length) {
    const note = document.createElement('p');
    note.className = 'woven-search-overflow';
    note.setAttribute('role', 'presentation');
    note.textContent = `${matches.length - visible.length} more matches. Add another letter to narrow the list.`;
    searchResults.appendChild(note);
  }
  searchCount.textContent = `${matches.length} match${matches.length === 1 ? '' : 'es'}. Choose a result.`;
  searchResults.hidden = false;
  searchInput.setAttribute('aria-expanded', 'true');
}
function itemOrder(a, b) {
  return a.score - b.score || String(a.record.name || '').localeCompare(String(b.record.name || ''));
}
function makeResult(record, index) {
  const option = document.createElement('button');
  option.type = 'button';
  option.className = 'woven-search-option';
  option.id = `woven-search-option-${index}`;
  option.setAttribute('role', 'option');
  option.setAttribute('aria-selected', 'false');
  option.dataset.resultIndex = String(index);
  const name = document.createElement('span');
  name.className = 'woven-result-name';
  name.textContent = record.name || 'Untitled publication';
  const meta = document.createElement('span');
  meta.className = 'woven-result-meta';
  meta.textContent = `${record.city || 'city unrecorded'} · ${recordYears(record)}`;
  option.append(name, meta);
  return option;
}
function recordYears(record) {
  if (!record.yearFounded) return 'founding year unrecorded';
  if (record.yearCeased) return `${record.yearFounded}–${record.yearCeased}`;
  return `${record.yearFounded}–${record.isActive ? 'now' : '?'}`;
}
function setActiveResult(index) {
  const options = Array.from(searchResults?.querySelectorAll('[role="option"]') || []);
  if (!options.length) return;
  activeResult = Math.max(0, Math.min(options.length - 1, index));
  options.forEach((option, i) => option.setAttribute('aria-selected', String(i === activeResult)));
  const active = options[activeResult];
  searchInput?.setAttribute('aria-activedescendant', active.id);
  active.scrollIntoView({ block: 'nearest' });
}
function closeSearchResults(clearStatus = false) {
  if (!searchResults || !searchInput) return;
  searchResults.hidden = true;
  searchInput.setAttribute('aria-expanded', 'false');
  searchInput.removeAttribute('aria-activedescendant');
  activeResult = -1;
  if (clearStatus && searchCount) searchCount.textContent = '';
}
function chooseResult(record) {
  if (!record || !searchInput || !searchCount) return;
  searchInput.value = record.name || '';
  closeSearchResults(false);
  searchCount.textContent = `Opening ${record.name}.`;
  hideCoach(false);
  openRecordWhenReady(Number(record.id), record.name, 0);
}
function openRecordWhenReady(id, name, attempt) {
  if (window.njbpWoven?.open) {
    window.njbpWoven.open(id);
    if (searchCount) searchCount.textContent = `${name} selected.`;
    return;
  }
  if (window.__woven?.app?.select) {
    window.__woven.app.select(id, {});
    if (searchCount) searchCount.textContent = `${name} selected.`;
    return;
  }
  if (attempt < 40) {
    setTimeout(() => openRecordWhenReady(id, name, attempt + 1), 75);
    return;
  }
  location.assign(`${location.pathname}?pub=${encodeURIComponent(id)}`);
}
searchInput?.addEventListener('input', (event) => {
  event.stopImmediatePropagation();
  renderSearchResults();
}, true);
searchInput?.addEventListener('search', (event) => {
  event.stopImmediatePropagation();
  renderSearchResults();
}, true);
searchInput?.addEventListener('keydown', (event) => {
  if (event.key === 'ArrowDown' && !searchResults.hidden) {
    event.preventDefault();
    event.stopImmediatePropagation();
    setActiveResult(activeResult + 1);
  } else if (event.key === 'ArrowUp' && !searchResults.hidden) {
    event.preventDefault();
    event.stopImmediatePropagation();
    setActiveResult(activeResult < 0 ? 0 : activeResult - 1);
  } else if (event.key === 'Enter' && !searchResults.hidden && matches.length) {
    event.preventDefault();
    event.stopImmediatePropagation();
    chooseResult(matches[activeResult >= 0 ? activeResult : 0]);
  } else if (event.key === 'Escape' && !searchResults.hidden) {
    event.preventDefault();
    event.stopImmediatePropagation();
    closeSearchResults();
  }
}, true);
searchForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  event.stopImmediatePropagation();
  if (matches.length) chooseResult(matches[activeResult >= 0 ? activeResult : 0]);
  else renderSearchResults();
}, true);
searchResults?.addEventListener('pointerover', (event) => {
  const option = event.target.closest('[data-result-index]');
  if (option) setActiveResult(Number(option.dataset.resultIndex));
});
searchResults?.addEventListener('click', (event) => {
  const option = event.target.closest('[data-result-index]');
  if (option) chooseResult(matches[Number(option.dataset.resultIndex)]);
});
document.addEventListener('pointerdown', (event) => {
  if (searchForm && !searchForm.contains(event.target)) closeSearchResults();
  if (moreTools?.open && !moreTools.contains(event.target)) moreTools.open = false;
});
document.getElementById('btn-reset')?.addEventListener('click', () => {
  if (searchInput) searchInput.value = '';
  matches = [];
  closeSearchResults(true);
});
moreTools?.querySelector('.woven-more-panel')?.addEventListener('click', (event) => {
  if (event.target.closest('button, a')) requestAnimationFrame(() => { moreTools.open = false; });
});
moreTools?.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && moreTools.open) {
    event.stopPropagation();
    moreTools.open = false;
    moreTools.querySelector('summary')?.focus();
  }
});
let tourWasOpen = false;
let tourSyncQueued = false;
function queueTourSync() {
  if (tourSyncQueued) return;
  tourSyncQueued = true;
  requestAnimationFrame(() => {
    tourSyncQueued = false;
    syncMobileTour();
  });
}
function syncMobileTour() {
  if (!tourbar) return;
  const open = !tourbar.hidden;
  if (open && !tourWasOpen) document.body.classList.remove('woven-story-expanded');
  const mobileOpen = open && narrow.matches;
  document.body.classList.toggle('woven-mobile-tour', mobileOpen);
  if (!open) document.body.classList.remove('woven-story-expanded');
  if (mobileOpen) ensureStoryToggle();
  else tourbar.querySelector('[data-guide-story-toggle]')?.remove();
  if (open) hideCoach(false);
  tourWasOpen = open;
}
function ensureStoryToggle() {
  let toggle = tourbar.querySelector('[data-guide-story-toggle]');
  if (!toggle) {
    toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'woven-btn';
    toggle.dataset.guideStoryToggle = '';
    toggle.setAttribute('aria-controls', 'woven-card');
    toggle.addEventListener('click', () => {
      document.body.classList.toggle('woven-story-expanded');
      updateStoryToggle();
      window.__woven?.app?.measureChrome?.();
    });
    const next = tourbar.querySelector('[data-act="next"], [data-act="end"]');
    tourbar.insertBefore(toggle, next || tourbar.firstChild);
  }
  updateStoryToggle();
}
function updateStoryToggle() {
  const toggle = tourbar?.querySelector('[data-guide-story-toggle]');
  if (!toggle) return;
  const expanded = document.body.classList.contains('woven-story-expanded');
  toggle.textContent = expanded ? 'More loom' : 'Read story';
  toggle.setAttribute('aria-expanded', String(expanded));
}
if (tourbar) {
  const tourObserver = new MutationObserver(queueTourSync);
  tourObserver.observe(tourbar, { childList: true, attributes: true, attributeFilter: ['hidden'] });
  narrow.addEventListener('change', queueTourSync);
  syncMobileTour();
}
