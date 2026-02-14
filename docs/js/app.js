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
    elements.resultsShowing = document.getElementById('results-showing'); // Added this
    elements.resultsTotal = document.getElementById('results-total');     // Added this
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
    const statCities = document.getElementById('stat-cities');
    const statActive = document.getElementById('stat-active');

    if (statPublications) animateCounter(statPublications, metadata.totalCount || state.publications.length);
    if (statCities) animateCounter(statCities, metadata.cities?.length || 27);
    if (statActive) animateCounter(statActive, metadata.activeCount || 52);
  }

  function animateCounter(element, target) {
    const duration = 1500;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Quartic ease out for a mechanical feel
      const easeOut = 1 - Math.pow(1 - progress, 4); 
      
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
    siblings.forEach(sib => sib.classList.remove('active', 'bg-white', 'text-ink-950', 'border-white'));
    siblings.forEach(sib => sib.classList.add('text-paper-300', 'border-white/20'));
    
    btn.classList.add('active', 'bg-white', 'text-ink-950', 'border-white');
    btn.classList.remove('text-paper-300', 'border-white/20');

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
    const statusClass = pub.isActive ? 'text-accent border-accent' : 'text-paper-300 border-paper-300';
    const statusText = pub.isActive ? 'ACTIVE' : 'ARCHIVED';
    const years = pub.yearFounded ? `${pub.yearFounded}${pub.yearCeased ? ' — ' + pub.yearCeased : ' — Present'}` : 'Unknown';
    const websiteLink = pub.websiteUrl ? `<a href="${pub.websiteUrl}" target="_blank" rel="noopener" class="text-xs font-mono uppercase tracking-wider text-accent hover:text-white transition-colors border-b border-transparent hover:border-accent pb-1">Visit Site</a>` : '';
    // Only show archive link if it's an actual URL (starts with http)
    const hasValidArchiveUrl = pub.archiveUrl && pub.archiveUrl.startsWith('http');
    const archiveLink = hasValidArchiveUrl ? `<a href="${pub.archiveUrl}" target="_blank" rel="noopener" class="text-xs font-mono uppercase tracking-wider text-paper-300 hover:text-white transition-colors border-b border-transparent hover:border-white pb-1">Archives</a>` : '';

    // Build one-line description from available fields
    const oneLiner = getOneLiner(pub);

    return `
      <article class="bg-ink-900 border border-white/10 hover:border-accent transition-colors p-6 flex flex-col h-full group">
        <header class="flex justify-between items-start mb-4">
            <span class="font-mono text-[10px] uppercase tracking-widest px-2 py-1 border ${statusClass}">${statusText}</span>
            <span class="font-mono text-xs text-paper-300">${pub.city || 'NJ'}</span>
        </header>

        <a href="publication.html?id=${pub.id}" class="block">
            <h3 class="font-serif text-2xl font-bold text-paper-100 mb-2 leading-tight group-hover:text-accent transition-colors">
                ${escapeHtml(pub.name)}
            </h3>
        </a>

        <p class="font-mono text-xs text-paper-300 border-b border-white/10 pb-4">
            ${years}
        </p>

        <p class="text-sm text-paper-200 leading-relaxed py-4 border-b border-white/10 italic flex-grow">
            ${escapeHtml(oneLiner)}
        </p>

        <footer class="flex gap-4 mt-auto pt-4">
            <a href="publication.html?id=${pub.id}" class="text-xs font-mono uppercase tracking-wider text-accent hover:text-white transition-colors border-b border-transparent hover:border-accent pb-1">View Details</a>
            ${websiteLink}
            ${archiveLink}
        </footer>
      </article>
    `;
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

  function updateResultsCount() {
    if (elements.resultsShowing) elements.resultsShowing.textContent = Math.min(state.currentPage * state.perPage, state.filteredPublications.length);
    if (elements.resultsTotal) elements.resultsTotal.textContent = state.filteredPublications.length;
  }

  function updateActiveFiltersDisplay() {
    if (!elements.activeFilters || !elements.activeFiltersList) return;

    const activeFilters = [];

    if (state.filters.search) activeFilters.push({ type: 'search', label: `"${state.filters.search}"` });
    if (state.filters.city !== 'all') activeFilters.push({ type: 'city', label: state.filters.city });
    if (state.filters.decade !== 'all') activeFilters.push({ type: 'decade', label: state.filters.decade });
    if (state.filters.status !== 'all') activeFilters.push({ type: 'status', label: state.filters.status === 'active' ? 'Active' : 'Archived' });
    if (state.filters.format !== 'all') activeFilters.push({ type: 'format', label: state.filters.format === 'print' ? 'Print' : 'Digital' });

    if (activeFilters.length === 0) {
      elements.activeFilters.classList.add('hidden');
      return;
    }

    elements.activeFilters.classList.remove('hidden');
    elements.activeFiltersList.innerHTML = activeFilters.map(f => `
      <span class="font-mono text-[10px] bg-white/10 text-paper-100 px-2 py-1 flex items-center gap-2 hover:bg-white/20 transition-colors cursor-pointer" onclick="window.njbp.removeFilter('${f.type}')">
        ${escapeHtml(f.label)}
        <span class="text-accent">&times;</span>
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
        if(btn.dataset.value === 'all') {
             btn.classList.add('active', 'bg-white', 'text-ink-950', 'border-white');
             btn.classList.remove('text-paper-300', 'border-white/20');
        } else {
             btn.classList.remove('active', 'bg-white', 'text-ink-950', 'border-white');
             btn.classList.add('text-paper-300', 'border-white/20');
        }
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
       if(btn.dataset.value === 'all') {
             btn.classList.add('active', 'bg-white', 'text-ink-950', 'border-white');
             btn.classList.remove('text-paper-300', 'border-white/20');
        } else {
             btn.classList.remove('active', 'bg-white', 'text-ink-950', 'border-white');
             btn.classList.add('text-paper-300', 'border-white/20');
        }
    });

    applyFilters();
  }

  function loadMore() {
    state.currentPage++;
    renderPublications();
    updateResultsCount(); // Ensure stats update
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
        <div class="col-span-full text-center py-12 border border-accent/50 bg-accent/5">
          <p class="text-accent font-mono uppercase tracking-widest mb-4">System Error</p>
          <p class="text-paper-300 mb-6 font-serif text-xl">${escapeHtml(message)}</p>
          <button onclick="location.reload()" class="px-6 py-3 bg-white text-ink-950 font-bold hover:bg-accent hover:text-white transition-colors">
            Reload System
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
