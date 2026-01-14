/**
 * NJ Black Press Database - Timeline Visualization
 * Interactive decade-by-decade visualization of publication activity
 */

(function() {
  'use strict';

  const decades = [
    { label: '1880s', start: 1880, end: 1889 },
    { label: '1890s', start: 1890, end: 1899 },
    { label: '1900s', start: 1900, end: 1909 },
    { label: '1910s', start: 1910, end: 1919 },
    { label: '1920s', start: 1920, end: 1929 },
    { label: '1930s', start: 1930, end: 1939 },
    { label: '1940s', start: 1940, end: 1949 },
    { label: '1950s', start: 1950, end: 1959 },
    { label: '1960s', start: 1960, end: 1969 },
    { label: '1970s', start: 1970, end: 1979 },
    { label: '1980s', start: 1980, end: 1989 },
    { label: '1990s', start: 1990, end: 1999 },
    { label: '2000s', start: 2000, end: 2009 },
    { label: '2010s', start: 2010, end: 2019 },
    { label: '2020s', start: 2020, end: 2029 }
  ];

  let publications = [];
  let decadeData = [];

  async function init() {
    await loadData();
    calculateDecadeData();
    renderTimeline();
    setupEventListeners();
  }

  async function loadData() {
    try {
      const response = await fetch('data/publications.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      publications = data.publications || [];
    } catch (error) {
      console.error('Timeline: Failed to load data:', error);
    }
  }

  function calculateDecadeData() {
    decadeData = decades.map(decade => {
      // Count publications that were active during this decade
      const activePublications = publications.filter(pub => {
        const founded = pub.yearFounded || 9999;
        const ceased = pub.yearCeased || 2026;
        return founded <= decade.end && ceased >= decade.start;
      });

      const founded = publications.filter(pub =>
        pub.yearFounded >= decade.start && pub.yearFounded <= decade.end
      );

      return {
        ...decade,
        activeCount: activePublications.length,
        foundedCount: founded.length,
        publications: activePublications.slice(0, 5) // Top 5 for tooltip
      };
    });
  }

  function renderTimeline() {
    const container = document.getElementById('timeline-visualization');
    if (!container) return;

    const maxCount = Math.max(...decadeData.map(d => d.activeCount), 1);

    const html = `
      <div class="timeline-chart">
        ${decadeData.map((decade, index) => {
          const height = (decade.activeCount / maxCount) * 100;
          const barColor = decade.foundedCount > 0 ? 'bg-amber-500' : 'bg-stone-600';

          return `
            <div class="timeline-bar-wrapper group" data-decade="${decade.label}">
              <div class="timeline-bar-container">
                <div class="timeline-bar ${barColor}" style="height: ${Math.max(height, 5)}%">
                  <span class="timeline-count">${decade.activeCount}</span>
                </div>
              </div>
              <span class="timeline-label">${decade.label.replace('s', '')}</span>

              <!-- Tooltip -->
              <div class="timeline-tooltip">
                <div class="font-semibold text-amber-400 mb-1">${decade.label}</div>
                <div class="text-sm text-stone-300">
                  <p>${decade.activeCount} active publication${decade.activeCount !== 1 ? 's' : ''}</p>
                  <p>${decade.foundedCount} founded this decade</p>
                </div>
                ${decade.publications.length > 0 ? `
                  <div class="mt-2 pt-2 border-t border-stone-600">
                    <p class="text-xs text-stone-400 mb-1">Notable:</p>
                    <ul class="text-xs text-stone-300">
                      ${decade.publications.slice(0, 3).map(p => `<li>• ${escapeHtml(p.name)}</li>`).join('')}
                    </ul>
                  </div>
                ` : ''}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    container.innerHTML = html;
  }

  function setupEventListeners() {
    // Decade bar clicks
    document.querySelectorAll('.timeline-bar-wrapper').forEach(wrapper => {
      wrapper.addEventListener('click', () => {
        const decade = wrapper.dataset.decade;
        if (window.njbp && window.njbp.filterByDecade) {
          window.njbp.filterByDecade(decade);
        }
      });
    });

    // Decade nav buttons
    document.querySelectorAll('.timeline-decade-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const decade = btn.dataset.decade;
        showDecadeDetails(decade);

        // Update active state
        document.querySelectorAll('.timeline-decade-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }

  function showDecadeDetails(decadeLabel) {
    const details = document.getElementById('timeline-details');
    if (!details) return;

    const decade = decadeData.find(d => d.label === decadeLabel);
    if (!decade) return;

    const pubs = publications.filter(pub => {
      const founded = pub.yearFounded || 9999;
      const ceased = pub.yearCeased || 2026;
      return founded <= decade.end && ceased >= decade.start;
    });

    details.innerHTML = `
      <div class="bg-stone-800/50 rounded-lg p-6 border border-stone-700/50">
        <h4 class="font-serif text-xl text-amber-400 mb-4">${decade.label}</h4>
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p class="text-3xl font-bold text-stone-100">${decade.activeCount}</p>
            <p class="text-sm text-stone-400">Active publications</p>
          </div>
          <div>
            <p class="text-3xl font-bold text-stone-100">${decade.foundedCount}</p>
            <p class="text-sm text-stone-400">Founded this decade</p>
          </div>
        </div>

        ${pubs.length > 0 ? `
          <div class="space-y-2">
            <p class="text-sm text-stone-400 mb-2">Publications active during this period:</p>
            <div class="flex flex-wrap gap-2">
              ${pubs.slice(0, 10).map(p => `
                <span class="px-2 py-1 bg-stone-700/50 text-stone-300 rounded text-sm">${escapeHtml(p.name)}</span>
              `).join('')}
              ${pubs.length > 10 ? `<span class="px-2 py-1 text-stone-500 text-sm">+${pubs.length - 10} more</span>` : ''}
            </div>
          </div>
        ` : '<p class="text-stone-500">No publications recorded for this decade.</p>'}

        <button onclick="window.njbp.filterByDecade('${decade.label}')"
                class="mt-4 px-4 py-2 bg-amber-500 text-stone-900 rounded hover:bg-amber-400 transition-colors text-sm font-medium">
          View all ${decade.label} publications
        </button>
      </div>
    `;
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
