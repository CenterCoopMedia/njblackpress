/**
 * NJ Black Press Archive — decade (era) pages (issue #40)
 *
 * One template, routed by ?decade=1930s. With no decade the page lists every
 * decade that holds records, with counts.
 *
 * RIGHTS RULE: the only images this file may emit are `webPath` values read
 * from data/clippings.json, and every one carries the `alt` text held beside
 * it. No other path is ever used as an image source, and a clipping without
 * alt text is skipped rather than rendered with an empty alt.
 */

(function () {
    'use strict';

    let publications = [];
    let publicationsById = {};
    let events = [];
    let clippings = [];
    let stories = [];

    let decades = [];          // every decade holding records, oldest first
    let pubsByDecade = {};
    let eventsByDecade = {};
    let clipsByDecade = {};

    async function init() {
        await loadData();
        indexByDecade();

        const decade = getDecade();
        if (!decade) {
            renderIndex();
            return;
        }

        if (decades.indexOf(decade) === -1) {
            showError();
            return;
        }

        renderDecade(decade);
    }

    function getDecade() {
        const params = new URLSearchParams(window.location.search);
        const value = params.get('decade');
        return value ? value.trim() : null;
    }

    async function loadData() {
        try {
            const [pubRes, eventRes, clipRes, storyRes] = await Promise.all([
                fetch('data/publications.json'),
                fetch('data/events.json'),
                fetch('data/clippings.json'),
                fetch('data/stories.json')
            ]);

            if (pubRes.ok) {
                const data = await pubRes.json();
                publications = data.publications || [];
                publications.forEach(p => { publicationsById[p.id] = p; });
            }
            if (eventRes.ok) {
                const data = await eventRes.json();
                events = data.events || [];
            }
            if (clipRes.ok) {
                const data = await clipRes.json();
                clippings = (data.clippings || []).filter(c => c.webPath && c.alt);
            }
            if (storyRes.ok) {
                const data = await storyRes.json();
                stories = data.stories || [];
            }
        } catch (error) {
            console.error('Failed to load era data:', error);
        }
    }

    function decadeOfYear(value) {
        const match = String(value || '').match(/\d{4}/);
        if (!match) return null;
        return match[0].slice(0, 3) + '0s';
    }

    function indexByDecade() {
        const seen = {};
        const add = (map, decade, item) => {
            if (!decade) return;
            if (!map[decade]) map[decade] = [];
            map[decade].push(item);
            seen[decade] = true;
        };

        publications.forEach(p => {
            // 'Unknown' is a real value in the data. A decade page cannot hold
            // a record with no founding year, so those titles stay out.
            const decade = p.decade && p.decade !== 'Unknown' ? p.decade : decadeOfYear(p.yearFounded);
            add(pubsByDecade, decade, p);
        });

        events.forEach(e => add(eventsByDecade, decadeOfYear(e.date), e));

        clippings.forEach(c => {
            // A clipping belongs to the decade its publication was founded in,
            // which is how the archive groups the record it illustrates.
            const placed = {};
            (c.publicationIds || []).forEach(pid => {
                const pub = publicationsById[pid];
                if (!pub) return;
                const decade = pub.decade && pub.decade !== 'Unknown' ? pub.decade : decadeOfYear(pub.yearFounded);
                if (!decade || placed[decade]) return;
                placed[decade] = true;
                add(clipsByDecade, decade, { clip: c, pub: pub });
            });
        });

        decades = Object.keys(seen).sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
    }

    // ---------------------------------------------------------------
    // Index — every decade with counts
    // ---------------------------------------------------------------

    function renderIndex() {
        const container = document.getElementById('era-content');
        if (!container) return;

        setMetadata(
            'Eras | NJ Black Press Archive',
            'Every decade the NJ Black Press Archive holds records for, with counts of publications founded, dated events and clippings.',
            'https://centercoopmedia.github.io/njblackpress/era.html'
        );

        if (decades.length === 0) {
            container.innerHTML = emptyPage('Eras', 'No decade in this archive holds records yet.');
            return;
        }

        const rows = decades.map(d => {
            const pubs = (pubsByDecade[d] || []).length;
            const evts = (eventsByDecade[d] || []).length;
            const clips = (clipsByDecade[d] || []).length;
            return `
                <li class="surface-cloth bg-ink-700 border border-ink-600 p-6">
                    <h2 class="font-display text-2xl font-bold leading-snug">
                        <a href="era.html?decade=${encodeURIComponent(d)}" class="text-paper-100 hover:text-accent transition-colors">The ${escapeHtml(d)}</a>
                    </h2>
                    <p class="font-mono text-[11px] text-paper-300 mt-3 tabular-nums">
                        ${pubs === 1 ? '1 publication founded' : pubs + ' publications founded'} &middot;
                        ${evts === 1 ? '1 dated event' : evts + ' dated events'} &middot;
                        ${clips === 1 ? '1 clipping' : clips + ' clippings'}
                    </p>
                </li>
            `;
        }).join('');

        container.innerHTML = `
            <section class="px-4 md:px-8 py-12 md:py-16">
                <div class="max-w-[1100px] mx-auto">
                    <h1 class="type-impression font-display text-4xl sm:text-5xl md:text-6xl font-extrabold leading-[0.95] tracking-normal text-paper-100 mb-4 balance">Eras</h1>
                    <p class="measure font-sans text-lg text-paper-200 leading-relaxed mb-10">
                        The archive holds records across ${decades.length} decades. Each decade page gathers the titles
                        founded then, the dated events logged for those years, and the clippings we are cleared to show.
                        The same material also reads as
                        <a href="story.html" class="link-thread text-accent hover:text-paper-100 transition-colors">narrative threads</a>.
                    </p>
                    <ul class="grid grid-cols-1 md:grid-cols-2 gap-4">${rows}</ul>
                </div>
            </section>
        `;
    }

    // ---------------------------------------------------------------
    // One decade
    // ---------------------------------------------------------------

    function renderDecade(decade) {
        const container = document.getElementById('era-content');
        if (!container) return;

        const pubs = (pubsByDecade[decade] || []).slice().sort((a, b) => {
            const ay = a.yearFounded || 0;
            const by = b.yearFounded || 0;
            if (ay !== by) return ay - by;
            return String(a.name).localeCompare(String(b.name));
        });
        const evts = (eventsByDecade[decade] || []).slice().sort((a, b) => {
            const av = String(a.date || '');
            const bv = String(b.date || '');
            return av === bv ? 0 : (av < bv ? -1 : 1);
        });
        const clips = (clipsByDecade[decade] || []);
        const threads = stories.filter(s => eraDecades(s.era).indexOf(decade) !== -1);

        const index = decades.indexOf(decade);
        const previous = index > 0 ? decades[index - 1] : null;
        const next = index < decades.length - 1 ? decades[index + 1] : null;

        const title = 'The ' + decade + ' | NJ Black Press Archive';
        const description = 'The ' + decade + ' in the NJ Black Press Archive: '
            + pubs.length + (pubs.length === 1 ? ' publication founded, ' : ' publications founded, ')
            + evts.length + (evts.length === 1 ? ' dated event, ' : ' dated events, ')
            + clips.length + (clips.length === 1 ? ' clipping.' : ' clippings.');
        setMetadata(title, description, 'https://centercoopmedia.github.io/njblackpress/era.html?decade=' + encodeURIComponent(decade));
        setBreadcrumb('The ' + decade);

        container.innerHTML = `
            <article>
                <header class="px-4 md:px-8 pt-12 md:pt-16 pb-8">
                    <div class="max-w-[1100px] mx-auto">
                        <h1 class="type-impression font-display text-4xl sm:text-5xl md:text-6xl font-extrabold leading-[0.95] tracking-normal text-paper-100 mb-4 balance">The ${escapeHtml(decade)}</h1>
                        <p class="font-mono text-xs text-paper-300 tabular-nums">
                            ${pubs.length === 1 ? '1 publication founded' : pubs.length + ' publications founded'} &middot;
                            ${evts.length === 1 ? '1 dated event' : evts.length + ' dated events'} &middot;
                            ${clips.length === 1 ? '1 clipping' : clips.length + ' clippings'}
                        </p>
                    </div>
                </header>

                <section class="px-4 md:px-8 py-10 border-t border-ink-600" aria-labelledby="pubs-heading">
                    <div class="max-w-[1100px] mx-auto">
                        <h2 id="pubs-heading" class="font-display text-2xl font-bold text-paper-100 mb-2">Publications founded in the ${escapeHtml(decade)}</h2>
                        <hr class="rail-wood mb-8" aria-hidden="true">
                        ${pubs.length > 0 ? `
                            <ul class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                ${pubs.map(p => `
                                    <li class="surface-cloth bg-ink-700 border border-ink-600 p-6">
                                        <p class="font-mono text-[10px] uppercase tracking-widest text-paper-300 mb-2">${escapeHtml(p.city || 'New Jersey')}</p>
                                        <h3 class="font-display text-lg font-bold leading-snug">
                                            <a href="publication.html?id=${p.id}" class="text-paper-100 hover:text-accent transition-colors">${escapeHtml(p.name)}</a>
                                        </h3>
                                        <p class="font-mono text-xs text-paper-300 mt-2 tabular-nums">${escapeHtml(formatYears(p))}</p>
                                    </li>
                                `).join('')}
                            </ul>
                        ` : `<p class="measure font-sans text-paper-200">No publication in this archive was founded in the ${escapeHtml(decade)}.</p>`}
                    </div>
                </section>

                <section class="px-4 md:px-8 py-10 bg-ink-800 border-y border-ink-600" aria-labelledby="events-heading">
                    <div class="max-w-[1100px] mx-auto">
                        <h2 id="events-heading" class="font-display text-2xl font-bold text-paper-100 mb-2">Dated events</h2>
                        <hr class="rail-wood mb-8" aria-hidden="true">
                        ${evts.length > 0 ? `
                            <ol class="space-y-8">${evts.map(eventEntry).join('')}</ol>
                        ` : `<p class="measure font-sans text-paper-200">No dated events are logged for this decade yet.</p>`}
                    </div>
                </section>

                <section class="px-4 md:px-8 py-10" aria-labelledby="clippings-heading">
                    <div class="max-w-[1100px] mx-auto">
                        <h2 id="clippings-heading" class="font-display text-2xl font-bold text-paper-100 mb-2">Clippings</h2>
                        <hr class="rail-wood mb-8" aria-hidden="true">
                        ${clips.length > 0 ? `
                            <div class="space-y-10">${clips.map(entry => clippingFigure(entry.clip, entry.pub)).join('')}</div>
                        ` : `<p class="measure font-sans text-paper-200">No clipping we are cleared to publish belongs to a title founded in this decade.</p>`}
                    </div>
                </section>

                <section class="px-4 md:px-8 py-10 border-t border-ink-600" aria-labelledby="threads-heading">
                    <div class="max-w-[1100px] mx-auto">
                        <h2 id="threads-heading" class="font-display text-2xl font-bold text-paper-100 mb-2">Stories that run through this decade</h2>
                        <hr class="rail-wood mb-8" aria-hidden="true">
                        ${threads.length > 0 ? `
                            <ul class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                ${threads.map(s => `
                                    <li class="surface-cloth bg-ink-700 border border-ink-600 p-6">
                                        <h3 class="font-display text-lg font-bold leading-snug">
                                            <a href="story.html?id=${encodeURIComponent(s.id)}" class="text-paper-100 hover:text-accent transition-colors">${escapeHtml(s.title)}</a>
                                        </h3>
                                        <p class="font-mono text-[11px] text-paper-300 mt-2">${escapeHtml(formatEra(s.era) || 'era not recorded')}</p>
                                        ${s.strength === 'weak' ? `<p class="font-mono text-[11px] text-accent mt-2">Thinly sourced.</p>` : ''}
                                    </li>
                                `).join('')}
                            </ul>
                        ` : `<p class="measure font-sans text-paper-200">No narrative thread reaches this decade yet.</p>`}
                    </div>
                </section>

                <nav class="px-4 md:px-8 pb-16" aria-label="Decade navigation">
                    <div class="max-w-[1100px] mx-auto flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
                        ${previous ? `<a href="era.html?decade=${encodeURIComponent(previous)}" class="text-accent hover:text-paper-100 transition-colors"><span aria-hidden="true">&larr;</span> The ${escapeHtml(previous)}</a>` : `<span class="text-paper-300">The ${escapeHtml(decade)} is the earliest decade on record.</span>`}
                        <a href="era.html" class="text-accent hover:text-paper-100 transition-colors">All decades</a>
                        ${next ? `<a href="era.html?decade=${encodeURIComponent(next)}" class="text-accent hover:text-paper-100 transition-colors">The ${escapeHtml(next)} <span aria-hidden="true">&rarr;</span></a>` : `<span class="text-paper-300">The ${escapeHtml(decade)} is the most recent decade on record.</span>`}
                    </div>
                </nav>
            </article>
        `;
    }

    function eventEntry(event) {
        const pubs = (event.publicationIds || []).map(id => publicationsById[id]).filter(Boolean);
        return `
            <li class="border-l-2 border-ink-600 pl-5 md:pl-6">
                <p class="font-mono text-[11px] uppercase tracking-widest text-accent mb-2 tabular-nums">${escapeHtml(formatDate(event.date))}</p>
                <h3 class="font-display text-xl font-bold text-paper-100 leading-snug measure balance mb-3">${escapeHtml(event.title)}</h3>
                ${event.description ? `<p class="measure font-sans text-[17px] leading-[1.7] text-paper-200">${escapeHtml(event.description)}</p>` : ''}
                ${event.confidence === 'medium' ? `<p class="measure font-mono text-[11px] text-paper-300 mt-3">Medium confidence. The date or the detail is not fully settled.</p>` : ''}
                ${pubs.length > 0 ? `
                    <p class="font-mono text-[11px] text-paper-300 mt-3">
                        ${pubs.length === 1 ? 'Publication:' : 'Publications:'}
                        ${pubs.map(p => `<a href="publication.html?id=${p.id}" class="text-accent hover:text-paper-100 transition-colors">${escapeHtml(p.name)}</a>`).join(', ')}
                    </p>
                ` : `<p class="font-mono text-[11px] text-paper-300 mt-3">No publication in the archive is linked to this event yet.</p>`}
            </li>
        `;
    }

    function clippingFigure(clip, pub) {
        if (!clip.webPath || !clip.alt) return '';
        const cropped = clip.status === 'crop_first';
        return `
            <figure class="evidence-figure surface-cloth bg-ink-700 border border-ink-600 p-4 max-w-[720px]">
                <div class="${cropped ? 'clip-mounted' : ''}">
                    <img src="${escapeAttr(clip.webPath)}"
                         alt="${escapeAttr(clip.alt)}"
                         ${clip.width ? `width="${clip.width}"` : ''} ${clip.height ? `height="${clip.height}"` : ''}
                         loading="lazy" decoding="async">
                </div>
                <figcaption class="pt-4 space-y-2">
                    ${clip.caption ? `<p class="measure font-sans text-[15px] text-paper-100 leading-relaxed">${escapeHtml(clip.caption)}</p>` : ''}
                    ${cropped ? `<p class="measure font-mono text-[11px] text-paper-300">Cropped detail. The full page is not reproduced.</p>` : ''}
                    ${clip.status === 'publishable_with_credit' ? `<p class="measure font-mono text-[11px] text-paper-300">Free to reuse with credit.</p>` : ''}
                    ${clip.citation ? `<p class="measure font-mono text-[11px] text-paper-300 leading-relaxed"><cite class="not-italic">${escapeHtml(clip.citation)}</cite></p>` : ''}
                    ${pub ? `<p class="font-mono text-[11px] text-paper-300">From <a href="publication.html?id=${pub.id}" class="text-accent hover:text-paper-100 transition-colors">${escapeHtml(pub.name)}</a></p>` : ''}
                </figcaption>
            </figure>
        `;
    }

    // ---------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------

    const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];

    function formatDate(value) {
        const text = String(value || '').trim();
        if (!text) return 'Date not recorded';
        const parts = text.split('-');
        const year = parts[0];
        if (parts.length === 1) return year;
        const month = MONTHS[parseInt(parts[1], 10) - 1];
        if (!month) return year;
        if (parts.length === 2) return month + ' ' + year;
        return month + ' ' + parseInt(parts[2], 10) + ', ' + year;
    }

    // Era strings are stored with a hyphen; ranges read with an en dash.
    function formatEra(era) {
        return String(era || '').replace(/-/g, '–');
    }

    function eraDecades(era) {
        const years = String(era || '').match(/\d{4}/g) || [];
        if (years.length === 0) return [];
        const first = parseInt(years[0], 10);
        const last = parseInt(years[years.length - 1], 10);
        const out = [];
        for (let y = Math.min(first, last); y <= Math.max(first, last); y += 10) {
            out.push(String(y).slice(0, 3) + '0s');
        }
        return out;
    }

    function formatYears(pub) {
        if (!pub.yearFounded) return pub.isActive === false ? 'ceased, dates unknown' : 'dates unknown';
        if (pub.yearCeased) return pub.yearFounded + '–' + pub.yearCeased;
        if (pub.isActive === false) return 'founded ' + pub.yearFounded + ', ceased';
        return pub.yearFounded + '–present';
    }

    function setMetadata(title, description, canonicalUrl) {
        document.title = title;
        const titleEl = document.getElementById('page-title');
        if (titleEl) titleEl.textContent = title;
        const setMeta = (id, val) => { const el = document.getElementById(id); if (el) el.setAttribute('content', val); };
        setMeta('meta-description', description);
        setMeta('og-title', title);
        setMeta('og-description', description);
        setMeta('og-url', canonicalUrl);
        setMeta('twitter-title', title);
        setMeta('twitter-description', description);
        const canonical = document.getElementById('canonical');
        if (canonical) canonical.setAttribute('href', canonicalUrl);
    }

    function setBreadcrumb(label) {
        const list = document.getElementById('breadcrumb');
        if (!list) return;
        const sep = document.createElement('li');
        sep.setAttribute('aria-hidden', 'true');
        sep.textContent = '/';
        const current = document.createElement('li');
        current.className = 'text-paper-100';
        current.setAttribute('aria-current', 'page');
        current.textContent = label;
        list.appendChild(sep);
        list.appendChild(current);
    }

    function emptyPage(heading, message) {
        return `
            <section class="px-4 md:px-8 py-16">
                <div class="max-w-[1100px] mx-auto">
                    <h1 class="font-display text-4xl font-extrabold text-paper-100 mb-4">${escapeHtml(heading)}</h1>
                    <p class="measure font-sans text-paper-200">${escapeHtml(message)}</p>
                </div>
            </section>
        `;
    }

    function showError() {
        const content = document.getElementById('era-content');
        const error = document.getElementById('error-state');
        if (content) content.classList.add('hidden');
        if (error) error.classList.remove('hidden');
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeAttr(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
