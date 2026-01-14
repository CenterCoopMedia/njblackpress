/**
 * NJ Black Press Database - Main Application
 * Handles data loading, filtering, search, and rendering
 */

(function() {
  'use strict';

  // State management
  const state = {
    publications: [],
    filteredPublications: [],
    filters: {
      search: '',
      city: 'all',
      decade: 'all',
      status: 'all',
      format: 'all'
    },
    sortBy: 'name',
    currentPage: 1,
    perPage: 24
  };

  // DOM elements cache
  const elements = {};

  // Initialize application
  async function init() {
    cacheElements();
    setupEventListeners();
    await loadData();
    hideLoadingOverlay();
  }

  function cacheElements() {
    elements.loadingOverlay = document.getElementById('loading-overlay');
    elements.searchInput = document.getElementById('database-search');
    elements.resultsGrid = document.getElementById('database-results');
    elements.resultsCount = document.getElementById('results-count');
    elements.emptyResults = document.getElementById('empty-results');
    elements.activeFilters = document.getElementById('active-filters');
    elements.activeFiltersList = document.getElementById('active-filters-list');
    elements.clearFilters = document.getElementById('clear-filters');
    elements.sortSelect = document.getElementById('sort-select');
    elements.loadMoreContainer = document.getElementById('load-more-container');
    elements.loadMoreBtn = document.getElementById('load-more-btn');
    elements.filterButtons = document.querySelectorAll('.filter-btn');
  }

  function setupEventListeners() {
    // Search with debounce
    if (elements.searchInput) {
      elements.searchInput.addEventListener('input', debounce(handleSearch, 300));
    }

    // Filter buttons
    elements.filterButtons.forEach(btn => {
      btn.addEventListener('click', handleFilterClick);
    });

    // Clear filters
    if (elements.clearFilters) {
      elements.clearFilters.addEventListener('click', resetFilters);
    }

    // Sort select
    if (elements.sortSelect) {
      elements.sortSelect.addEventListener('change', handleSort);
    }

    // Load more
    if (elements.loadMoreBtn) {
      elements.loadMoreBtn.addEventListener('click', loadMore);
    }

    // Reset search button
    const resetSearch = document.getElementById('reset-search');
    if (resetSearch) {
      resetSearch.addEventListener('click', resetFilters);
    }
  }

  async function loadData() {
    try {
      const response = await fetch('data/publications.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      state.publications = data.publications || [];
      state.filteredPublications = [...state.publications];

      // Update stats
      updateStats(data.metadata);

      // Initial render
      renderPublications();
      updateResultsCount();

    } catch (error) {
      console.error('Failed to load data:', error);
      showError('Unable to load publication data. Please refresh the page.');
    }
  }

  function updateStats(metadata) {
    const statPublications = document.getElementById('stat-publications');
    const statYears = document.getElementById('stat-years');
    const statCities = document.getElementById('stat-cities');
    const statActive = document.getElementById('stat-active');

    if (statPublications) animateCounter(statPublications, metadata.totalCount || state.publications.length);
    if (statYears) animateCounter(statYears, 145); // 1880-2025
    if (statCities) animateCounter(statCities, metadata.cities?.length || 27);
    if (statActive) animateCounter(statActive, metadata.activeCount || 52);
  }

  function animateCounter(element, target) {
    const duration = 2000;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + (target - start) * easeOut);

      element.textContent = current;

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = target;
      }
    }

    requestAnimationFrame(update);
  }

  function handleSearch(e) {
    state.filters.search = e.target.value.toLowerCase().trim();
    state.currentPage = 1;
    applyFilters();
  }

  function handleFilterClick(e) {
    const btn = e.currentTarget;
    const filterType = btn.dataset.filter;
    const filterValue = btn.dataset.value;

    // Toggle active state
    const siblings = document.querySelectorAll(`.filter-btn[data-filter="${filterType}"]`);
    siblings.forEach(sib => sib.classList.remove('active'));
    btn.classList.add('active');

    // Update state
    state.filters[filterType] = filterValue;
    state.currentPage = 1;
    applyFilters();
  }

  function handleSort(e) {
    state.sortBy = e.target.value;
    sortPublications();
    renderPublications();
  }

  function applyFilters() {
    let filtered = [...state.publications];

    // Search filter
    if (state.filters.search) {
      const query = state.filters.search;
      filtered = filtered.filter(pub =>
        pub.name?.toLowerCase().includes(query) ||
        pub.city?.toLowerCase().includes(query) ||
        pub.primaryFocus?.toLowerCase().includes(query) ||
        pub.missionStatement?.toLowerCase().includes(query) ||
        pub.publishers?.toLowerCase().includes(query)
      );
    }

    // City filter
    if (state.filters.city !== 'all') {
      filtered = filtered.filter(pub => pub.city === state.filters.city);
    }

    // Decade filter
    if (state.filters.decade !== 'all') {
      filtered = filtered.filter(pub => pub.decade === state.filters.decade);
    }

    // Status filter
    if (state.filters.status !== 'all') {
      const isActive = state.filters.status === 'active';
      filtered = filtered.filter(pub => pub.isActive === isActive);
    }

    // Format filter
    if (state.filters.format !== 'all') {
      filtered = filtered.filter(pub => {
        const medium = pub.medium?.toLowerCase() || '';
        if (state.filters.format === 'print') return medium.includes('print');
        if (state.filters.format === 'digital') return medium.includes('digital') || medium.includes('online');
        return true;
      });
    }

    state.filteredPublications = filtered;
    sortPublications();
    renderPublications();
    updateResultsCount();
    updateActiveFiltersDisplay();
  }

  function sortPublications() {
    const sorted = [...state.filteredPublications];

    switch (state.sortBy) {
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

    state.filteredPublications = sorted;
  }

  function renderPublications() {
    if (!elements.resultsGrid) return;

    const start = 0;
    const end = state.currentPage * state.perPage;
    const toShow = state.filteredPublications.slice(start, end);

    if (toShow.length === 0) {
      elements.resultsGrid.innerHTML = '';
      if (elements.emptyResults) elements.emptyResults.classList.remove('hidden');
      if (elements.loadMoreContainer) elements.loadMoreContainer.classList.add('hidden');
      return;
    }

    if (elements.emptyResults) elements.emptyResults.classList.add('hidden');

    elements.resultsGrid.innerHTML = toShow.map(pub => createPublicationCard(pub)).join('');

    // Show/hide load more
    if (elements.loadMoreContainer) {
      if (end < state.filteredPublications.length) {
        elements.loadMoreContainer.classList.remove('hidden');
      } else {
        elements.loadMoreContainer.classList.add('hidden');
      }
    }
  }

  function createPublicationCard(pub) {
    const statusClass = pub.isActive ? 'bg-emerald-500/20 text-emerald-300' : 'bg-stone-500/20 text-stone-400';
    const statusText = pub.isActive ? 'Active' : 'Ceased';
    const years = pub.yearFounded ? `${pub.yearFounded}${pub.yearCeased ? '-' + pub.yearCeased : '-Present'}` : 'Unknown';
    const websiteLink = pub.websiteUrl ? `<a href="${pub.websiteUrl}" target="_blank" rel="noopener" class="text-amber-400 hover:text-amber-300 text-sm">Visit Website &rarr;</a>` : '';
    const archiveLink = pub.archiveUrl ? `<a href="${pub.archiveUrl}" target="_blank" rel="noopener" class="text-stone-400 hover:text-stone-300 text-sm">View Archive &rarr;</a>` : '';

    return `
      <article class="publication-card bg-stone-800/50 rounded-lg p-5 border border-stone-700/50 hover:border-amber-500/30 transition-all duration-300 hover:-translate-y-1">
        <div class="flex items-start justify-between gap-3 mb-3">
          <h3 class="font-serif text-lg text-stone-100 leading-tight">${escapeHtml(pub.name)}</h3>
          <span class="px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${statusClass}">${statusText}</span>
        </div>

        <div class="space-y-2 text-sm text-stone-400 mb-4">
          <p><span class="text-stone-500">Location:</span> ${escapeHtml(pub.city || 'Unknown')}</p>
          <p><span class="text-stone-500">Years:</span> ${years}</p>
          <p><span class="text-stone-500">Frequency:</span> ${escapeHtml(pub.frequency || 'Unknown')}</p>
          ${pub.primaryFocus ? `<p><span class="text-stone-500">Focus:</span> ${escapeHtml(truncate(pub.primaryFocus, 60))}</p>` : ''}
        </div>

        ${pub.missionStatement ? `<p class="text-sm text-stone-300 italic mb-4 line-clamp-2">"${escapeHtml(truncate(pub.missionStatement, 120))}"</p>` : ''}

        <div class="flex gap-4 mt-auto pt-3 border-t border-stone-700/50">
          ${websiteLink}
          ${archiveLink}
        </div>
      </article>
    `;
  }

  function updateResultsCount() {
    if (elements.resultsCount) {
      elements.resultsCount.textContent = state.filteredPublications.length;
    }
  }

  function updateActiveFiltersDisplay() {
    if (!elements.activeFilters || !elements.activeFiltersList) return;

    const activeFilters = [];

    if (state.filters.search) activeFilters.push({ type: 'search', label: `"${state.filters.search}"` });
    if (state.filters.city !== 'all') activeFilters.push({ type: 'city', label: state.filters.city });
    if (state.filters.decade !== 'all') activeFilters.push({ type: 'decade', label: state.filters.decade });
    if (state.filters.status !== 'all') activeFilters.push({ type: 'status', label: state.filters.status === 'active' ? 'Active' : 'Ceased' });
    if (state.filters.format !== 'all') activeFilters.push({ type: 'format', label: state.filters.format === 'print' ? 'Print' : 'Digital' });

    if (activeFilters.length === 0) {
      elements.activeFilters.classList.add('hidden');
      return;
    }

    elements.activeFilters.classList.remove('hidden');
    elements.activeFiltersList.innerHTML = activeFilters.map(f => `
      <span class="inline-flex items-center gap-1 px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full text-sm">
        ${escapeHtml(f.label)}
        <button onclick="window.njbp.removeFilter('${f.type}')" class="hover:text-amber-100">&times;</button>
      </span>
    `).join('');
  }

  function removeFilter(type) {
    if (type === 'search') {
      state.filters.search = '';
      if (elements.searchInput) elements.searchInput.value = '';
    } else {
      state.filters[type] = 'all';
      // Reset button state
      const buttons = document.querySelectorAll(`.filter-btn[data-filter="${type}"]`);
      buttons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === 'all');
      });
    }
    state.currentPage = 1;
    applyFilters();
  }

  function resetFilters() {
    state.filters = {
      search: '',
      city: 'all',
      decade: 'all',
      status: 'all',
      format: 'all'
    };
    state.currentPage = 1;

    if (elements.searchInput) elements.searchInput.value = '';

    // Reset all filter buttons
    elements.filterButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.value === 'all');
    });

    applyFilters();
  }

  function loadMore() {
    state.currentPage++;
    renderPublications();
  }

  function hideLoadingOverlay() {
    if (elements.loadingOverlay) {
      elements.loadingOverlay.classList.add('opacity-0');
      setTimeout(() => {
        elements.loadingOverlay.classList.add('hidden');
      }, 500);
    }
  }

  function showError(message) {
    if (elements.resultsGrid) {
      elements.resultsGrid.innerHTML = `
        <div class="col-span-full text-center py-12">
          <p class="text-red-400">${escapeHtml(message)}</p>
          <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-amber-500 text-stone-900 rounded hover:bg-amber-400">
            Retry
          </button>
        </div>
      `;
    }
  }

  // Utility functions
  function debounce(fn, delay) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function truncate(str, length) {
    if (!str) return '';
    return str.length > length ? str.substring(0, length) + '...' : str;
  }

  // Expose API for external access
  window.njbp = {
    removeFilter,
    resetFilters,
    getState: () => state,
    filterByDecade: (decade) => {
      state.filters.decade = decade;
      state.currentPage = 1;
      applyFilters();
      // Scroll to database
      document.getElementById('database')?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
