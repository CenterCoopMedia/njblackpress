/**
 * NJ Black Press Database - Publication Detail Page
 * Loads and displays individual publication records
 */

(function() {
    'use strict';

    let allPublications = [];
    let featuredPublications = { historic: [], contemporary: [] };
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
            // Load both data sources in parallel
            const [pubResponse, featuredResponse] = await Promise.all([
                fetch('data/publications.json'),
                fetch('data/featured-publications.json')
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
        } catch (error) {
            console.error('Failed to load publication data:', error);
        }
    }

    function findPublication(id) {
        // Check featured publications first (they have richer data)
        let pub = featuredPublications.historic.find(p => p.id === id);
        if (pub) return { ...pub, _source: 'featured-historic' };

        pub = featuredPublications.contemporary.find(p => p.id === id);
        if (pub) return { ...pub, _source: 'featured-contemporary' };

        // Fall back to main publications list
        pub = allPublications.find(p => p.id === id);
        if (pub) return { ...pub, _source: 'main' };

        return null;
    }

    function renderPublication(pub) {
        const container = document.getElementById('publication-content');
        if (!container) return;

        // Update page title
        document.getElementById('page-title').textContent = `${pub.name} | NJ Black Press Archive`;
        document.title = `${pub.name} | NJ Black Press Archive`;

        const statusClass = pub.isActive !== false && !pub.yearCeased ? 'text-accent border-accent' : 'text-paper-300 border-paper-300';
        const statusText = pub.isActive !== false && !pub.yearCeased ? 'ACTIVE' : 'ARCHIVED';
        const years = formatYears(pub);

        // Build sections
        const missionSection = pub.missionStatement ? buildMissionSection(pub.missionStatement) : '';
        const metadataSection = buildMetadataSection(pub);
        const historicalSection = pub.historicalNotes ? buildHistoricalSection(pub.historicalNotes) : '';
        const peopleSection = buildPeopleSection(pub);
        const tagsSection = buildTagsSection(pub);
        const archiveSection = buildArchiveSection(pub);
        const relatedSection = buildRelatedSection(pub);

        container.innerHTML = `
            <!-- Hero Section -->
            <section class="relative bg-ink-950 border-b border-white/10 py-16 md:py-24 px-4 md:px-8">
                <div class="max-w-[1400px] mx-auto">

                    <!-- Decorative corner elements -->
                    <div class="absolute top-8 left-8 w-16 h-16 border-l-2 border-t-2 border-accent/30 hidden lg:block"></div>
                    <div class="absolute top-8 right-8 w-16 h-16 border-r-2 border-t-2 border-accent/30 hidden lg:block"></div>

                    <div class="animate-in delay-1">
                        <div class="flex flex-wrap items-center gap-4 mb-6">
                            <span class="font-mono text-xs uppercase tracking-widest px-3 py-1 border ${statusClass}">${statusText}</span>
                            ${pub.alternateName ? `<span class="font-mono text-xs text-paper-300">Also known as: ${escapeHtml(pub.alternateName)}</span>` : ''}
                        </div>
                    </div>

                    <h1 class="font-serif text-5xl md:text-7xl lg:text-8xl font-black leading-[0.9] tracking-tighter text-paper-100 mb-6 animate-in delay-2">
                        ${escapeHtml(pub.name)}
                    </h1>

                    <div class="flex flex-wrap items-center gap-6 text-paper-300 animate-in delay-3">
                        <div class="flex items-center gap-2">
                            <svg class="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                            </svg>
                            <span class="font-serif text-xl">${escapeHtml(pub.city || 'New Jersey')}</span>
                        </div>
                        <span class="text-white/30">|</span>
                        <span class="font-mono text-sm tracking-wide">${years}</span>
                    </div>

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
        return `
            <section class="bg-ink-800 border-y border-white/10 py-12 md:py-16 px-4 md:px-8 animate-in delay-4">
                <div class="max-w-[1000px] mx-auto">
                    <p class="font-mono text-xs text-accent uppercase tracking-widest mb-4">Mission Statement</p>
                    <blockquote class="pull-quote font-serif text-2xl md:text-3xl lg:text-4xl text-paper-100 leading-relaxed font-light italic">
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
                <h2 class="font-mono text-xs text-accent uppercase tracking-widest mb-6 pb-2 border-b border-white/10">Publication Details</h2>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-6">
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

    function buildHistoricalSection(notes) {
        // Split into paragraphs if long
        const paragraphs = notes.split(/\n\n|\. (?=[A-Z])/g).filter(p => p.trim());

        return `
            <div class="animate-in delay-5">
                <h2 class="font-mono text-xs text-accent uppercase tracking-widest mb-6 pb-2 border-b border-white/10">Historical Notes</h2>
                <div class="prose prose-invert max-w-none">
                    ${paragraphs.length > 1 ? `
                        <div class="md:columns-2 gap-8 column-rule space-y-4">
                            ${paragraphs.map((p, i) => `
                                <p class="${i === 0 ? 'drop-cap' : ''} font-serif text-lg text-paper-200 leading-relaxed">${escapeHtml(p.trim())}${!p.trim().endsWith('.') ? '.' : ''}</p>
                            `).join('')}
                        </div>
                    ` : `
                        <p class="drop-cap font-serif text-lg text-paper-200 leading-relaxed">${escapeHtml(notes)}</p>
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
                <h3 class="font-serif text-xl font-bold mb-6 text-center border-b border-white/10 pb-4">
                    <span class="ornament">Masthead</span>
                </h3>

                <div class="space-y-6">
                    ${founders.length > 0 ? `
                        <div class="masthead-entry pb-4">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Founder${founders.length > 1 ? 's' : ''}</p>
                            ${founders.map(f => `<p class="font-serif text-lg text-center text-paper-100">${escapeHtml(f)}</p>`).join('')}
                        </div>
                    ` : ''}

                    ${publishers.length > 0 ? `
                        <div class="masthead-entry pb-4">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Publisher${publishers.length > 1 ? 's' : ''}</p>
                            ${publishers.map(p => `<p class="font-serif text-lg text-center text-paper-100">${escapeHtml(p)}</p>`).join('')}
                        </div>
                    ` : ''}

                    ${staff.length > 0 ? `
                        <div class="space-y-3">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Key Staff</p>
                            ${staff.map(s => `
                                <div class="text-center">
                                    <p class="font-serif text-paper-100">${escapeHtml(s.name)}</p>
                                    <p class="font-mono text-xs text-paper-300">${escapeHtml(s.role)}</p>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    ${staffString ? `
                        <div class="masthead-entry pb-4">
                            <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-2 text-center">Key Staff</p>
                            <p class="font-serif text-lg text-center text-paper-100">${escapeHtml(staffString)}</p>
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
                <h3 class="font-mono text-xs text-accent uppercase tracking-widest mb-4">Topics & Tags</h3>
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

    function buildArchiveSection(pub) {
        // Only treat archiveUrl as a link if it starts with http
        const hasValidArchiveUrl = pub.archiveUrl && pub.archiveUrl.startsWith('http');
        // If archiveUrl exists but isn't a URL, treat it as a catalog reference
        const hasCatalogRef = pub.archiveUrl && !pub.archiveUrl.startsWith('http');

        const hasArchive = hasValidArchiveUrl || hasCatalogRef || pub.physicalArchive || pub.websiteUrl;
        if (!hasArchive) return '';

        return `
            <div class="bg-ink-950 border border-accent/30 p-6 animate-in delay-6">
                <h3 class="font-mono text-xs text-accent uppercase tracking-widest mb-4">Access & Archives</h3>
                <div class="space-y-4">
                    ${pub.websiteUrl ? `
                        <a href="${pub.websiteUrl}" target="_blank" rel="noopener"
                           class="flex items-center gap-3 text-paper-100 hover:text-accent transition-colors group">
                            <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
                            </svg>
                            <span class="font-sans group-hover:underline">Visit Website</span>
                            <span class="text-accent ml-auto">&rarr;</span>
                        </a>
                    ` : ''}

                    ${hasValidArchiveUrl ? `
                        <a href="${pub.archiveUrl}" target="_blank" rel="noopener"
                           class="flex items-center gap-3 text-paper-100 hover:text-accent transition-colors group">
                            <svg class="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"/>
                            </svg>
                            <span class="font-sans group-hover:underline">Digital Archive</span>
                            <span class="text-accent ml-auto">&rarr;</span>
                        </a>
                    ` : ''}

                    ${hasCatalogRef ? `
                        <div class="flex items-start gap-3 text-paper-300">
                            <svg class="w-5 h-5 text-accent mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                            </svg>
                            <div>
                                <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-1">Catalog Reference</p>
                                <p class="font-sans text-sm text-paper-200">${escapeHtml(pub.archiveUrl)}</p>
                            </div>
                        </div>
                    ` : ''}

                    ${pub.physicalArchive ? `
                        <div class="flex items-start gap-3 text-paper-300">
                            <svg class="w-5 h-5 text-accent mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                            </svg>
                            <div>
                                <p class="font-mono text-[10px] uppercase tracking-widest text-accent mb-1">Physical Archive</p>
                                <p class="font-sans text-sm text-paper-200">${escapeHtml(pub.physicalArchive)}</p>
                            </div>
                        </div>
                    ` : ''}
                </div>
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
                    <h2 class="font-serif text-2xl font-bold mb-8">Related Publications</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        ${related.map(r => `
                            <a href="publication.html?id=${r.id}"
                               class="block bg-ink-900 border border-white/10 hover:border-accent p-6 transition-colors group">
                                <p class="font-mono text-[10px] uppercase tracking-widest text-paper-300 mb-2">${escapeHtml(r.city || 'NJ')}</p>
                                <h3 class="font-serif text-lg font-bold group-hover:text-accent transition-colors">${escapeHtml(r.name)}</h3>
                                <p class="font-mono text-xs text-paper-300 mt-2">${formatYears(r)}</p>
                            </a>
                        `).join('')}
                    </div>
                </div>
            </section>
        `;
    }

    function formatYears(pub) {
        if (!pub.yearFounded) return 'Dates unknown';
        if (pub.yearCeased) return `${pub.yearFounded} — ${pub.yearCeased}`;
        if (pub.isActive === false) return `${pub.yearFounded} — Ceased`;
        return `${pub.yearFounded} — Present`;
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

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
