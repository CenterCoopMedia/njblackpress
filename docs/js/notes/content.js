import { escapeHtml, publicationYears, safeURL } from './data.js';

const FEATURED_STORIES = ['story-001', 'story-004', 'story-005'];

let model;
let hooks;
let panelEl;
let twinEl;
let storyListEl;
let featuredStoriesEl;
let totalsEl;
let findListEl;
let findCountEl;
let currentStory = null;
let delegatedEventsBound = false;

export function mountContent(nextModel, nextHooks = {}) {
  model = nextModel;
  hooks = nextHooks;
  panelEl = document.getElementById('notes-panel-content');
  twinEl = document.getElementById('notes-twin');
  storyListEl = document.getElementById('notes-story-list');
  featuredStoriesEl = document.getElementById('notes-featured-stories');
  totalsEl = document.getElementById('notes-totals');
  findListEl = document.getElementById('notes-publications');
  findCountEl = document.getElementById('notes-find-count');

  populateCities();
  bindDelegatedEvents();
  renderStories();
  renderTwin();
  renderFind({});

  return {
    showPublication,
    showStop,
    close,
    renderFind,
    renderTwin,
    renderStories
  };
}

function showPublication(id, { backToStory = false } = {}) {
  const publication = model.byId.get(Number(id));
  if (!publication || !panelEl) return '';

  const relatedStories = storiesForPublication(publication.id);
  const locationNote = compositeLocationNote(publication);
  panelEl.innerHTML = `
    ${backToStory && currentStory ? '<button type="button" class="notes-back" data-action="back-story">Back to story</button>' : ''}
    <h2 id="notes-panel-title" tabindex="-1">${escapeHtml(publication.name)}</h2>
    ${publication.alternateName ? `<p class="notes-alternate">Also known as ${escapeHtml(publication.alternateName)}</p>` : ''}
    <p class="notes-meta">${escapeHtml(publication.city || 'Place not recorded')}</p>
    <p class="notes-meta">${escapeHtml(publicationYears(publication))}</p>
    ${locationNote}
    ${publication.publishers ? `<p>Publisher: ${escapeHtml(publication.publishers)}</p>` : ''}
    ${publicationDetails(publication)}
    ${publication.missionStatement ? `<p><em>${escapeHtml(publication.missionStatement)}</em></p>` : ''}
    ${publication.historicalNotes ? `<p>${escapeHtml(publication.historicalNotes)}</p>` : ''}
    ${evidenceSection(publication)}
    ${publicationSourceLinks(publication)}
    ${relatedStories.length ? relatedStoriesSection(relatedStories) : ''}
    <p><a class="notes-record-link" href="publication.html?id=${publication.id}">Open the full record</a></p>`;

  return publication.name;
}

function showStop(story, index) {
  const resolvedStory = typeof story === 'string'
    ? model.stories.find((item) => item.id === story)
    : story;
  if (!resolvedStory || !panelEl) return '';

  if (!resolvedStory.stops.length) {
    currentStory = { id: resolvedStory.id, index: 0 };
    panelEl.innerHTML = `
      <h2 id="notes-panel-title" tabindex="-1">${escapeHtml(resolvedStory.title)}</h2>
      ${resolvedStory.summary ? `<p>${escapeHtml(resolvedStory.summary)}</p>` : ''}
      <p class="notes-uncertainty">No documented stops are available for this story.</p>`;
    return resolvedStory.title;
  }

  const stop = resolvedStory.stops[Number(index)];
  if (!stop) return '';

  currentStory = { id: resolvedStory.id, index: Number(index) };
  const event = stop.event;
  const publications = (event.publicationIds || [])
    .map((id) => model.byId.get(Number(id)))
    .filter(Boolean);
  const beforeMap = Number.parseInt(event.date, 10) < 1880;
  const primaryPublication = stop.publicationId == null
    ? null
    : model.byId.get(Number(stop.publicationId));

  panelEl.innerHTML = `
    <p class="notes-kicker">${escapeHtml(resolvedStory.title)} · Stop ${Number(index) + 1} of ${resolvedStory.stops.length}</p>
    <h2 id="notes-panel-title" tabindex="-1">${escapeHtml(event.title)}</h2>
    <p class="notes-meta">${escapeHtml(stop.dateLabel || event.date)}</p>
    ${event.confidence && event.confidence !== 'high' ? `<p class="notes-confidence">Confidence: ${escapeHtml(event.confidence)}</p>` : ''}
    ${beforeMap ? '<p class="notes-uncertainty">Before this map begins.</p>' : ''}
    ${!stop.position ? '<p class="notes-uncertainty">No publication or place recorded for this event.</p>' : ''}
    ${primaryPublication ? compositeLocationNote(primaryPublication) : ''}
    <p>${escapeHtml(event.description)}</p>
    ${event.people?.length ? `<p class="notes-people">People: ${escapeHtml(event.people.join(', '))}</p>` : ''}
    ${clippingFigure(stop.clipping)}
    ${citationSection(event.sourceFiles)}
    ${publications.length ? relatedPublicationsSection(publications) : ''}`;

  return event.title;
}

