/**
 * NJ Black Press Archive — narrative story pages (issue #40)
 *
 * One template, routed by ?id=story-NNN. With no id the page lists all
 * threads grouped by era.
 *
 * RIGHTS RULE: the only images this file may emit are `webPath` values read
 * from data/clippings.json, and every one carries the `alt` text held beside
 * it. No other path is ever used as an image source, and a clipping without
 * alt text is skipped rather than rendered with an empty alt.
 */

(function () {
    'use strict';

    let stories = [];
    let events = {};
    let publications = {};
    let clippingsByPublication = {};

    async function init() {
        await loadData();

        const id = getStoryId();
        if (!id) {
            renderIndex();
            return;
        }

        const story = stories.find(s => s.id === id);
        if (!story) {
            showError();
            return;
        }

        renderStory(story);
    }

    function getStoryId() {
        const params = new URLSearchParams(window.location.search);
        const id = params.get('id');
        return id ? id.trim() : null;
    }

    async function loadData() {
        try {
            const [storyRes, eventRes, pubRes, clipRes] = await Promise.all([
                fetch('data/stories.json'),
                fetch('data/events.json'),
                fetch('data/publications.json'),
                fetch('data/clippings.json')
            ]);

            if (storyRes.ok) {
                const data = await storyRes.json();
                stories = data.stories || [];
            }
            if (eventRes.ok) {
                const data = await eventRes.json();
                (data.events || []).forEach(e => { events[e.id] = e; });
            }
            if (pubRes.ok) {
                const data = await pubRes.json();
                (data.publications || []).forEach(p => { publications[p.id] = p; });
            }
            if (clipRes.ok) {
                const data = await clipRes.json();
                (data.clippings || []).forEach(c => {
                    if (!c.webPath || !c.alt) return;
                    (c.publicationIds || []).forEach(pid => {
                        if (!clippingsByPublication[pid]) clippingsByPublication[pid] = [];
                        clippingsByPublication[pid].push(c);
                    });
                });
            }
        } catch (error) {
            console.error('Failed to load story data:', error);
        }
    }

    // ---------------------------------------------------------------
    // Index — every thread, grouped by era
    // ---------------------------------------------------------------

    function renderIndex() {
        const container = document.getElementById('story-content');
        if (!container) return;

        setMetadata(
            'Stories | NJ Black Press Archive',
            'Thirteen narrative threads traced through the NJ Black Press Archive, each built from dated events, publications and clippings.',
            'https://centercoopmedia.github.io/njblackpress/story.html'
        );

        if (stories.length === 0) {
            container.innerHTML = emptyPage('Stories', 'No narrative threads are logged yet.');
            return;
        }

        const eras = [];
        const byEra = {};
        stories.forEach(s => {
            const era = s.era || 'Era not recorded';
            if (!byEra[era]) { byEra[era] = []; eras.push(era); }
            byEra[era].push(s);
        });
        eras.sort(compareEra);

        const groups = eras.map(era => `
            <section class="mb-14">
                <h2 class="font-display text-2xl font-bold text-paper-100 mb-2">${escapeHtml(formatEra(era))}</h2>
                <hr class="rail-wood mb-6" aria-hidden="true">
                <ul class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${byEra[era].map(s => storyCard(s)).join('')}
                </ul>
            </section>
        `).join('');

        container.innerHTML = `
            <section class="px-4 md:px-8 py-12 md:py-16">
                <div class="max-w-[1100px] mx-auto">
                    <h1 class="type-impression font-display text-4xl sm:text-5xl md:text-6xl font-extrabold leading-[0.95] tracking-normal text-paper-100 mb-4 balance">Stories</h1>
                    <p class="measure font-sans text-lg text-paper-200 leading-relaxed mb-10">
                        ${stories.length} narrative threads run through this archive. Each one is assembled from dated
                        events in the record, the publications they belong to, and the clippings we are cleared to show.
                        Read a thread, or browse the same material
                        <a href="era.html" class="link-thread text-accent hover:text-paper-100 transition-colors">decade by decade</a>.
                    </p>
                    ${groups}
                </div>
            </section>
        `;
    }

    function storyCard(story) {
        const stops = (story.eventIds || []).length;
        const pubs = (story.publicationIds || []).length;
        const opening = firstSentence(story.thread);
        const weak = story.strength === 'weak';
        return `
            <li class="surface-cloth bg-ink-700 border border-ink-600 p-6 flex flex-col gap-3">
                <h3 class="font-display text-xl font-bold leading-snug">
                    <a href="story.html?id=${encodeURIComponent(story.id)}" class="text-paper-100 hover:text-accent transition-colors">${escapeHtml(story.title)}</a>
                </h3>
                ${opening ? `<p class="font-sans text-[15px] text-paper-200 leading-relaxed">${escapeHtml(opening)}</p>` : ''}
                <p class="font-mono text-[11px] text-paper-300 mt-auto">
                    ${escapeHtml(formatEra(story.era) || 'era not recorded')} &middot;
                    ${stops === 1 ? '1 dated stop' : stops + ' dated stops'} &middot;
                    ${pubs === 1 ? '1 publication' : pubs + ' publications'}
                </p>
                ${weak ? `<p class="font-mono text-[11px] text-accent">Thinly sourced. This thread rests on very little evidence.</p>` : ''}
            </li>
        `;
    }

    // ---------------------------------------------------------------
    // One story
    // ---------------------------------------------------------------

    function renderStory(story) {
        const container = document.getElementById('story-content');
        if (!container) return;

        const canonical = 'https://centercoopmedia.github.io/njblackpress/story.html?id=' + encodeURIComponent(story.id);
        const description = firstSentence(story.thread) || (story.title + ' — a narrative thread from the NJ Black Press Archive.');
        setMetadata(story.title + ' | NJ Black Press Archive', description, canonical);
        setBreadcrumb(story.title);

        const shown = {};
        const stops = (story.eventIds || [])
            .map(id => events[id])
            .filter(Boolean)
            .sort(byDate);

        const missingStops = (story.eventIds || []).length - stops.length;

        const stopsHtml = stops.length > 0
            ? `<ol class="space-y-10">${stops.map((e, i) => stopEntry(e, i, shown)).join('')}</ol>`
            : `<p class="measure font-sans text-paper-200">No dated events are logged for this thread yet.</p>`;

        // Any cleared clipping for a publication in this thread that no stop
        // has already carried is shown after the chronology, so nothing held
        // is silently dropped.
        const leftovers = [];
        (story.publicationIds || []).forEach(pid => {
            (clippingsByPublication[pid] || []).forEach(c => {
                if (shown[c.webPath]) return;
                shown[c.webPath] = true;
                leftovers.push(c);
            });
        });

        const pubCards = (story.publicationIds || [])
            .map(id => publications[id])
            .filter(Boolean);

        container.innerHTML = `
            <article>
                <header class="px-4 md:px-8 pt-12 md:pt-16 pb-8">
                    <div class="max-w-[1100px] mx-auto">
                        <h1 class="type-impression font-display text-4xl sm:text-5xl md:text-6xl font-extrabold leading-[0.95] tracking-normal text-paper-100 mb-4 balance">${escapeHtml(story.title)}</h1>
                        <p class="font-mono text-xs text-paper-300">
                            ${escapeHtml(formatEra(story.era) || 'era not recorded')} &middot;
                            ${stops.length === 1 ? '1 dated stop' : stops.length + ' dated stops'}${(story.people && story.people.length) ? ' &middot; ' + escapeHtml(story.people.join(', ')) : ''}
                        </p>
                        ${story.strength === 'weak' ? `
                            <p class="measure font-mono text-xs text-accent mt-4">
                                Thinly sourced. This thread rests on very little evidence and should not be read as settled.
                            </p>
                        ` : ''}
                    </div>
                </header>

                <section class="px-4 md:px-8 pb-12">
                    <div class="max-w-[1100px] mx-auto">
                        <p class="measure font-sans text-[18px] leading-[1.7] text-paper-50">${escapeHtml(story.thread || '')}</p>
                    </div>
                </section>

                <hr class="divider-stitched max-w-[1100px] mx-auto" aria-hidden="true">

                <section class="px-4 md:px-8 py-12" aria-labelledby="stops-heading">
                    <div class="max-w-[1100px] mx-auto">
                        <h2 id="stops-heading" class="font-display text-2xl font-bold text-paper-100 mb-2">Chronology</h2>
                        <hr class="rail-wood mb-8" aria-hidden="true">
                        ${stopsHtml}
                        ${missingStops > 0 ? `<p class="measure font-mono text-[11px] text-paper-300 mt-8">${missingStops === 1 ? 'One event listed for this thread is not in the event record yet.' : missingStops + ' events listed for this thread are not in the event record yet.'}</p>` : ''}
                    </div>
                </section>

                ${leftovers.length > 0 ? `
                <section class="px-4 md:px-8 py-12 bg-ink-800 border-y border-ink-600" aria-labelledby="clippings-heading">
                    <div class="max-w-[1100px] mx-auto">
                        <h2 id="clippings-heading" class="font-display text-2xl font-bold text-paper-100 mb-2">More clippings from this thread</h2>
                        <hr class="rail-wood mb-8" aria-hidden="true">
                        <div class="space-y-10">${leftovers.map(clippingFigure).join('')}</div>
                    </div>
                </section>
                ` : ''}

                <section class="px-4 md:px-8 py-12" aria-labelledby="pubs-heading">
                    <div class="max-w-[1100px] mx-auto">
                        <h2 id="pubs-heading" class="font-display text-2xl font-bold text-paper-100 mb-2">Publications in this thread</h2>
                        <hr class="rail-wood mb-8" aria-hidden="true">
                        ${pubCards.length > 0 ? `
                            <ul class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                ${pubCards.map(p => `
                                    <li class="surface-cloth bg-ink-700 border border-ink-600 p-6">
                                        <p class="font-mono text-[10px] uppercase tracking-widest text-paper-300 mb-2">${escapeHtml(p.city || 'New Jersey')}</p>
                                        <h3 class="font-display text-lg font-bold leading-snug">
                                            <a href="publication.html?id=${p.id}" class="text-paper-100 hover:text-accent transition-colors">${escapeHtml(p.name)}</a>
                                        </h3>
                                        <p class="font-mono text-xs text-paper-300 mt-2">${escapeHtml(formatYears(p))}</p>
                                        ${p.decade && p.decade !== 'Unknown' ? `<p class="font-mono text-xs mt-2"><a href="era.html?decade=${encodeURIComponent(p.decade)}" class="text-accent hover:text-paper-100 transition-colors">The ${escapeHtml(p.decade)}</a></p>` : ''}
                                    </li>
                                `).join('')}
                            </ul>
                        ` : `<p class="measure font-sans text-paper-200">No publication in the archive is linked to this thread yet.</p>`}
                    </div>
                </section>

                <section class="px-4 md:px-8 pb-16">
                    <div class="max-w-[1100px] mx-auto flex flex-wrap gap-6 font-mono text-xs">
                        <a href="story.html" class="text-accent hover:text-paper-100 transition-colors">All stories</a>
                        ${eraDecades(story.era).length > 0 ? eraDecades(story.era).map(d => `<a href="era.html?decade=${encodeURIComponent(d)}" class="text-accent hover:text-paper-100 transition-colors">The ${escapeHtml(d)}</a>`).join('') : ''}
                    </div>
                </section>
            </article>
        `;
    }

    function stopEntry(event, index, shown) {
        const pubs = (event.publicationIds || []).map(id => publications[id]).filter(Boolean);

        // Clippings for this stop's publications, each shown once per page.
        const clips = [];
        (event.publicationIds || []).forEach(pid => {
            (clippingsByPublication[pid] || []).forEach(c => {
                if (shown[c.webPath]) return;
                shown[c.webPath] = true;
                clips.push(c);
            });
        });

        return `
            <li class="border-l-2 border-ink-600 pl-5 md:pl-6">
                <p class="font-mono text-[11px] uppercase tracking-widest text-accent mb-2">${escapeHtml(formatDate(event.date))}</p>
                <h3 class="font-display text-xl md:text-2xl font-bold text-paper-100 leading-snug measure balance mb-3">${escapeHtml(event.title)}</h3>
                ${event.description ? `<p class="measure font-sans text-[17px] leading-[1.7] text-paper-200">${escapeHtml(event.description)}</p>` : ''}
                ${event.confidence === 'medium' ? `<p class="measure font-mono text-[11px] text-paper-300 mt-3">Medium confidence. The date or the detail is not fully settled.</p>` : ''}
                ${pubs.length > 0 ? `
                    <p class="font-mono text-[11px] text-paper-300 mt-3">
                        ${pubs.length === 1 ? 'Publication:' : 'Publications:'}
                        ${pubs.map(p => `<a href="publication.html?id=${p.id}" class="text-accent hover:text-paper-100 transition-colors">${escapeHtml(p.name)}</a>`).join(', ')}
                    </p>
                ` : `<p class="font-mono text-[11px] text-paper-300 mt-3">No publication in the archive is linked to this event yet.</p>`}
                ${clips.length > 0 ? `<div class="mt-6 space-y-8">${clips.map(clippingFigure).join('')}</div>` : ''}
            </li>
        `;
    }

    // ---------------------------------------------------------------
    // Clippings
    // ---------------------------------------------------------------

    function clippingFigure(clip) {
        // Guarded twice on purpose: loadData drops clippings without alt text,
        // and this renderer refuses to emit an image without it.
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

    function byDate(a, b) {
        const av = String(a.date || '');
        const bv = String(b.date || '');
        if (av === bv) return 0;
        return av < bv ? -1 : 1;
    }

    // Era strings read "1930s-1940s"; sort by the first decade, then the last.
    function compareEra(a, b) {
        const parse = v => (String(v).match(/\d{4}/g) || ['9999']).map(Number);
        const av = parse(a);
        const bv = parse(b);
        if (av[0] !== bv[0]) return av[0] - bv[0];
        return (av[av.length - 1] || 0) - (bv[bv.length - 1] || 0);
    }

    // Era strings are stored with a hyphen; ranges read with an en dash.
    function formatEra(era) {
        return String(era || '').replace(/-/g, '–');
    }

    function eraDecades(era) {
        const years = String(era || '').match(/\d{4}/g) || [];
        const out = [];
        years.forEach(y => {
            const decade = y.slice(0, 3) + '0s';
            if (out.indexOf(decade) === -1) out.push(decade);
        });
        return out;
    }

    function firstSentence(text) {
        const clean = String(text || '').trim();
        if (!clean) return '';
        // A period after a single capital letter is an initial ("Alfred P."),
        // not a sentence end. The same goes for a common honorific.
        const pattern = /[.!?](?=\s|$)/g;
        let sentence = clean;
        let match;
        while ((match = pattern.exec(clean)) !== null) {
            const before = clean.slice(0, match.index);
            if (/(^|[\s(])[A-Z]$/.test(before)) continue;
            if (/\b(Mr|Mrs|Ms|Dr|Rev|St|Jr|Sr|Col|Gen|Capt|Sgt|Prof|vs|no)$/i.test(before)) continue;
            sentence = clean.slice(0, match.index + 1);
            break;
        }
        return sentence.length > 220 ? sentence.slice(0, 200).replace(/\s\S*$/, '') + '…' : sentence;
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
        const content = document.getElementById('story-content');
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
