/**
 * NJ Black Press Database - Archive Page
 * Full directory with advanced filtering, sorting, and view modes
 */

(function() {
    'use strict';

    // State
    const state = {
        publications: [],
        filtered: [],
        filters: {
            search: '',
            city: 'all',
            decade: 'all',
            status: 'all'
        },
        sort: 'name',
        view: 'grid',
        page: 1,
        perPage: 24
    };

    // DOM cache
    const elements = {};

    async function init() {
        cacheElements();
        loadStateFromURL();
        await loadData();
        populateCityFilter();
        setupEventListeners();
        applyFilters();
        updateUIFromState();
        hideLoadingOverlay();
    }

    function cacheElements() {
        elements.searchInput = document.getElementById('search-input');
        elements.cityFilter = document.getElementById('city-filter');
        elements.decadeFilter = document.getElementById('decade-filter');
        elements.sortSelect = document.getElementById('sort-select');
        elements.statusBtns = document.querySelectorAll('.status-btn');
        elements.viewGrid = document.getElementById('view-grid');
        elements.viewList = document.getElementById('view-list');
        elements.resultsGrid = document.getElementById('results-grid');
        elements.resultsList = document.getElementById('results-list');
        elements.listRows = document.getElementById('list-rows');
        elements.emptyState = document.getElementById('empty-state');
        elements.activeFilters = document.getElementById('active-filters');
        elements.resultsShowing = document.getElementById('results-showing');
        elements.resultsTotal = document.getElementById('results-total');
        elements.loadMoreContainer = document.getElementById('load-more-container');
        elements.loadMoreBtn = document.getElementById('load-more-btn');
        elements.clearAllFilters = document.getElementById('clear-all-filters');
        elements.heroTotal = document.getElementById('hero-total');
        elements.statActive = document.getElementById('stat-active');
        elements.statArchived = document.getElementById('stat-archived');
        elements.statCities = document.getElementById('stat-cities');
    }

    function loadStateFromURL() {
        const params = new URLSearchParams(window.location.search);

        if (params.has('search')) state.filters.search = params.get('search');
        if (params.has('city')) state.filters.city = params.get('city');
        if (params.has('decade')) state.filters.decade = params.get('decade');
        if (params.has('status')) state.filters.status = params.get('status');
        if (params.has('sort')) state.sort = params.get('sort');
        if (params.has('view')) state.view = params.get('view');
    }

    function updateURL() {
        const params = new URLSearchParams();

        if (state.filters.search) params.set('search', state.filters.search);
        if (state.filters.city !== 'all') params.set('city', state.filters.city);
        if (state.filters.decade !== 'all') params.set('decade', state.filters.decade);
        if (state.filters.status !== 'all') params.set('status', state.filters.status);
        if (state.sort !== 'name') params.set('sort', state.sort);
        if (state.view !== 'grid') params.set('view', state.view);

        const newURL = params.toString() ? `${window.location.pathname}?${params}` : window.location.pathname;
        window.history.replaceState({}, '', newURL);
    }

    async function loadData() {
        try {
            const response = await fetch('data/publications.json');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();

            state.publications = data.publications || [];

            // Update hero stats
            if (elements.heroTotal) elements.heroTotal.textContent = state.publications.length;

            const activeCount = state.publications.filter(p => p.isActive !== false && !p.yearCeased).length;
            const archivedCount = state.publications.length - activeCount;
            const cities = new Set(state.publications.map(p => p.city).filter(Boolean));

            animateCounter(elements.statActive, activeCount);
            animateCounter(elements.statArchived, archivedCount);
            animateCounter(elements.statCities, cities.size);

        } catch (error) {
            console.error('Failed to load data:', error);
            showError('Unable to load publication data.');
        }
    }

    function populateCityFilter() {
        const cities = [...new Set(state.publications.map(p => p.city).filter(Boolean))].sort();

        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            elements.cityFilter.appendChild(option);
        });
    }

    function setupEventListeners() {
        // Search
        elements.searchInput.addEventListener('input', debounce((e) => {
            state.filters.search = e.target.value.trim().toLowerCase();
            state.page = 1;
            applyFilters();
        }, 300));

        // City filter
        elements.cityFilter.addEventListener('change', (e) => {
            state.filters.city = e.target.value;
            state.page = 1;
            applyFilters();
        });

        // Decade filter
        elements.decadeFilter.addEventListener('change', (e) => {
            state.filters.decade = e.target.value;
            state.page = 1;
            applyFilters();
        });

        // Status buttons
        elements.statusBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                elements.statusBtns.forEach(b => b.classList.remove('active', 'text-accent'));
                elements.statusBtns.forEach(b => b.classList.add('text-paper-300'));
                btn.classList.add('active', 'text-accent');
                btn.classList.remove('text-paper-300');

                state.filters.status = btn.dataset.status;
                state.page = 1;
                applyFilters();
            });
        });

        // Sort
        elements.sortSelect.addEventListener('change', (e) => {
            state.sort = e.target.value;
            applyFilters();
        });

        // View toggle
        elements.viewGrid.addEventListener('click', () => {
            state.view = 'grid';
            updateViewMode();
        });
        elements.viewList.addEventListener('click', () => {
            state.view = 'list';
            updateViewMode();
        });

        // Load more
        elements.loadMoreBtn.addEventListener('click', loadMore);

        // Clear filters
        elements.clearAllFilters.addEventListener('click', resetFilters);
    }

    function updateUIFromState() {
        // Search
        if (state.filters.search && elements.searchInput) {
            elements.searchInput.value = state.filters.search;
        }

        // City
        if (state.filters.city !== 'all') {
            elements.cityFilter.value = state.filters.city;
        }

        // Decade
        if (state.filters.decade !== 'all') {
            elements.decadeFilter.value = state.filters.decade;
        }

        // Status
        elements.statusBtns.forEach(btn => {
            btn.classList.remove('active', 'text-accent');
            btn.classList.add('text-paper-300');
            if (btn.dataset.status === state.filters.status) {
                btn.classList.add('active', 'text-accent');
                btn.classList.remove('text-paper-300');
            }
        });

        // Sort
        elements.sortSelect.value = state.sort;

        // View mode
        updateViewMode();
    }

    function updateViewMode() {
        if (state.view === 'grid') {
            elements.resultsGrid.classList.remove('hidden');
            elements.resultsList.classList.add('hidden');
            elements.viewGrid.classList.add('text-accent');
            elements.viewGrid.classList.remove('text-paper-300');
            elements.viewList.classList.remove('text-accent');
            elements.viewList.classList.add('text-paper-300');
        } else {
            elements.resultsGrid.classList.add('hidden');
            elements.resultsList.classList.remove('hidden');
            elements.viewList.classList.add('text-accent');
            elements.viewList.classList.remove('text-paper-300');
            elements.viewGrid.classList.remove('text-accent');
            elements.viewGrid.classList.add('text-paper-300');
        }

        renderResults();
        updateURL();
    }

    function applyFilters() {
        let filtered = [...state.publications];

        // Search
        if (state.filters.search) {
            const query = state.filters.search.toLowerCase();
            filtered = filtered.filter(pub =>
                (pub.name && pub.name.toLowerCase().includes(query)) ||
                (pub.city && pub.city.toLowerCase().includes(query)) ||
                (pub.missionStatement && pub.missionStatement.toLowerCase().includes(query)) ||
                (pub.historicalNotes && pub.historicalNotes.toLowerCase().includes(query)) ||
                (pub.primaryFocus && pub.primaryFocus.toLowerCase().includes(query)) ||
                (pub.publishers && pub.publishers.toLowerCase().includes(query)) ||
                (pub.tags && pub.tags.some(t => t.toLowerCase().includes(query)))
            );
        }

        // City
        if (state.filters.city !== 'all') {
            filtered = filtered.filter(pub => pub.city === state.filters.city);
        }

        // Decade
        if (state.filters.decade !== 'all') {
            filtered = filtered.filter(pub => pub.decade === state.filters.decade);
        }

        // Status
        if (state.filters.status !== 'all') {
            if (state.filters.status === 'active') {
                filtered = filtered.filter(pub => pub.isActive !== false && !pub.yearCeased);
            } else {
                filtered = filtered.filter(pub => pub.isActive === false || pub.yearCeased);
            }
        }

        // Sort
        filtered = sortPublications(filtered);

        state.filtered = filtered;
        renderResults();
        updateActiveFiltersDisplay();
        updateURL();
    }

    function sortPublications(list) {
        const sorted = [...list];

        switch (state.sort) {
            case 'name':
                sorted.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
                break;
            case 'year-asc':
                sorted.sort((a, b) => (a.yearFounded || 9999) - (b.yearFounded || 9999));
                break;
            case 'year-desc':
                sorted.sort((a, b) => (b.yearFounded || 0) - (a.yearFounded || 0));
                break;
            case 'city':
                sorted.sort((a, b) => (a.city || '').localeCompare(b.city || ''));
                break;
        }

        return sorted;
    }

    function renderResults() {
        const toShow = state.filtered.slice(0, state.page * state.perPage);

        // Update counts
        elements.resultsShowing.textContent = toShow.length;
        elements.resultsTotal.textContent = state.filtered.length;

        if (state.filtered.length === 0) {
            elements.emptyState.classList.remove('hidden');
            elements.resultsGrid.innerHTML = '';
            elements.listRows.innerHTML = '';
            elements.loadMoreContainer.classList.add('hidden');
            return;
        }

        elements.emptyState.classList.add('hidden');

        if (state.view === 'grid') {
            renderGridView(toShow);
        } else {
            renderListView(toShow);
        }

        // Load more
        if (toShow.length < state.filtered.length) {
            elements.loadMoreContainer.classList.remove('hidden');
        } else {
            elements.loadMoreContainer.classList.add('hidden');
        }
    }

    function renderGridView(publications) {
        elements.resultsGrid.innerHTML = publications.map((pub, index) => {
            const isActive = pub.isActive !== false && !pub.yearCeased;
            const statusClass = isActive ? 'text-accent border-accent' : 'text-paper-300 border-paper-300';
            const statusText = isActive ? 'ACTIVE' : 'ARCHIVED';
            const years = formatYears(pub);
            const oneLiner = getOneLiner(pub);
            const tags = pub.tags ? pub.tags.slice(0, 3) : [];

            return `
                <article class="catalog-card bg-ink-800 border border-white/10 hover:border-accent transition-all p-6 fade-in" style="animation-delay: ${Math.min(index * 30, 300)}ms">
                    <header class="flex justify-between items-start mb-3">
                        <span class="font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 border ${statusClass}">${statusText}</span>
                        <span class="font-mono text-xs text-paper-300 index-number">#${String(pub.id).padStart(3, '0')}</span>
                    </header>

                    <a href="publication.html?id=${pub.id}" class="block group">
                        <h2 class="font-serif text-xl font-bold text-paper-100 mb-1 leading-tight group-hover:text-accent transition-colors">
                            ${escapeHtml(pub.name)}
                        </h2>
                    </a>

                    <p class="font-mono text-xs text-paper-300 pb-3 border-b border-white/10">
                        ${escapeHtml(pub.city || 'NJ')} &middot; ${years}
                    </p>

                    <p class="text-sm text-paper-200 leading-relaxed py-3 border-b border-white/10 italic">${escapeHtml(oneLiner)}</p>

                    ${tags.length > 0 ? `
                        <div class="flex flex-wrap gap-1 pt-3">
                            ${tags.map(t => `<span class="text-[10px] font-mono px-2 py-0.5 bg-white/5 text-paper-300">${escapeHtml(t)}</span>`).join('')}
                        </div>
                    ` : ''}

                    <footer class="flex gap-4 mt-4 pt-4 border-t border-white/5">
                        <a href="publication.html?id=${pub.id}" class="text-xs font-mono uppercase tracking-wider text-accent hover:text-white transition-colors">
                            View Record &rarr;
                        </a>
                        ${pub.websiteUrl ? `
                            <a href="${pub.websiteUrl}" target="_blank" rel="noopener" class="text-xs font-mono uppercase tracking-wider text-paper-300 hover:text-white transition-colors ml-auto">
                                Website
                            </a>
                        ` : ''}
                    </footer>
                </article>
            `;
        }).join('');
    }

    function renderListView(publications) {
        elements.listRows.innerHTML = publications.map((pub, index) => {
            const isActive = pub.isActive !== false && !pub.yearCeased;
            const statusClass = isActive ? 'text-accent' : 'text-paper-300';
            const statusText = isActive ? 'Active' : 'Archived';
            const years = formatYears(pub);

            return `
                <a href="publication.html?id=${pub.id}"
                   class="list-row py-4 border-b border-white/10 hover:bg-ink-800 transition-colors px-2 -mx-2 fade-in"
                   style="animation-delay: ${Math.min(index * 20, 200)}ms">

                    <div class="flex items-center gap-3">
                        <span class="font-mono text-xs text-paper-300 index-number hidden md:inline">#${String(pub.id).padStart(3, '0')}</span>
                        <span class="font-serif text-lg font-bold text-paper-100 hover:text-accent transition-colors">${escapeHtml(pub.name)}</span>
                    </div>

                    <span class="text-sm text-paper-300 hidden md:block">${escapeHtml(pub.city || 'NJ')}</span>
                    <span class="font-mono text-xs text-paper-300 hidden md:block">${years}</span>
                    <span class="font-mono text-xs ${statusClass} text-right hidden md:block">${statusText}</span>

                    <!-- Mobile info -->
                    <div class="md:hidden text-xs text-paper-300 mt-1">
                        ${escapeHtml(pub.city || 'NJ')} &middot; ${years} &middot; <span class="${statusClass}">${statusText}</span>
                    </div>
                </a>
            `;
        }).join('');
    }

    function updateActiveFiltersDisplay() {
        const chips = [];

        if (state.filters.search) {
            chips.push({ type: 'search', label: `"${state.filters.search}"` });
        }
        if (state.filters.city !== 'all') {
            chips.push({ type: 'city', label: state.filters.city });
        }
        if (state.filters.decade !== 'all') {
            chips.push({ type: 'decade', label: state.filters.decade });
        }
        if (state.filters.status !== 'all') {
            chips.push({ type: 'status', label: state.filters.status === 'active' ? 'Active Only' : 'Archived Only' });
        }

        if (chips.length === 0) {
            elements.activeFilters.innerHTML = '';
            return;
        }

        elements.activeFilters.innerHTML = `
            <span class="font-mono text-xs text-paper-300 mr-2">Filters:</span>
            ${chips.map(chip => `
                <button onclick="window.archivePage.clearFilter('${chip.type}')"
                        class="flex items-center gap-1 px-2 py-1 bg-white/10 hover:bg-white/20 text-paper-100 text-xs font-mono transition-colors">
                    ${escapeHtml(chip.label)}
                    <span class="text-accent ml-1">&times;</span>
                </button>
            `).join('')}
            <button onclick="window.archivePage.resetFilters()" class="text-xs text-accent hover:underline font-mono ml-2">
                Clear All
            </button>
        `;
    }

    function clearFilter(type) {
        if (type === 'search') {
            state.filters.search = '';
            elements.searchInput.value = '';
        } else if (type === 'city') {
            state.filters.city = 'all';
            elements.cityFilter.value = 'all';
        } else if (type === 'decade') {
            state.filters.decade = 'all';
            elements.decadeFilter.value = 'all';
        } else if (type === 'status') {
            state.filters.status = 'all';
            elements.statusBtns.forEach(btn => {
                btn.classList.remove('active', 'text-accent');
                btn.classList.add('text-paper-300');
                if (btn.dataset.status === 'all') {
                    btn.classList.add('active', 'text-accent');
                    btn.classList.remove('text-paper-300');
                }
            });
        }

        state.page = 1;
        applyFilters();
    }

    function resetFilters() {
        state.filters = {
            search: '',
            city: 'all',
            decade: 'all',
            status: 'all'
        };
        state.page = 1;

        elements.searchInput.value = '';
        elements.cityFilter.value = 'all';
        elements.decadeFilter.value = 'all';

        elements.statusBtns.forEach(btn => {
            btn.classList.remove('active', 'text-accent');
            btn.classList.add('text-paper-300');
            if (btn.dataset.status === 'all') {
                btn.classList.add('active', 'text-accent');
                btn.classList.remove('text-paper-300');
            }
        });

        applyFilters();
    }

    function loadMore() {
        state.page++;
        renderResults();
    }

    function formatYears(pub) {
        if (!pub.yearFounded) return 'Unknown';
        if (pub.yearCeased) return `${pub.yearFounded}–${pub.yearCeased}`;
        return `${pub.yearFounded}–`;
    }

    function getOneLiner(pub) {
        // Priority 1: Mission statement (cleaned up)
        if (pub.missionStatement) {
            let mission = pub.missionStatement.replace(/^["']|["']$/g, '').trim();
            return truncate(mission, 80);
        }

        // Priority 2: Primary focus / content areas
        if (pub.primaryFocus && pub.primaryFocus.toLowerCase() !== 'newspaper') {
            return truncate(pub.primaryFocus, 80);
        }

        // Priority 3: Construct from format + frequency
        const format = pub.format || 'Publication';
        const frequency = pub.frequency ? pub.frequency.toLowerCase() : '';
        const medium = pub.medium ? pub.medium.toLowerCase() : '';

        if (frequency && medium) {
            return `${frequency.charAt(0).toUpperCase() + frequency.slice(1)} ${medium} ${format.toLowerCase()}`;
        } else if (frequency) {
            return `${frequency.charAt(0).toUpperCase() + frequency.slice(1)} ${format.toLowerCase()}`;
        } else if (format) {
            return format;
        }

        return 'Publication record';
    }

    function truncate(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '...' : str;
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function debounce(fn, delay) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function animateCounter(element, target) {
        if (!element) return;
        const duration = 1000;
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            element.textContent = Math.floor(start + (target - start) * easeOut);
            if (progress < 1) requestAnimationFrame(update);
        }

        requestAnimationFrame(update);
    }

    function hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('opacity-0');
            setTimeout(() => overlay.classList.add('hidden'), 500);
        }
    }

    function showError(message) {
        elements.resultsGrid.innerHTML = `
            <div class="col-span-full text-center py-12 border border-accent/50 bg-accent/5">
                <p class="text-accent font-mono uppercase tracking-widest mb-2">Error</p>
                <p class="text-paper-300">${escapeHtml(message)}</p>
            </div>
        `;
    }

    // Expose API
    window.archivePage = {
        clearFilter,
        resetFilters,
        getState: () => state
    };

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
