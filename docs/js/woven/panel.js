// Woven — the publication and event side panel. Not modal: the reader keeps
// orbiting with the record open next to the cloth.

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

let el = null;
let onClose = null;
let lastFocus = null;

export function initPanel(closeHandler) {
  el = document.getElementById('woven-panel');
  onClose = closeHandler;
  el.addEventListener('click', (e) => {
    if (e.target.closest('.p-close')) closePanel();
  });
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.stopPropagation(); closePanel(); }
  });
}

export function closePanel() {
  if (!el || el.hidden) return false;
  el.hidden = true;
  el.innerHTML = '';
  if (lastFocus && document.contains(lastFocus)) lastFocus.focus();
  lastFocus = null;
  if (onClose) onClose();
  return true;
}

export function isOpen() { return el && !el.hidden; }

function endLine(t) {
  if (t.endState === 'still') return 'Still publishing';
  if (t.endState === 'ceased') return `Ceased ${t.yearCeased ?? 'date unknown'}`;
  return 'End date unrecorded';
}

function evidenceCard(e) {
  const rights = esc(e.rightsStatus.replace(/_/g, ' '));
  if (e.rightsStatus === 'metadata_only') {
    return `<div class="evidence-card" data-rights="metadata_only">
      <span class="ev-rights">${rights}</span>
      <hr class="rail-wood">
      <p class="shelf-label">${esc(e.citation || e.caption || 'Catalog entry')}</p>
      <hr class="rail-wood">
      ${e.url ? `<a class="link-thread" href="${esc(e.url)}" target="_blank" rel="noopener noreferrer">View at source</a>` : ''}
    </div>`;
  }
  return `<div class="evidence-card" data-rights="${esc(e.rightsStatus)}">
    <span class="ev-rights">${rights}</span>
    <cite>${esc(e.citation || e.caption || '')}</cite>
    ${e.caption && e.citation ? `<p>${esc(e.caption)}</p>` : ''}
    ${e.rightsStatus === 'crop_first' ? '<p class="ev-rights">Cropped detail. Full page not reproduced.</p>' : ''}
    ${e.url ? `<a class="link-thread" href="${esc(e.url)}" target="_blank" rel="noopener noreferrer">View at source</a>` : ''}
  </div>`;
}

export function openPublication(t, model, hooks) {
  lastFocus = document.activeElement;
  const years = t.yearFounded ? `${t.yearFounded}${t.yearCeased ? `–${t.yearCeased}` : '–'}` : 'founding year unrecorded';
  el.innerHTML = `
    <button type="button" class="woven-btn p-close">Close</button>
    <h2 id="woven-panel-title" tabindex="-1">${esc(t.name)}</h2>
    ${t.alternateName ? `<p class="p-meta">Also known as ${esc(t.alternateName)}</p>` : ''}
    <p class="p-meta">${esc(t.city || 'city unrecorded')} · ${esc(years)}</p>
    <p class="p-meta">${esc(endLine(t))}</p>
    ${t.publishers ? `<p>Publisher: ${esc(t.publishers)}</p>` : ''}
    ${[t.format, t.frequency, t.medium, t.languages].some(Boolean) ? `<p class="p-meta">${esc([t.format, t.frequency, t.medium, t.languages].filter(Boolean).join(' · '))}</p>` : ''}
    ${t.missionStatement ? `<p><em>${esc(t.missionStatement)}</em></p>` : ''}
    ${t.historicalNotes ? `<p>${esc(t.historicalNotes)}</p>` : ''}
    <h3>Evidence we hold</h3>
    ${t.evidence.length ? t.evidence.map(evidenceCard).join('') : '<p>Nothing survives but the catalog entry.</p>'}
    ${t.stories && t.stories.length ? `<h3>Part of these threads</h3>${t.stories.map((s) => `<p><button type="button" class="woven-btn t-play" data-story="${esc(s.id)}">${esc(s.title)}</button></p>`).join('')}` : ''}
    <h3>Full record</h3>
    <p><a class="link-thread" href="publication.html?id=${Number(t.id)}">Open the full record</a></p>`;
  el.hidden = false;
  el.querySelectorAll('.t-play').forEach((b) => {
    b.addEventListener('click', () => hooks.playStory(b.dataset.story));
  });
  el.querySelector('#woven-panel-title').focus();
}

export function openEvent(k, model, hooks) {
  lastFocus = document.activeElement;
  const e = k.event;
  const related = (e.publicationIds || []).map((id) => model.byId.get(id)).filter(Boolean);
  el.innerHTML = `
    <button type="button" class="woven-btn p-close">Close</button>
    <h2 id="woven-panel-title" tabindex="-1">${esc(e.title)}</h2>
    <p class="p-meta">${esc(e.date)}${e.confidence === 'medium' ? ' · Medium confidence' : ''}</p>
    ${!related.length ? '<p class="p-meta">Context — not tied to a specific publication.</p>' : ''}
    <p>${esc(e.description)}</p>
    ${e.people && e.people.length ? `<h3>People</h3><p>${esc(e.people.join(', '))}</p>` : ''}
    ${related.length ? `<h3>Publications</h3>${related.map((t) => `<p><a class="link-thread" href="?pub=${Number(t.id)}">${esc(t.name)}</a></p>`).join('')}` : ''}
    ${e.sourceFiles && e.sourceFiles.length ? `<h3>Source files</h3>${e.sourceFiles.map((f) => `<p class="p-meta">${esc(f)}</p>`).join('')}` : ''}`;
  el.hidden = false;
  el.querySelector('#woven-panel-title').focus();
}
