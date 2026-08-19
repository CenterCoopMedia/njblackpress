/**
 * NJ Black Press Database - Publication Detail Page
 * Loads and displays individual publication records
 */

(function() {
    'use strict';

    let allPublications = [];
    let featuredPublications = { historic: [], contemporary: [] };
    let clippingsBySourcePath = {};
    let currentPublication = null;

    async function init() {
        const id = getPublicationId();
        if (!id) {
            showError();
            return;
        }

        await loadData();

        currentPublication = findPublication(id);

        if (!currentPublication) {
            showError();
            return;
        }

        renderPublication(currentPublication);
        hideLoadingOverlay();
    }

    function getPublicationId() {
        const params = new URLSearchParams(window.location.search);
        const id = params.get('id');
        return id ? parseInt(id, 10) : null;
    }

    async function loadData() {
        try {
            // Load all three data sources in parallel
            const [pubResponse, featuredResponse, clippingsResponse] = await Promise.all([
                fetch('data/publications.json'),
                fetch('data/featured-publications.json'),
                fetch('data/clippings.json').catch(() => null)
            ]);

            if (pubResponse.ok) {
                const data = await pubResponse.json();
                allPublications = data.publications || [];
            }

            if (featuredResponse.ok) {
                const featured = await featuredResponse.json();
                featuredPublications.historic = featured.featuredHistoric || [];
                featuredPublications.contemporary = featured.featuredContemporary || [];
            }

            // clippings.json is the ONLY source of publishable evidence images.
            // Evidence 'file' paths are unpublished research scans and must
            // never be rendered as image sources.
            if (clippingsResponse && clippingsResponse.ok) {
                const clipData = await clippingsResponse.json();
                (clipData.clippings || []).forEach(c => {
                    if (c.sourcePath && c.webPath) clippingsBySourcePath[c.sourcePath] = c;
                });
            }
        } catch (error) {
            console.error('Failed to load publication data:', error);
        }
    }

    function findPublication(id) {
        const base = allPublications.find(p => p.id === id) || null;

        // Featured records carry richer curated fields but are missing the
        // evidence array, websiteUrl and computed fields. Merge them onto the
        // main record so every publication renders the same sections.
        const historic = featuredPublications.historic.find(p => p.id === id);
        if (historic) return mergeRecords(base, historic, 'featured-historic');

        const contemporary = featuredPublications.contemporary.find(p => p.id === id);
        if (contemporary) return mergeRecords(base, contemporary, 'featured-contemporary');

        if (base) return { ...base, _source: 'main' };

        return null;
    }

    function mergeRecords(base, overlay, source) {
        const merged = { ...(base || {}) };
        Object.keys(overlay).forEach(key => {
            const value = overlay[key];
            if (value === null || value === undefined || value === '') return;
            if (Array.isArray(value) && value.length === 0) return;
            merged[key] = value;
        });
        merged.evidence = (base && base.evidence) || [];
        // The wiki filename is built from the publications.json name, which can
        // differ from the curated featured name ("The Newark Herald" vs
        // "Newark Herald"). Keep the canonical name so the slug still resolves.
        merged._canonicalName = (base && base.name) || overlay.name;
        merged._source = source;
        return merged;
    }

    function renderPublication(pub) {
        const container = document.getElementById('publication-content');
        if (!container) return;

        // Update page title
        document.getElementById('page-title').textContent = `${pub.name} | NJ Black Press Archive`;
        document.title = `${pub.name} | NJ Black Press Archive`;

        // Update meta tags for per-publication SEO
        const metaYears = pub.yearFounded ? (pub.yearCeased ? `${pub.yearFounded}–${pub.yearCeased}` : `Est. ${pub.yearFounded}`) : '';
        const location = pub.city ? `${pub.city}, NJ` : 'New Jersey';
        const cleanNotes = pub.historicalNotes ? stripResearchAnnotations(pub.historicalNotes) : '';
        const ogDesc = cleanNotes
            ? cleanNotes.slice(0, 155).replace(/\s\S*$/, '') + '...'
            : pub.missionStatement
                ? pub.missionStatement.slice(0, 155).replace(/\s\S*$/, '') + '...'
                : `${pub.name} — ${location}${metaYears ? ' • ' + metaYears : ''}. From the NJ Black Press Archive.`;
        const canonicalUrl = `https://centercoopmedia.github.io/njblackpress/publication.html?id=${pub.id}`;

        const setMeta = (id, val) => { const el = document.getElementById(id); if (el) el.setAttribute('content', val); };
        setMeta('meta-description', ogDesc);
        setMeta('og-title', `${pub.name} | NJ Black Press Archive`);
        setMeta('og-description', ogDesc);
        setMeta('og-url', canonicalUrl);
        setMeta('twitter-title', `${pub.name} | NJ Black Press Archive`);
        setMeta('twitter-description', ogDesc);
        const canonical = document.getElementById('canonical');
        if (canonical) canonical.setAttribute('href', canonicalUrl);

        const years = formatYears(pub);

        // Build sections
        const missionSection = pub.missionStatement ? buildMissionSection(pub.missionStatement) : '';
        const metadataSection = buildMetadataSection(pub);
        const historicalSection = buildHistoricalSection(pub);
        const evidenceSection = buildEvidenceSection(pub);
        const peopleSection = buildPeopleSection(pub);
        const tagsSection = buildTagsSection(pub);
        const archiveSection = buildArchiveSection(pub);
        const relatedSection = buildRelatedSection(pub);
        const altName = classifyAlternateName(pub.alternateName);

        container.innerHTML = `
            <!-- Hero Section -->
            <section class="relative bg-ink-950 border-b border-white/10 py-16 md:py-24 px-4 md:px-8">
                <div class="max-w-[1400px] mx-auto">

                    <!-- Decorative corner elements -->
                    <div class="absolute top-8 left-8 w-16 h-16 border-l-2 border-t-2 border-accent/30 hidden lg:block"></div>
                    <div class="absolute top-8 right-8 w-16 h-16 border-r-2 border-t-2 border-accent/30 hidden lg:block"></div>

                    ${altName && !altName.isFate ? `
                    <div class="animate-in delay-1">
                        <p class="font-mono text-xs text-paper-300 mb-6">${escapeHtml(altName.label)} ${escapeHtml(altName.value)}</p>
                    </div>
                    ` : ''}

                    <h1 class="type-impression font-display text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold leading-[0.88] tracking-normal text-paper-100 mb-6 animate-in delay-2">
                        ${escapeHtml(pub.name)}
                    </h1>

                    <div class="flex flex-wrap items-center gap-6 text-paper-300 animate-in delay-3">
                        <div class="flex items-center gap-2">
                            <svg class="w-4 h-4 text-accent" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                            <span class="font-display text-xl">${escapeHtml(pub.city || 'New Jersey')}</span>
                        </div>
                        <span class="text-white/30">|</span>
                        <span class="font-mono text-sm tracking-wide">${years}</span>
                    </div>

                    <p class="mt-8 animate-in delay-3">
                        <a href="${wikiHref(pub)}"
                           class="inline-block font-mono text-xs uppercase tracking-widest text-accent hover:text-paper-100 transition-colors border-b border-accent/40 hover:border-paper-100 py-1">
                            Wiki page for this title <span aria-hidden="true">&rarr;</span>
                        </a>
                    </p>

                </div>
            </section>

            ${missionSection}

            <!-- Main Content Grid -->
            <section class="py-16 md:py-20 px-4 md:px-8 bg-ink-900">
                <div class="max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16">

                    <!-- Main Column -->
                    <div class="lg:col-span-8 space-y-12">
                        ${metadataSection}
                        ${historicalSection}
                        ${evidenceSection}
                    </div>

                    <!-- Sidebar -->
                    <aside class="lg:col-span-4 space-y-8">
                        ${peopleSection}
                        ${tagsSection}
                        ${archiveSection}
                    </aside>

                </div>
            </section>

            ${relatedSection}
        `;
    }

    function buildMissionSection(mission) {
        // The blockquote already draws an opening quote mark via CSS, so a
        // literal wrapping quote in the data would render twice.
        mission = stripWrappingQuotes(mission);
        if (!mission) return '';

        return `
            <section class="bg-ink-800 border-y border-white/10 py-12 md:py-16 px-4 md:px-8 animate-in delay-4">
                <div class="max-w-[1000px] mx-auto">
                    <h2 class="font-mono text-xs text-accent uppercase tracking-widest mb-4">Mission statement</h2>
                    <blockquote class="pull-quote font-sans text-xl sm:text-2xl md:text-3xl text-paper-100 leading-relaxed font-light italic">
                        ${escapeHtml(mission)}
                    </blockquote>
                </div>
            </section>
        `;
    }

    function buildMetadataSection(pub) {
        const items = [];

        if (pub.frequency) items.push({ label: 'Frequency', value: pub.frequency });
        if (pub.format) items.push({ label: 'Format', value: pub.format });
        if (pub.medium) items.push({ label: 'Medium', value: pub.medium });
        if (pub.languages) {
            const langs = Array.isArray(pub.languages) ? pub.languages.join(', ') : pub.languages;
            items.push({ label: 'Language', value: langs });
        }
        if (pub.primaryFocus) items.push({ label: 'Focus', value: pub.primaryFocus });

        if (items.length === 0) return '';

        return `
            <div class="animate-in delay-4">
                <h2 class="font-mono text-xs text-accent uppercase tracking-widest mb-6 pb-2 border-b border-white/10">Publication details</h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                    ${items.map(item => `
                        <div class="border-l-2 border-white/10 pl-4">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-paper-300 mb-1">${item.label}</p>
                            <p class="font-sans text-paper-100">${escapeHtml(item.value)}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    function stripResearchAnnotations(text) {
        // Remove [March 2026 research: ...] and [March 2026 research (estimated): ...] annotations
        // These are for the raw data, not for display
        return text.replace(/\s*\[March 2026 research(?:\s*\(estimated\))?\s*:\s*[^\]]*\]/g, '').trim();
    }

    function stripWrappingQuotes(text) {
        if (!text) return '';
        let out = String(text).trim();
        // Strip one matched pair of straight or curly quotes wrapping the whole string
        const pairs = [['"', '"'], ['“', '”'], ["'", "'"], ['‘', '’']];
        for (const [open, close] of pairs) {
            if (out.length > 1 && out.startsWith(open) && out.endsWith(close)) {
                out = out.slice(open.length, out.length - close.length).trim();
                break;
            }
        }
        return out;
    }

    // Values in alternateName that describe what happened to a title rather
    // than naming it (for example "Absorbed by the New Jersey Herald News,
    // 1939") must not be labelled "Also known as".
    const FATE_PATTERN = /^\s*(absorbed|merged|continued|succeeded|superseded|became|renamed|replaced|split|incorporated|folded|ceased|acquired|published as part)\b/i;

    function classifyAlternateName(value) {
        const text = value ? String(value).trim() : '';
        if (!text) return null;
        if (FATE_PATTERN.test(text)) {
            return { label: 'Publication history:', value: text, isFate: true };
        }
        return { label: 'Also known as', value: text, isFate: false };
    }

    function buildHistoricalSection(pub) {
        let notes = stripResearchAnnotations(pub.historicalNotes || '');
        const altName = classifyAlternateName(pub.alternateName);

        // Split only on actual paragraph breaks (double newlines), not sentence boundaries
        const paragraphs = notes.split(/\n\n+/).filter(p => p.trim());
        if (altName && altName.isFate) paragraphs.push(altName.value);
        if (paragraphs.length === 0) return '';
        notes = paragraphs.join('\n\n');

        // Use multi-column layout for longer text
        const useColumns = notes.length > 500;

        return `
            <div class="animate-in delay-5">
                <h2 class="font-mono text-xs text-accent uppercase tracking-widest mb-6 pb-2 border-b border-white/10">Historical notes</h2>
                <div class="prose prose-invert max-w-none">
                    ${useColumns ? `
                        <div class="columns-1 md:columns-2 gap-8 column-rule space-y-4">
                            ${paragraphs.map((p, i) => `
                                <p class="${i === 0 ? 'drop-cap' : ''} font-sans text-lg text-paper-200 leading-relaxed">${escapeHtml(p.trim())}</p>
                            `).join('')}
                        </div>
                    ` : `
                        ${paragraphs.map((p, i) => `
                            <p class="${i === 0 ? 'drop-cap' : ''} font-sans text-lg text-paper-200 leading-relaxed">${escapeHtml(p.trim())}</p>
                        `).join('')}
                    `}
                </div>
            </div>
        `;
    }

    function buildPeopleSection(pub) {
        const founders = pub.founders || [];
        const publishers = pub.publishers ? (Array.isArray(pub.publishers) ? pub.publishers : [pub.publishers]) : [];

        // Handle keyStaff as either an array of objects or a string
        let staff = [];
        let staffString = null;
        if (pub.keyStaff) {
            if (Array.isArray(pub.keyStaff)) {
                staff = pub.keyStaff;
            } else if (typeof pub.keyStaff === 'string') {
                staffString = pub.keyStaff;
            }
        }

        if (founders.length === 0 && publishers.length === 0 && staff.length === 0 && !staffString) {
            return '';
        }

        return `
            <div class="bg-ink-800 border border-white/10 p-6 animate-in delay-5">
                <h3 class="font-display text-xl font-bold mb-6 text-center border-b border-white/10 pb-4">
                    <span class="ornament-mark" aria-hidden="true">~</span><span>Masthead</span><span class="ornament-mark" aria-hidden="true">~</span>
                </h3>

                <div class="space-y-6">
                    ${founders.length > 0 ? `
                        <div class="masthead-entry pb-4">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Founder${founders.length > 1 ? 's' : ''}</p>
                            ${founders.map(f => `<p class="font-display text-lg text-center text-paper-100">${escapeHtml(f)}</p>`).join('')}
                        </div>
                    ` : ''}

                    ${publishers.length > 0 ? `
                        <div class="masthead-entry pb-4">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Publisher${publishers.length > 1 ? 's' : ''}</p>
                            ${publishers.map(p => `<p class="font-display text-lg text-center text-paper-100">${escapeHtml(p)}</p>`).join('')}
                        </div>
                    ` : ''}

                    ${staff.length > 0 ? `
                        <div class="space-y-3">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Key staff</p>
                            ${staff.map(s => `
                                <div class="text-center">
                                    <p class="font-display text-paper-100">${escapeHtml(s.name)}</p>
                                    <p class="font-mono text-xs text-paper-300">${escapeHtml(s.role)}</p>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    ${staffString ? `
                        <div class="masthead-entry pb-4">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Key staff</p>
                            <p class="font-display text-lg text-center text-paper-100">${escapeHtml(staffString)}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    function buildTagsSection(pub) {
        const tags = pub.tags || [];
        if (tags.length === 0) return '';

        return `
            <div class="animate-in delay-6">
                <h3 class="font-mono text-xs text-accent uppercase tracking-widest mb-4">Topics and tags</h3>
                <div class="flex flex-wrap gap-2">
                    ${tags.map(tag => `
                        <a href="archive.html?search=${encodeURIComponent(tag)}"
                           class="px-3 py-1 bg-ink-800 border border-white/10 hover:border-accent hover:text-accent text-paper-300 text-sm font-mono transition-colors">
                            ${escapeHtml(tag)}
                        </a>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // ---------------------------------------------------------------
    // Provenance helpers
    // ---------------------------------------------------------------

    // Display names carry their article so link text reads as a destination:
    // "View at the Library of Congress", not "View at Library of Congress".
    const HOST_LABELS = {
        'loc.gov': 'the Library of Congress',
        'chroniclingamerica.loc.gov': 'the Library of Congress',
        'archive.org': 'the Internet Archive',
        'web.archive.org': 'the Wayback Machine',
        'newspapers.com': 'Newspapers.com',
        'worldcat.org': 'WorldCat',
        'search.worldcat.org': 'WorldCat',
        'hathitrust.org': 'HathiTrust',
        'babel.hathitrust.org': 'HathiTrust',
        'marxists.org': 'the Marxists Internet Archive',
        'libcom.org': 'libcom.org',
        'nyshistoricnewspapers.org': 'NYS Historic Newspapers'
    };

    function hostLabel(url) {
        if (!url) return '';
        let host;
        try {
            host = new URL(url).hostname.toLowerCase();
        } catch (e) {
            return '';
        }
        if (HOST_LABELS[host]) return HOST_LABELS[host];
        const bare = host.replace(/^www\./, '');
        if (HOST_LABELS[bare]) return HOST_LABELS[bare];
        // Try the registrable-looking tail (example: cdn.archive.org -> archive.org)
        const parts = bare.split('.');
        if (parts.length > 2) {
            const tail = parts.slice(-2).join('.');
            if (HOST_LABELS[tail]) return HOST_LABELS[tail];
        }
        return bare;
    }

    // Plain-language rights note. Only 'publishable' and
    // 'publishable_with_credit' carry a reuse statement; every other status
    // shows its citation alone.
    function rightsNote(status) {
        switch (status) {
            case 'publishable':
                return 'Public domain, free to reuse.';
            case 'publishable_with_credit':
                return 'Free to reuse with credit.';
            default:
                return '';
        }
    }

    function isUrl(value) {
        return typeof value === 'string' && /^https?:\/\//i.test(value.trim());
    }

    // Mirrors slugify() in scripts/generate_okf_wiki.py, which the HTML wiki
    // generator reuses to name docs/wiki/publications/NNN-slug.html
    function slugify(value, fallback) {
        const text = String(value || '')
            .toLowerCase()
            .replace(/&/g, ' and ')
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '');
        return text || (fallback || 'item');
    }

    function wikiHref(pub) {
        const id = String(pub.id).padStart(3, '0');
        return 'wiki/publications/' + id + '-' + slugify(pub._canonicalName || pub.name) + '.html';
    }

    // ---------------------------------------------------------------
    // Evidence
    // ---------------------------------------------------------------

    function buildEvidenceSection(pub) {
        const evidence = Array.isArray(pub.evidence) ? pub.evidence : [];
        if (evidence.length === 0) return '';

        const withImage = [];
        const textOnly = [];

        evidence.forEach(item => {
            const clip = clippingsBySourcePath[item.file];
            // RIGHTS RULE: an evidence item may show an image only when
            // clippings.json publishes it for this publication. The evidence
            // 'file' path is an unpublished research scan and is never used
            // as an image source.
            if (clip && Array.isArray(clip.publicationIds) && clip.publicationIds.indexOf(pub.id) !== -1) {
                withImage.push({ item: item, clip: clip });
            } else {
                textOnly.push(item);
            }
        });

        const figures = withImage.map(entry => {
            const item = entry.item;
            const clip = entry.clip;
            const caption = clip.caption || item.caption || '';
            const citation = clip.citation || item.citation || '';
            const note = rightsNote(clip.status || item.rightsStatus);
            const label = hostLabel(item.url);
            return `
                <figure class="evidence-figure bg-ink-800 border border-white/10 flex flex-col">
                    <img src="${escapeAttr(clip.webPath)}"
                         alt="${escapeAttr(clip.alt || caption)}"
                         ${clip.width ? `width="${clip.width}"` : ''} ${clip.height ? `height="${clip.height}"` : ''}
                         loading="lazy" decoding="async">
                    <figcaption class="p-4 grow flex flex-col gap-2">
                        ${caption ? `<p class="measure font-sans text-sm text-paper-200 leading-relaxed">${escapeHtml(caption)}</p>` : ''}
                        <div class="mt-auto space-y-1">
                            ${citation ? `<p class="measure font-mono text-[11px] text-paper-300 leading-relaxed"><cite class="not-italic" title="${escapeAttr(citation)}">${escapeHtml(citation)}</cite></p>` : ''}
                            ${note ? `<p class="measure font-mono text-[11px] text-paper-300/80">${escapeHtml(note)}</p>` : ''}
                            ${isUrl(item.url) ? `<p class="font-mono text-[11px]"><a href="${escapeAttr(item.url)}" target="_blank" rel="noopener noreferrer" class="text-accent hover:text-paper-100 transition-colors">View at ${escapeHtml(label)} <span aria-hidden="true">&nearr;</span></a></p>` : ''}
                        </div>
                    </figcaption>
                </figure>
            `;
        }).join('');

        const records = textOnly.map(item => {
            const note = rightsNote(item.rightsStatus);
            const label = hostLabel(item.url);
            return `
                <li class="border-l-2 border-white/10 pl-4 py-1 space-y-1">
                    ${item.caption ? `<p class="measure font-sans text-sm text-paper-200 leading-relaxed">${escapeHtml(item.caption)}</p>` : ''}
                    ${item.citation ? `<p class="measure font-mono text-[11px] text-paper-300 leading-relaxed"><cite class="not-italic" title="${escapeAttr(item.citation)}">${escapeHtml(item.citation)}</cite></p>` : ''}
                    ${note ? `<p class="measure font-mono text-[11px] text-paper-300/80">${escapeHtml(note)}</p>` : ''}
                    ${isUrl(item.url) ? `<p class="font-mono text-[11px]"><a href="${escapeAttr(item.url)}" target="_blank" rel="noopener noreferrer" class="text-accent hover:text-paper-100 transition-colors">View at ${escapeHtml(label)} <span aria-hidden="true">&nearr;</span></a></p>` : ''}
                </li>
            `;
        }).join('');

        const count = evidence.length;
        const summary = (count === 1 ? '1 source record supports this entry.' : count + ' source records support this entry.')
            + (withImage.length === 0 ? ' No image from these sources is cleared for publication, so they are listed as citations.' : '');

        return `
            <div class="animate-in delay-5">
                <h2 class="balance font-mono text-xs text-accent uppercase tracking-widest mb-6 pb-2 border-b border-white/10">Evidence</h2>
                <p class="measure font-mono text-[11px] text-paper-300 mb-6">${escapeHtml(summary)}</p>
                ${figures ? `<div class="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">${figures}</div>` : ''}
                ${records ? `<ul class="space-y-5">${records}</ul>` : ''}
            </div>
        `;
    }

    // ---------------------------------------------------------------
    // Access, archives, rights and citation
    // ---------------------------------------------------------------

    function buildArchiveSection(pub) {
        const archiveRaw = pub.archiveUrl ? String(pub.archiveUrl).trim() : '';
        const hasArchiveLink = isUrl(archiveRaw);
        // 85 of 136 records hold a catalog string here, not a URL. Print those
        // as a labelled identifier rather than a broken link.
        const catalogRef = archiveRaw && !hasArchiveLink ? archiveRaw : '';
        const hasWebsite = isUrl(pub.websiteUrl);

        // Distinct citations across the evidence array, each with its rights note.
        const seen = {};
        const citations = [];
        (Array.isArray(pub.evidence) ? pub.evidence : []).forEach(item => {
            const text = (item.citation || '').trim();
            if (!text || seen[text]) return;
            seen[text] = true;
            citations.push({ text: text, note: rightsNote(item.rightsStatus) });
        });

        const nothingToShow = !hasArchiveLink && !catalogRef && !hasWebsite && !pub.physicalArchive;

        return `
            <div class="bg-ink-950 border border-accent/30 p-6 animate-in delay-6">
                <h3 class="balance font-mono text-xs text-accent uppercase tracking-widest mb-4">Access and archives</h3>
                <div class="space-y-4">
                    ${hasWebsite ? `
                        <a href="${escapeAttr(pub.websiteUrl)}" target="_blank" rel="noopener noreferrer"
                           class="flex items-center gap-3 text-paper-100 hover:text-accent transition-colors group">
                            <svg class="w-5 h-5 text-accent shrink-0" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
                            </svg>
                            <span class="font-sans group-hover:underline">Read at ${escapeHtml(hostLabel(pub.websiteUrl))}</span>
                            <span class="text-accent ml-auto" aria-hidden="true">&rarr;</span>
                        </a>
                    ` : ''}

                    ${hasArchiveLink ? `
                        <a href="${escapeAttr(archiveRaw)}" target="_blank" rel="noopener noreferrer"
                           class="flex items-center gap-3 text-paper-100 hover:text-accent transition-colors group">
                            <svg class="w-5 h-5 text-accent shrink-0" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                            </svg>
                            <span class="font-sans group-hover:underline">Archive record at ${escapeHtml(hostLabel(archiveRaw))}</span>
                            <span class="text-accent ml-auto" aria-hidden="true">&rarr;</span>
                        </a>
                    ` : ''}

                    ${catalogRef ? `
                        <div class="flex items-start gap-3 text-paper-300">
                            <svg class="w-5 h-5 text-accent mt-0.5 shrink-0" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                            </svg>
                            <div class="min-w-0">
                                <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-1">Library catalog record</p>
                                <p class="measure font-mono text-sm text-paper-200 break-words" title="${escapeAttr(catalogRef)}">${escapeHtml(catalogRef)}</p>
                            </div>
                        </div>
                    ` : ''}

                    ${pub.physicalArchive ? `
                        <div class="flex items-start gap-3 text-paper-300">
                            <svg class="w-5 h-5 text-accent mt-0.5 shrink-0" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                            </svg>
                            <div class="min-w-0">
                                <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-1">Physical archive</p>
                                <p class="measure font-sans text-sm text-paper-200">${escapeHtml(pub.physicalArchive)}</p>
                            </div>
                        </div>
                    ` : ''}

                    ${nothingToShow ? `
                        <p class="measure font-sans text-sm text-paper-300">No digital or physical archive has been located for this title yet.</p>
                    ` : ''}
                </div>

                ${citations.length > 0 ? `
                    <div class="mt-6 pt-4 border-t border-white/10">
                        <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-3">How to cite</p>
                        <ul class="space-y-3">
                            ${citations.map(c => `
                                <li>
                                    <p class="measure font-mono text-[11px] text-paper-200 leading-relaxed"><cite class="not-italic" title="${escapeAttr(c.text)}">${escapeHtml(c.text)}</cite></p>
                                    ${c.note ? `<p class="measure font-mono text-[11px] text-paper-300/80">${escapeHtml(c.note)}</p>` : ''}
                                </li>
                            `).join('')}
                        </ul>
                        <p class="measure font-mono text-[11px] text-paper-300/80 mt-3">Where no reuse note appears, cite the source and ask the holding institution for permission.</p>
                    </div>
                ` : ''}
            </div>
        `;
    }

    function buildRelatedSection(pub) {
        // Find related publications (same city or overlapping era)
        const related = allPublications.filter(p => {
            if (p.id === pub.id) return false;
            // Same city
            if (p.city && pub.city && p.city === pub.city) return true;
            // Same decade
            if (p.decade && pub.decade && p.decade === pub.decade) return true;
            return false;
        }).slice(0, 4);

        if (related.length === 0) return '';

        return `
            <section class="bg-ink-950 border-t border-white/10 py-16 px-4 md:px-8">
                <div class="max-w-[1400px] mx-auto">
                    <h2 class="font-display text-2xl font-bold mb-8">Related publications</h2>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        ${related.map(r => `
                            <a href="publication.html?id=${r.id}"
                               class="block bg-ink-900 border border-white/10 hover:border-accent p-6 transition-colors group">
                                <p class="font-mono text-[10px] uppercase tracking-widest text-paper-300 mb-2">${escapeHtml(r.city || 'NJ')}</p>
                                <h3 class="font-display text-lg font-bold group-hover:text-accent transition-colors">${escapeHtml(r.name)}</h3>
                                <p class="font-mono text-xs text-paper-300 mt-2">${formatYears(r)}</p>
                            </a>
                        `).join('')}
                    </div>
                </div>
            </section>
        `;
    }

    function formatYears(pub) {
        if (!pub.yearFounded) return pub.isActive === false ? 'ceased, dates unknown' : 'dates unknown';
        if (pub.yearCeased) return `${pub.yearFounded}–${pub.yearCeased}`;
        if (pub.isActive === false) return `founded ${pub.yearFounded}, ceased`;
        return `${pub.yearFounded}–present`;
    }

    function showError() {
        hideLoadingOverlay();
        document.getElementById('publication-content').classList.add('hidden');
        document.getElementById('error-state').classList.remove('hidden');
    }

    function hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('opacity-0');
            setTimeout(() => overlay.classList.add('hidden'), 500);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // Attribute-safe escaping: escapeHtml leaves quotes intact, which is fine
    // for text nodes but not for src/href/alt values.
    function escapeAttr(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