function close() {
  if (panelEl) panelEl.innerHTML = '';
}

function renderFind({ query = '', city = '', evidence = 'all' } = {}) {
  const needle = normalise(query);
  const matching = model.publications
    .filter((publication) => matchesPublication(publication, needle, city, evidence))
    .sort(publicationOrder);
  const ids = new Set(matching.map((publication) => publication.id));

  if (findListEl) {
    findListEl.innerHTML = matching.length
      ? matching.map((publication) => `<li>
          <button type="button" class="notes-publication-result" data-publication="${publication.id}">
            <span class="notes-publication-name">${escapeHtml(publication.name)}</span>
            <span class="notes-publication-place">${escapeHtml(publication.city || 'Place not recorded')}</span>
            <span class="notes-publication-years">${escapeHtml(publicationYears(publication))}</span>
          </button>
        </li>`).join('')
      : '<li class="notes-empty">No titles match these filters.</li>';
  }
  if (findCountEl) findCountEl.textContent = `${matching.length} ${matching.length === 1 ? 'title' : 'titles'}`;
  return ids;
}

function renderTwin() {
  if (!twinEl) return;
  const publications = [...model.publications].sort(publicationOrder);
  twinEl.innerHTML = `
    <h2 id="notes-twin-heading">The archive, as a list</h2>
    <p>${model.counts.total} publications. Open a title to read its record, evidence, and related documented events.</p>
    <ol class="notes-record-list">
      ${publications.map(publicationRecord).join('')}
    </ol>
    <section class="notes-story-text" aria-labelledby="notes-story-text-heading">
      <h2 id="notes-story-text-heading">Stories</h2>
      <ol>${model.stories.map(storyText).join('')}</ol>
    </section>`;
}

function renderStories() {
  const stories = model.stories || [];
  if (storyListEl) {
    storyListEl.innerHTML = stories.map((story) => `<li>
      <button type="button" class="notes-story-button" data-story="${escapeHtml(story.id)}">
        <span>${escapeHtml(story.title)}</span>
        <span class="notes-story-count">${story.stops.length} ${story.stops.length === 1 ? 'stop' : 'stops'}</span>
      </button>
    </li>`).join('');
  }
  if (featuredStoriesEl) {
    featuredStoriesEl.innerHTML = FEATURED_STORIES
      .map((id) => stories.find((story) => story.id === id))
      .filter(Boolean)
      .map((story) => `<button type="button" class="notes-featured-story" data-story="${escapeHtml(story.id)}">${escapeHtml(story.title)}</button>`)
      .join('');
  }
  if (totalsEl) {
    totalsEl.textContent = `${model.counts.total} publications · ${model.counts.active} still publishing · ${model.counts.clippings} clippings`;
  }
}

function publicationRecord(publication) {
  const events = eventsForPublication(publication.id);
  const relatedStories = storiesForPublication(publication.id);
  return `<li id="notes-publication-${publication.id}">
    <details>
      <summary>${escapeHtml(publication.name)} · ${escapeHtml(publication.city || 'Place not recorded')} · ${escapeHtml(publicationYears(publication))}</summary>
      <div class="notes-record-detail">
        ${publication.alternateName ? `<p>Also known as ${escapeHtml(publication.alternateName)}</p>` : ''}
        ${publication.publishers ? `<p>Publisher: ${escapeHtml(publication.publishers)}</p>` : ''}
        ${publicationDetails(publication)}
        ${publication.missionStatement ? `<p><em>${escapeHtml(publication.missionStatement)}</em></p>` : ''}
        ${publication.historicalNotes ? `<p>${escapeHtml(publication.historicalNotes)}</p>` : ''}
        ${evidenceSection(publication)}
        ${publicationSourceLinks(publication)}
        ${events.length ? `<h3>Documented events</h3><ol class="notes-event-list">${events.map(eventText).join('')}</ol>` : ''}
        ${relatedStories.length ? relatedStoriesSection(relatedStories) : ''}
        <p><button type="button" data-publication="${publication.id}">Open this record</button></p>
        <p><a class="notes-record-link" href="publication.html?id=${publication.id}">Open the full record</a></p>
      </div>
    </details>
  </li>`;
}

