// Woven — the accessibility twin. The same archive as a document.
// It is built before any triangle renders and stays complete at all times.

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

let model = null;
let hooks = {};
let liveEl = null;
let liveAssertEl = null;
let lastAnnounce = 0;

export function buildTwin(m, callbacks) {
  model = m;
  hooks = callbacks || {};
  const root = document.getElementById('woven-twin');
  liveEl = document.getElementById('woven-live');
  liveAssertEl = document.getElementById('woven-live-assertive');

  const c = m.counts;
  root.innerHTML = `
    <h2 id="woven-twin-h">The weave, as a list</h2>
    <p id="woven-help">${c.total} publications, 1880 to 2026, grouped by the decade each one began. Open any title for its evidence and its events.</p>
    <ol class="era-bands">${m.bands.filter((b) => b.count).map(bandHTML).join('')}</ol>
    <section id="woven-twin-tours" aria-labelledby="tours-h">
      <h3 id="tours-h">Guided threads</h3>
      <ol class="tour-list">${m.tours.map(tourHTML).join('')}</ol>
    </section>
    <section id="woven-twin-ghost" aria-labelledby="ghost-h">
      <h3 id="ghost-h">Titles that survive only as a catalog entry</h3>
      <p>${c.ghost} of these papers exist now as a single line in a catalog — a title, a city, a range of years, recorded by a librarian who held the issue we cannot find. No page, no masthead, no photograph. They are woven into the same cloth as everything else, thin and unfinished, because an absence in the record is not an absence in the history. Their names follow.</p>
      <ol class="ghost-list">${ghostHTML()}</ol>
    </section>`;

  root.addEventListener('click', onClick);
  return root;
}

function bandHTML(band) {
  return `<li class="era-band" id="band-${band.key}" aria-labelledby="band-${band.key}-h">
    <h3 id="band-${band.key}-h">${esc(band.label)} — ${band.count} publication${band.count === 1 ? '' : 's'}</h3>
    <ol class="threads">${band.threads.map(threadHTML).join('')}</ol>
  </li>`;
}

function stateLine(t) {
  if (t.endState === 'still') return 'still publishing';
  if (t.endState === 'ceased') return `ceased ${t.yearCeased ?? 'date unknown'}`;
  return 'end date unrecorded';
}

function yearsLine(t) {
  const a = t.yearFounded ?? 'founding year unrecorded';
  if (t.endState === 'ceased' && t.yearCeased) return `${a} to ${t.yearCeased}`;
  if (t.endState === 'still') return `${a} to now`;
  return `${a} onward, end unrecorded`;
}

function threadHTML(t) {
  const ev = t.evidenceCount === 1 ? '1 item of evidence' : `${t.evidenceCount} items of evidence`;
  const evidenceLine = t.ghost ? 'catalog entry only' : ev;
  return `<li id="thread-${t.id}" data-pub="${t.id}" data-state="${t.endState}"${t.ghost ? ' data-ghost="true"' : ''}>
    <button type="button" class="t-open" data-pub="${t.id}" aria-expanded="false" aria-controls="thread-${t.id}-detail">
      <span class="t-name">${esc(t.name)}</span>
      <span class="t-place">${esc(t.city || 'city unrecorded')}</span>
      <span class="t-years">${esc(yearsLine(t))}</span>
      <span class="t-evidence">${esc(evidenceLine)}</span>
      <span class="t-state">${esc(stateLine(t))}</span>
    </button>
    <div id="thread-${t.id}-detail" class="t-detail" hidden>
      ${t.alternateName ? `<p class="t-alt">Also known as ${esc(t.alternateName)}</p>` : ''}
      ${t.publishers ? `<p class="t-meta">Publisher: ${esc(t.publishers)}</p>` : ''}
      ${t.format || t.frequency || t.medium ? `<p class="t-meta">${esc([t.format, t.frequency, t.medium].filter(Boolean).join(' · '))}</p>` : ''}
      ${t.missionStatement ? `<p class="t-mission"><em>${esc(t.missionStatement)}</em></p>` : ''}
      ${t.historicalNotes ? `<p class="t-notes">${esc(t.historicalNotes)}</p>` : ''}
      ${evidenceHTML(t)}
      ${eventsHTML(t)}
      ${storiesHTML(t)}
      <a class="link-thread" href="publication.html?id=${t.id}">Open the full record</a>
    </div>
  </li>`;
}

function evidenceHTML(t) {
  if (!t.evidence.length) return '<p class="t-meta">No evidence recorded.</p>';
  return `<h4>Evidence we hold</h4><ol class="evidence">${t.evidence.map((e) => `
    <li class="evidence-item" data-rights="${esc(e.rightsStatus)}">
      <span class="ev-rights">${esc(e.rightsStatus.replace(/_/g, ' '))}</span>
      <cite>${esc(e.citation || e.caption || e.source || 'source unrecorded')}</cite>
      ${e.url ? `<a class="link-thread" href="${esc(e.url)}" target="_blank" rel="noopener noreferrer">View at source</a>` : ''}
    </li>`).join('')}</ol>`;
}

function eventsHTML(t) {
  if (!t.events || !t.events.length) return '';
  return `<h4>Documented events</h4><ol class="events">${t.events.map((k) => `
    <li id="ev-${t.id}-${k.eventId}" data-event="${k.eventId}">
      <span class="e-date">${esc(k.event.date)}</span>
      <span class="e-title">${esc(k.event.title)}</span>
      ${k.confidence === 'medium' ? '<span class="e-conf">Medium confidence</span>' : ''}
    </li>`).join('')}</ol>`;
}

