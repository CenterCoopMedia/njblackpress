/**
 * NJ Black Press Database - Featured Publications
 * Renders featured historical and contemporary publication showcases
 */

(function() {
  'use strict';

  let publications = [];

  async function init() {
    await loadData();
    renderFeaturedHistorical();
    renderFeaturedContemporary();
  }

  async function loadData() {
    try {
      const response = await fetch('data/publications.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      publications = data.publications || [];
    } catch (error) {
      console.error('Featured: Failed to load data:', error);
    }
  }

  function renderFeaturedHistorical() {
    const container = document.getElementById('featured-historical-grid');
    if (!container) return;

    const featured = publications.filter(p => p.isFeaturedHistoric);

    if (featured.length === 0) {
      // Fallback to oldest publications
      featured.push(...publications
        .filter(p => p.yearFounded && p.yearFounded < 1980)
        .sort((a, b) => (a.yearFounded || 9999) - (b.yearFounded || 9999))
        .slice(0, 8)
      );
    }

    container.innerHTML = featured.map(pub => createHistoricalCard(pub)).join('');
  }

  function renderFeaturedContemporary() {
    const container = document.getElementById('featured-contemporary-grid');
    if (!container) return;

    const featured = publications.filter(p => p.isFeaturedContemporary);

    if (featured.length === 0) {
      // Fallback to recent active digital publications
      featured.push(...publications
        .filter(p => p.isActive && p.websiteUrl && p.yearFounded && p.yearFounded >= 2010)
        .slice(0, 6)
      );
    }

    container.innerHTML = featured.map(pub => createContemporaryCard(pub)).join('');
  }

  function createHistoricalCard(pub) {
    const years = pub.yearFounded ? `${pub.yearFounded}${pub.yearCeased ? '-' + pub.yearCeased : ''}` : 'Unknown';
    const archiveLink = pub.archiveUrl
      ? `<a href="${pub.archiveUrl}" target="_blank" rel="noopener" class="inline-flex items-center gap-1 text-amber-400 hover:text-amber-300 text-sm mt-3">
           View Archive <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
         </a>`
      : '';

    return `
      <article class="featured-card group bg-gradient-to-br from-stone-800 to-stone-900 rounded-xl p-6 border border-stone-700/50 hover:border-amber-500/30 transition-all duration-300">
        <div class="flex items-start justify-between mb-4">
          <span class="px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-xs font-medium">${pub.decade || 'Historic'}</span>
          <span class="text-stone-500 text-sm">${escapeHtml(pub.city || 'NJ')}</span>
        </div>

        <h3 class="font-serif text-xl text-stone-100 mb-2 group-hover:text-amber-400 transition-colors">
          ${escapeHtml(pub.name)}
        </h3>

        <p class="text-stone-400 text-sm mb-3">${years}</p>

        ${pub.missionStatement ? `
          <p class="text-stone-300 text-sm italic line-clamp-2 mb-3">"${escapeHtml(truncate(pub.missionStatement, 100))}"</p>
        ` : ''}

        ${pub.historicalNotes ? `
          <p class="text-stone-400 text-sm line-clamp-3">${escapeHtml(truncate(pub.historicalNotes, 150))}</p>
        ` : ''}

        ${archiveLink}
      </article>
    `;
  }

  function createContemporaryCard(pub) {
    const websiteLink = pub.websiteUrl
      ? `<a href="${pub.websiteUrl}" target="_blank" rel="noopener"
           class="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 text-stone-900 rounded-lg hover:bg-amber-400 transition-colors text-sm font-medium">
           Visit Website
           <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
         </a>`
      : '';

    return `
      <article class="featured-card group bg-gradient-to-br from-emerald-900/30 to-stone-900 rounded-xl p-6 border border-emerald-500/20 hover:border-emerald-400/40 transition-all duration-300">
        <div class="flex items-start justify-between mb-4">
          <span class="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-medium">Active</span>
          <span class="text-stone-500 text-sm">${escapeHtml(pub.city || 'NJ')}</span>
        </div>

        <h3 class="font-serif text-xl text-stone-100 mb-2 group-hover:text-emerald-400 transition-colors">
          ${escapeHtml(pub.name)}
        </h3>

        <p class="text-stone-400 text-sm mb-3">Founded ${pub.yearFounded || 'Recently'}</p>

        ${pub.missionStatement ? `
          <p class="text-stone-300 text-sm italic line-clamp-3 mb-4">"${escapeHtml(truncate(pub.missionStatement, 120))}"</p>
        ` : ''}

        ${pub.primaryFocus ? `
          <div class="flex flex-wrap gap-1 mb-4">
            ${pub.primaryFocus.split(',').slice(0, 3).map(tag =>
              `<span class="px-2 py-0.5 bg-stone-700/50 text-stone-400 rounded text-xs">${escapeHtml(tag.trim())}</span>`
            ).join('')}
          </div>
        ` : ''}

        ${websiteLink}
      </article>
    `;
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

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