function storyText(story) {
  const publications = (story.publicationIds || []).map((id) => model.byId.get(Number(id))).filter(Boolean);
  return `<li id="notes-story-${escapeHtml(story.id)}">
    <details>
      <summary>${escapeHtml(story.title)} · ${story.stops.length} ${story.stops.length === 1 ? 'stop' : 'stops'}</summary>
      <div class="notes-story-detail">
        ${story.summary ? `<p>${escapeHtml(story.summary)}</p>` : ''}
        ${publications.length ? `<h3>Publications</h3><ul>${publications.map((publication) => `<li><button type="button" data-publication="${publication.id}">${escapeHtml(publication.name)}</button></li>`).join('')}</ul>` : ''}
        <h3>Stops</h3>
        <ol class="notes-story-stops">${story.stops.map((stop, index) => stopText(story, stop, index)).join('')}</ol>
        <p><button type="button" data-story="${escapeHtml(story.id)}">Start this story</button></p>
      </div>
    </details>
  </li>`;
}

function stopText(story, stop, index) {
  const event = stop.event;
  const beforeMap = Number.parseInt(event.date, 10) < 1880;
  return `<li>
    <p><button type="button" class="notes-stop-button" data-stop-story="${escapeHtml(story.id)}" data-stop-index="${index}">${escapeHtml(stop.dateLabel || event.date)} · ${escapeHtml(event.title)}</button></p>
    <p>${escapeHtml(event.description)}</p>
    ${event.confidence && event.confidence !== 'high' ? `<p>Confidence: ${escapeHtml(event.confidence)}</p>` : ''}
    ${beforeMap ? '<p>Before this map begins.</p>' : ''}
    ${!stop.position ? '<p>No publication or place recorded for this event.</p>' : ''}
    ${clippingFigure(stop.clipping)}
    ${citationSection(event.sourceFiles)}
  </li>`;
}

function eventText(event) {
  return `<li>
    <p>${escapeHtml(event.date)} · ${escapeHtml(event.title)}</p>
    <p>${escapeHtml(event.description)}</p>
    ${event.confidence && event.confidence !== 'high' ? `<p>Confidence: ${escapeHtml(event.confidence)}</p>` : ''}
    ${citationSection(event.sourceFiles)}
  </li>`;
}

function evidenceSection(publication) {
  const evidence = publication.evidence || [];
  if (!evidence.length) return '<h3>Evidence</h3><p>No evidence records are attached to this publication in the archive.</p>';
  return `<h3>Evidence</h3><ol class="notes-evidence-list">${evidence.map(evidenceItem).join('')}</ol>`;
}

function evidenceItem(evidence) {
  const link = sourceLink(evidence.url, 'View at source');
  return `<li>
    <p><cite>${escapeHtml(evidence.citation || evidence.caption || 'Citation not recorded.')}</cite></p>
    ${evidence.caption && evidence.citation ? `<p>${escapeHtml(evidence.caption)}</p>` : ''}
    <p class="notes-rights">${escapeHtml(String(evidence.rightsStatus || '').replaceAll('_', ' '))}</p>
    ${evidence.rightsStatus === 'crop_first' ? '<p>Cropped detail. Full page not reproduced.</p>' : ''}
    ${link}
  </li>`;
}

function clippingFigure(clip) {
  if (!clip) return '';
  const imageURL = safeImageURL(clip.webPath);
  const citation = clip.citation ? `<figcaption><cite>${escapeHtml(clip.citation)}</cite>${clip.caption ? ` — ${escapeHtml(clip.caption)}` : ''}</figcaption>` : '';
  if (!imageURL) return clip.citation ? `<p><cite>${escapeHtml(clip.citation)}</cite></p>` : '';
  return `<figure class="notes-stop-clip">
    <img src="${escapeHtml(imageURL)}" alt="${escapeHtml(clip.alt || '')}" loading="lazy">
    ${citation}
    ${clip.status === 'crop_first' || clip.rightsStatus === 'crop_first' ? '<p>Cropped detail. Full page not reproduced.</p>' : ''}
  </figure>`;
}

function citationSection(sourceFiles) {
  const citations = [...new Set((sourceFiles || []).map((source) => model.citeSource(source)).filter(Boolean))];
  if (!citations.length) return '';
  return `<section class="notes-citations"><h3>Sources</h3><ul>${citations.map((citation) => `<li><cite>${escapeHtml(citation)}</cite></li>`).join('')}</ul></section>`;
}