function storiesHTML(t) {
  if (!t.stories || !t.stories.length) return '';
  return `<h4>Part of these threads</h4><ul class="stories">${t.stories.map((s) => `
    <li><button type="button" class="t-play" data-story="${esc(s.id)}">${esc(s.title)}</button></li>`).join('')}</ul>`;
}

function tourHTML(tour) {
  const weak = tour.strength === 'weak';
  return `<li id="tour-${esc(tour.id)}" data-story="${esc(tour.id)}">
    <h4>${esc(tour.title)}</h4>
    <p class="tour-meta">${esc(tour.era)} · ${tour.stops.length} stop${tour.stops.length === 1 ? '' : 's'}${weak ? ' · Thinly sourced' : ''}</p>
    <button type="button" class="t-play" data-story="${esc(tour.id)}">Play the thread</button>
    <details><summary>Read this thread as text</summary>
      <p>${esc(tour.thread)}</p>
      ${weak ? '<p class="warn">This thread rests on two cover artifacts and one dated clipping. Read it as a lead, not a finding.</p>' : ''}
      <h5>Publications in this thread</h5>
      <ul>${tour.threadIds.map((id) => `<li><a class="link-thread" href="?pub=${id}">${esc(model.byId.get(id).name)}</a></li>`).join('')}</ul>
      <h5>Stops</h5>
      <ol>${tour.stops.map((s) => `<li><span class="e-date">${esc(s.dateLabel)}</span> ${esc(s.event.title)}<br><span class="e-desc">${esc(s.event.description)}</span>${s.clipping ? `<br><cite>${esc(s.clipping.citation)}</cite>` : ''}</li>`).join('')}</ol>
    </details>
  </li>`;
}

function ghostHTML() {
  return model.threads
    .filter((t) => t.ghost)
    .sort((a, b) => (a.yearFounded ?? 9999) - (b.yearFounded ?? 9999) || a.name.localeCompare(b.name))
    .map((t) => `<li id="ghost-${t.id}" data-pub="${t.id}">
      <span class="g-name">${esc(t.name)}</span>
      <span class="g-place">${esc(t.city || 'city unrecorded')}</span>
      <span class="g-years">${esc(yearsLine(t))}</span>
      <cite>${esc((t.evidence[0] && t.evidence[0].citation) || 'No catalog citation recorded.')}</cite>
    </li>`).join('');
}

function onClick(e) {
  const play = e.target.closest('.t-play');
  if (play) { hooks.playStory && hooks.playStory(play.dataset.story); return; }
  const open = e.target.closest('.t-open');
  if (!open) return;
  const li = open.parentElement;
  const detail = li.querySelector('.t-detail');
  const expanded = open.getAttribute('aria-expanded') === 'true';
  open.setAttribute('aria-expanded', String(!expanded));
  detail.hidden = expanded;
  if (!expanded) hooks.select && hooks.select(+open.dataset.pub, { fromTwin: true });
}

/** One direction of truth: the canvas and the twin both render this state. */
export function syncTwin(state) {
  const root = document.getElementById('woven-twin');
  if (!root) return;
  root.querySelectorAll('[aria-current]').forEach((el) => el.removeAttribute('aria-current'));
  root.querySelectorAll('[data-hover]').forEach((el) => el.removeAttribute('data-hover'));
  root.querySelectorAll('[data-in-tour]').forEach((el) => el.removeAttribute('data-in-tour'));

  if (state.selectedId != null) {
    const li = document.getElementById(`thread-${state.selectedId}`);
    if (li) {
      li.setAttribute('aria-current', 'true');
      if (state.scrollTwin) li.scrollIntoView({ block: 'nearest' });
    }
  }
  if (state.hoverId != null) {
    const li = document.getElementById(`thread-${state.hoverId}`);
    if (li) li.setAttribute('data-hover', 'true');
  }
  if (state.tourId) {
    const li = document.getElementById(`tour-${state.tourId}`);
    if (li) li.setAttribute('aria-current', 'step');
    const tour = model.tours.find((t) => t.id === state.tourId);
    if (tour) {
      for (const id of tour.threadIds) {
        const el = document.getElementById(`thread-${id}`);
        if (el) el.setAttribute('data-in-tour', 'true');
      }
      const stop = tour.stops[state.stopIndex];
      if (stop && stop.threadId != null) {
        const btn = document.querySelector(`#thread-${stop.threadId} .t-open`);
        const detail = document.getElementById(`thread-${stop.threadId}-detail`);
        if (btn && detail && detail.hidden) { btn.setAttribute('aria-expanded', 'true'); detail.hidden = false; }
        const evLi = document.getElementById(`ev-${stop.threadId}-${stop.eventId}`);
        if (evLi) evLi.setAttribute('aria-current', 'step');
      }
    }
  }
  if (state.ghostGroup) {
    for (const id of state.ghostGroup) {
      const el = document.getElementById(`ghost-${id}`);
      if (el) el.setAttribute('aria-current', 'true');
    }
  }
}

/** Polite announcements, throttled to one per 800 ms. Extra messages drop. */
export function announce(text) {
  if (!liveEl) return;
  const now = performance.now();
  if (now - lastAnnounce < 800) return;
  lastAnnounce = now;
  liveEl.textContent = text;
}

export function announceAssertive(text) {
  if (liveAssertEl) liveAssertEl.textContent = text;
}

export function promoteTwin(message) {
  const stage = document.getElementById('woven-stage');
  if (stage && stage.parentNode) stage.parentNode.removeChild(stage);
  document.body.classList.add('twin-primary');
  const banner = document.getElementById('woven-banner');
  if (banner) {
    banner.hidden = false;
    banner.querySelector('.banner-text').textContent = message;
  }
  announceAssertive(message);
}
