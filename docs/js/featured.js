/**
 * NJ Black Press Database - Featured Publications
 * Renders featured historical and contemporary publication showcases
 * with extended data support for richer content display
 */

(function() {
  'use strict';

  let publications = [];
  let featuredData = { featuredHistoric: [], featuredContemporary: [] };
  let expandedCards = new Set();

  async function init() {
    await loadData();
    renderFeaturedHistorical();
    renderFeaturedContemporary();
    setupEventListeners();
  }

  async function loadData() {
    try {
      // Load both data sources in parallel
      const [pubResponse, featuredResponse] = await Promise.all([
        fetch('data/publications.json'),
        fetch('data/featured-publications.json').catch(() => ({ ok: false }))
      ]);

      if (!pubResponse.ok) throw new Error(`HTTP ${pubResponse.status}`);
      const pubData = await pubResponse.json();
      publications = pubData.publications || [];

      // Load featured data if available
      if (featuredResponse.ok) {
        featuredData = await featuredResponse.json();
      }
    } catch (error) {
      console.error('Featured: Failed to load data:', error);
    }
  }

  function getExtendedData(pubId, type) {
    const source = type === 'historic' ? featuredData.featuredHistoric : featuredData.featuredContemporary;
    return source.find(item => item.id === pubId) || null;
  }

  function renderFeaturedHistorical() {
    const container = document.getElementById('featured-historical-grid');
    if (!container) return;

    let featured = publications.filter(p => p.isFeaturedHistoric);

    if (featured.length === 0) {
      // Fallback to oldest publications
      featured = publications
        .filter(p => p.yearFounded && p.yearFounded < 1980)
        .sort((a, b) => (a.yearFounded || 9999) - (b.yearFounded || 9999))
        .slice(0, 8);
    }

    container.innerHTML = featured.map(pub => createHistoricalCard(pub)).join('');
  }

  function renderFeaturedContemporary() {
    const container = document.getElementById('featured-contemporary-grid');
    if (!container) return;

    let featured = publications.filter(p => p.isFeaturedContemporary);

    if (featured.length === 0) {
      // Fallback to recent active digital publications
      featured = publications
        .filter(p => p.isActive && p.websiteUrl && p.yearFounded && p.yearFounded >= 2010)
        .slice(0, 6);
    }

    container.innerHTML = featured.map(pub => createContemporaryCard(pub)).join('');
  }

  function createHistoricalCard(pub) {
    const extended = getExtendedData(pub.id, 'historic');
    const years = pub.yearFounded ? `${pub.yearFounded}${pub.yearCeased ? ' - ' + pub.yearCeased : ' - Present'}` : 'Unknown';
    const cardId = `historic-${pub.id}`;
    const isExpanded = expandedCards.has(cardId);

    // Use extended data if available, fallback to base publication data
    const founders = extended?.founders || [];
    const historicalNotes = extended?.historicalNotes || pub.historicalNotes || '';
    const physicalArchive = extended?.physicalArchive || null;
    const tags = extended?.tags || [];
    const missionStatement = extended?.missionStatement || pub.missionStatement || '';

    // Condensed notes for collapsed state
    const condensedNotes = truncate(historicalNotes, 180);
    const hasMoreContent = historicalNotes.length > 180;

    // Build archive links section
    let archiveSection = '';
    if (pub.archiveUrl || physicalArchive) {
      archiveSection = '<div class="flex flex-wrap items-center gap-3 mt-4 pt-4 border-t border-stone-700/50">';

      if (pub.archiveUrl) {
        archiveSection += `
          <a href="${pub.archiveUrl}" target="_blank" rel="noopener"
             class="inline-flex items-center gap-1.5 text-amber-400 hover:text-amber-300 text-sm transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path>
            </svg>
            Digital Archive
          </a>`;
      }

      if (physicalArchive) {
        archiveSection += `
          <span class="text-stone-500 text-xs flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
            </svg>
            ${escapeHtml(physicalArchive.location)}
          </span>`;
      }

      archiveSection += '</div>';
    }

    // Build tags section
    let tagsSection = '';
    if (tags.length > 0) {
      tagsSection = `
        <div class="flex flex-wrap gap-1.5 mt-3">
          ${tags.map(tag => `
            <span class="px-2 py-0.5 bg-stone-700/60 text-stone-400 rounded text-xs">${escapeHtml(tag)}</span>
          `).join('')}
        </div>`;
    }

    return `
      <article class="featured-card group bg-gradient-to-br from-stone-800 to-stone-900 rounded-xl p-6 border border-stone-700/50 hover:border-amber-500/30 transition-all duration-300" data-card-id="${cardId}">
        <div class="flex items-start justify-between mb-3">
          <span class="px-2.5 py-1 bg-amber-500/20 text-amber-400 rounded text-xs font-semibold tracking-wide">${escapeHtml(pub.decade || 'Historic')}</span>
          <span class="text-stone-500 text-sm">${escapeHtml(pub.city || 'NJ')}</span>
        </div>

        <h3 class="font-serif text-xl text-stone-100 mb-1 group-hover:text-amber-400 transition-colors leading-tight">
          ${escapeHtml(pub.name)}
        </h3>

        <p class="text-stone-400 text-sm mb-3">${years}</p>

        ${founders.length > 0 ? `
          <p class="text-stone-300 text-sm mb-3">
            <span class="text-stone-500">Founded by:</span> ${escapeHtml(founders.join(', '))}
          </p>
        ` : ''}

        ${missionStatement ? `
          <blockquote class="text-stone-300 text-sm italic border-l-2 border-amber-500/50 pl-3 mb-4">
            "${escapeHtml(truncate(missionStatement, 120))}"
          </blockquote>
        ` : ''}

        ${historicalNotes ? `
          <div class="historical-notes">
            <p class="text-stone-400 text-sm leading-relaxed ${isExpanded ? '' : 'line-clamp-4'}" data-full-text="${escapeAttr(historicalNotes)}">
              ${isExpanded ? escapeHtml(historicalNotes) : escapeHtml(condensedNotes)}
            </p>
            ${hasMoreContent ? `
              <button class="read-more-btn text-amber-400 hover:text-amber-300 text-sm mt-2 flex items-center gap-1 transition-colors" data-card-id="${cardId}">
                ${isExpanded ? 'Show less' : 'Read more'}
                <svg class="w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </button>
            ` : ''}
          </div>
        ` : ''}

        ${tagsSection}
        ${archiveSection}
      </article>
    `;
  }

  function createContemporaryCard(pub) {
    const extended = getExtendedData(pub.id, 'contemporary');

    // Use extended data if available
    const founders = extended?.founders || [];
    const missionStatement = extended?.missionStatement || pub.missionStatement || '';
    const focusAreas = extended?.focusAreas || (pub.primaryFocus ? pub.primaryFocus.split(',').map(s => s.trim()) : []);
    const tags = extended?.tags || [];
    const websiteUrl = extended?.websiteUrl || pub.websiteUrl;

    // Build focus areas / tags section
    let focusSection = '';
    if (focusAreas.length > 0 || tags.length > 0) {
      const displayTags = tags.length > 0 ? tags : focusAreas.slice(0, 4);
      focusSection = `
        <div class="flex flex-wrap gap-1.5 mb-4">
          ${displayTags.map(tag => `
            <span class="px-2 py-0.5 bg-emerald-500/10 text-emerald-400/80 border border-emerald-500/20 rounded text-xs">${escapeHtml(tag)}</span>
          `).join('')}
        </div>`;
    }

    const websiteLink = websiteUrl
      ? `<a href="${websiteUrl}" target="_blank" rel="noopener"
           class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 text-stone-900 rounded-lg hover:bg-emerald-400 transition-colors text-sm font-medium">
           Visit Website
           <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
         </a>`
      : '';

    return `
      <article class="featured-card group bg-gradient-to-br from-emerald-900/30 to-stone-900 rounded-xl p-6 border border-emerald-500/20 hover:border-emerald-400/40 transition-all duration-300">
        <div class="flex items-start justify-between mb-3">
          <span class="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-semibold tracking-wide flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
            Active
          </span>
          <span class="text-stone-500 text-sm">${escapeHtml(pub.city || 'NJ')}</span>
        </div>

        <h3 class="font-serif text-xl text-stone-100 mb-1 group-hover:text-emerald-400 transition-colors leading-tight">
          ${escapeHtml(pub.name)}
        </h3>

        <p class="text-stone-400 text-sm mb-3">Founded ${pub.yearFounded || 'Recently'}</p>

        ${founders.length > 0 ? `
          <p class="text-stone-300 text-sm mb-3">
            <span class="text-stone-500">By:</span> ${escapeHtml(founders.join(', '))}
          </p>
        ` : ''}

        ${missionStatement ? `
          <blockquote class="text-stone-300 text-sm italic border-l-2 border-emerald-500/50 pl-3 mb-4">
            "${escapeHtml(truncate(missionStatement, 140))}"
          </blockquote>
        ` : ''}

        ${focusSection}
        ${websiteLink}
      </article>
    `;
  }

  function setupEventListeners() {
    document.addEventListener('click', function(e) {
      const readMoreBtn = e.target.closest('.read-more-btn');
      if (readMoreBtn) {
        const cardId = readMoreBtn.dataset.cardId;
        toggleExpanded(cardId);
      }
    });
  }

  function toggleExpanded(cardId) {
    if (expandedCards.has(cardId)) {
      expandedCards.delete(cardId);
    } else {
      expandedCards.add(cardId);
    }
    // Re-render to update the card
    renderFeaturedHistorical();
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function truncate(str, length) {
    if (!str) return '';
    if (str.length <= length) return str;
    // Try to break at a word boundary
    const truncated = str.substring(0, length);
    const lastSpace = truncated.lastIndexOf(' ');
    if (lastSpace > length - 30) {
      return truncated.substring(0, lastSpace) + '...';
    }
    return truncated + '...';
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