function relatedStoriesSection(stories) {
  return `<section class="notes-related-stories"><h3>Related stories</h3><ul>${stories.map((story) => `<li><button type="button" data-story="${escapeHtml(story.id)}">${escapeHtml(story.title)}</button></li>`).join('')}</ul></section>`;
}

function relatedPublicationsSection(publications) {
  return `<section class="notes-related-publications"><h3>Publications</h3><ul>${publications.map((publication) => `<li><button type="button" data-publication="${publication.id}">${escapeHtml(publication.name)}</button></li>`).join('')}</ul></section>`;
}

function publicationSourceLinks(publication) {
  const links = [
    [publication.websiteUrl, 'Publication website'],
    [publication.archiveUrl, 'Archive record']
  ].map(([url, label]) => sourceLink(url, label)).filter(Boolean);
  return links.length ? `<section class="notes-publication-links"><h3>Links</h3>${links.join('')}</section>` : '';
}

function publicationDetails(publication) {
  const details = [publication.format, publication.frequency, publication.medium, publication.languages].filter(Boolean);
  return details.length ? `<p class="notes-meta">${escapeHtml(details.join(' · '))}</p>` : '';
}

function matchesPublication(publication, needle, city, evidence) {
  const searchable = [
    publication.name,
    publication.alternateName,
    publication.city,
    publication.publishers,
    publication.primaryFocus,
    publication.medium,
    publication.format
  ].filter(Boolean).join(' ');
  if (needle && !normalise(searchable).includes(needle)) return false;
  if (city && publication.city !== city) return false;
  if (evidence === 'active' && !publication.active) return false;
  if (evidence === 'evidence' && publication.unsourced) return false;
  if (evidence === 'missing' && !publication.unsourced) return false;
  return true;
}

function populateCities() {
  const cityEl = document.getElementById('notes-city');
  if (!cityEl) return;
  const selected = cityEl.value;
  const cities = [...new Set(model.publications.map((publication) => publication.city).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right));
  cityEl.innerHTML = `<option value="">All places</option>${cities.map((city) => `<option value="${escapeHtml(city)}">${escapeHtml(city)}</option>`).join('')}`;
  cityEl.value = cities.includes(selected) ? selected : '';
}

function storiesForPublication(id) {
  return model.stories.filter((story) => (story.publicationIds || []).includes(Number(id)));
}

function eventsForPublication(id) {
  return model.events.filter((event) => (event.publicationIds || []).includes(Number(id)));
}

function compositeLocationNote(publication) {
  const cluster = model.clusters.find((item) => item.id === publication.clusterId);
  if (cluster?.precision !== 'composite_midpoint') return '';
  return '<p class="notes-uncertainty">This location combines the recorded places. It does not identify an address.</p>';
}

function publicationOrder(left, right) {
  return (left.yearFounded ?? Number.MAX_SAFE_INTEGER) - (right.yearFounded ?? Number.MAX_SAFE_INTEGER)
    || left.name.localeCompare(right.name);
}

function normalise(value) {
  return String(value || '').trim().toLocaleLowerCase();
}

function safeImageURL(value) {
  const path = safeURL(value);
  return typeof path === 'string' ? path : '';
}

function safeExternalURL(value) {
  try {
    const url = new URL(String(value ?? ''));
    return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
  } catch {
    return '';
  }
}

function sourceLink(value, text) {
  const url = safeExternalURL(value);
  return url ? `<p><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a></p>` : '';
}

function bindDelegatedEvents() {
  if (delegatedEventsBound) return;
  delegatedEventsBound = true;
  document.addEventListener('click', (event) => {
    const control = event.target.closest('[data-action], [data-publication], [data-story], [data-stop-story]');
    if (!control || !isContentControl(control)) return;

    if (control.dataset.action === 'back-story' && currentStory) {
      hooks.onStop?.(currentStory.id, currentStory.index);
      return;
    }
    if (control.dataset.stopStory) {
      hooks.onStop?.(control.dataset.stopStory, Number(control.dataset.stopIndex));
      return;
    }
    if (control.dataset.story) {
      hooks.onStory?.(control.dataset.story);
      return;
    }
    if (control.dataset.publication && model.byId.has(Number(control.dataset.publication))) {
      hooks.onPublication?.(Number(control.dataset.publication));
    }
  });
}

function isContentControl(control) {
  return [panelEl, twinEl, storyListEl, featuredStoriesEl, findListEl]
    .filter(Boolean)
    .some((root) => root.contains(control));
}
