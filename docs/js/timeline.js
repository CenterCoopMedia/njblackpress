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

    const isMobile = window.innerWidth < 768;
    const barGap = isMobile ? 'gap-[2px]' : 'gap-1';
    const chartHeight = isMobile ? 'h-[200px]' : 'h-[300px]';

    const html = `
      <div class="flex items-end justify-between ${chartHeight} w-full ${barGap}">
        ${decadeData.map((decade, index) => {
          const height = (decade.activeCount / maxCount) * 100;
          const barColor = decade.foundedCount > 0 ? 'bg-paper-100' : 'bg-paper-300';
          // Add accent if heavily active
          const activeClass = decade.activeCount > 5 ? 'group-hover:bg-accent' : 'group-hover:bg-accent/70';

          return `
            <div class="relative flex flex-col justify-end items-center h-full flex-1 group cursor-pointer timeline-bar-wrapper" data-decade="${decade.label}">
              <!-- Bar -->
              <div class="w-full mx-[2px] ${barColor} ${activeClass} transition-all duration-300 ease-out origin-bottom hover:scale-y-105"
                   style="height: ${Math.max(height, 5)}%">
              </div>

              <!-- Label -->
              <span class="absolute -bottom-8 font-mono text-[8px] md:text-[10px] text-paper-300 -rotate-45 group-hover:text-white transition-colors origin-top-left translate-x-1 md:translate-x-2">
                ${decade.label.replace('s', '')}
              </span>

              <!-- Tooltip -->
              <div class="timeline-tooltip absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-36 md:w-48 bg-ink-900 border border-white/10 p-3 md:p-4 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-2xl">
                <div class="font-serif text-base md:text-lg text-accent mb-1 font-bold">${decade.label}</div>
                <div class="text-xs font-mono text-paper-300 space-y-1 border-t border-white/10 pt-2">
                  <p><span class="text-white">${decade.activeCount}</span> Active</p>
                  <p><span class="text-white">${decade.foundedCount}</span> Founded</p>
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    container.innerHTML = html;
  }

  function setupEventListeners() {
    // Decade bar clicks - tap to show tooltip on mobile, double-tap or click to filter
    let lastTapped = null;
    document.querySelectorAll('.timeline-bar-wrapper[data-decade]').forEach(wrapper => {
      wrapper.addEventListener('click', (e) => {
        const isTouchDevice = 'ontouchstart' in window;
        const decade = wrapper.dataset.decade;

        if (isTouchDevice) {
          // On touch: first tap shows tooltip, second tap navigates
          if (lastTapped === wrapper) {
            // Second tap - navigate
            lastTapped = null;
            if (window.njbp && window.njbp.filterByDecade) {
              window.njbp.filterByDecade(decade);
            }
          } else {
            // First tap - show tooltip
            e.preventDefault();
            // Hide all other tooltips
            document.querySelectorAll('.timeline-tooltip').forEach(t => t.classList.remove('!opacity-100'));
            // Show this tooltip
            const tooltip = wrapper.querySelector('.timeline-tooltip');
            if (tooltip) tooltip.classList.add('!opacity-100');
            lastTapped = wrapper;
          }
        } else {
          if (window.njbp && window.njbp.filterByDecade) {
            window.njbp.filterByDecade(decade);
          }
        }
      });
    });

    // Decade nav buttons
    document.querySelectorAll('.timeline-decade-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const decade = btn.dataset.decade;
        showDecadeDetails(decade);

        // Update active state
        document.querySelectorAll('.timeline-decade-btn').forEach(b => {
             b.classList.remove('border-accent', 'text-accent');
             b.classList.add('border-white/20', 'text-paper-300');
        });
        btn.classList.remove('border-white/20', 'text-paper-300');
        btn.classList.add('border-accent', 'text-accent');
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

    // Show the details panel
    details.classList.remove('hidden');

    details.innerHTML = `
        <header class="flex justify-between items-start mb-6 border-b border-white/10 pb-4">
            <div>
                <h4 class="font-serif text-3xl text-white font-bold mb-1">${decade.label}</h4>
                <p class="font-mono text-xs text-accent uppercase tracking-widest">Historical Snapshot</p>
            </div>
            <div class="text-right font-mono text-xs text-paper-300">
                <p><span class="text-white text-lg">${decade.activeCount}</span> Active</p>
                <p><span class="text-white text-lg">${decade.foundedCount}</span> Founded</p>
            </div>
        </header>

        ${pubs.length > 0 ? `
          <div>
            <p class="font-mono text-xs text-paper-300 uppercase tracking-widest mb-3">Publications of Record</p>
            <div class="flex flex-wrap gap-2">
              ${pubs.slice(0, 15).map(p => `
                <span class="px-3 py-1 bg-white/5 border border-white/10 hover:border-accent hover:text-white text-paper-300 text-sm transition-colors cursor-default">${escapeHtml(p.name)}</span>
              `).join('')}
              ${pubs.length > 15 ? `<span class="px-3 py-1 text-paper-300 text-sm italic">+${pubs.length - 15} more...</span>` : ''}
            </div>
          </div>
        ` : '<p class="text-paper-300 italic font-serif">No publications recorded for this decade.</p>'}

        <div class="mt-8 pt-4 border-t border-white/10 text-center md:text-left">
            <button onclick="window.njbp.filterByDecade('${decade.label}')"
                    class="inline-block px-6 py-3 bg-paper-100 text-ink-950 hover:bg-accent hover:text-white font-mono text-xs font-bold uppercase tracking-widest transition-colors">
            View Full Decade Archive
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
