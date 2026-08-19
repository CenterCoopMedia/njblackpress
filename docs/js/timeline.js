/**
 * NJ Black Press Database - Timeline Visualization
 * Interactive decade-by-decade visualization of publication activity.
 *
 * Each decade bar is stacked (founded + ceased, honest proportions) and
 * carries an incident row of event dots beneath the axis. Issue #39.
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
  let events = [];
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
      console.error('Timeline: Failed to load publications data:', error);
    }

    try {
      const response = await fetch('data/events.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      events = data.events || [];
    } catch (error) {
      console.error('Timeline: Failed to load events data:', error);
    }
  }

  function yearOf(dateStr) {
    if (!dateStr) return null;
    const match = /^(\d{4})/.exec(dateStr);
    return match ? parseInt(match[1], 10) : null;
  }

  function calculateDecadeData() {
    decadeData = decades.map(decade => {
      // Publications active at any point during this decade
      const activePublications = publications.filter(pub => {
        const founded = pub.yearFounded || 9999;
        const ceased = pub.yearCeased || 2026;
        return founded <= decade.end && ceased >= decade.start;
      });

      const founded = publications.filter(pub =>
        pub.yearFounded >= decade.start && pub.yearFounded <= decade.end
      );

      const ceased = publications.filter(pub =>
        pub.yearCeased !== null && pub.yearCeased !== undefined &&
        pub.yearCeased >= decade.start && pub.yearCeased <= decade.end
      );

      const decadeEvents = events
        .filter(evt => {
          const y = yearOf(evt.date);
          return y !== null && y >= decade.start && y <= decade.end;
        })
        .sort((a, b) => (a.date > b.date ? 1 : a.date < b.date ? -1 : 0));

      const highCount = decadeEvents.filter(e => e.confidence === 'high').length;
      const mediumCount = decadeEvents.filter(e => e.confidence !== 'high').length;

      return {
        ...decade,
        activeCount: activePublications.length,
        foundedCount: founded.length,
        ceasedCount: ceased.length,
        publications: activePublications.slice(0, 5), // Top 5 for tooltip
        events: decadeEvents,
        eventCount: decadeEvents.length,
        highConfidenceCount: highCount,
        mediumConfidenceCount: mediumCount
      };
    });
  }

  function renderTimeline() {
    const container = document.getElementById('timeline-visualization');
    if (!container) return;

    const maxTotal = Math.max(...decadeData.map(d => d.foundedCount + d.ceasedCount), 1);

    const isMobile = window.innerWidth < 768;
    const barGap = isMobile ? 'gap-[2px]' : 'gap-1';
    const chartHeight = isMobile ? 'h-[180px]' : 'h-[260px]';

    const barsHtml = decadeData.map(decade => {
      const total = decade.foundedCount + decade.ceasedCount;
      const barHeightPct = (total / maxTotal) * 100;
      const foundedSegPct = total > 0 ? (decade.foundedCount / total) * 100 : 0;
      const ceasedSegPct = total > 0 ? (decade.ceasedCount / total) * 100 : 0;

      const ariaLabel = `${decade.label}: ${decade.foundedCount} founded, ${decade.ceasedCount} ceased, ` +
        `${decade.activeCount} publishing in the ${decade.label}, ${decade.eventCount} recorded event${decade.eventCount === 1 ? '' : 's'}. ` +
        `Press enter to filter the archive by this decade.`;

      return `
        <div class="relative flex flex-col justify-end items-center h-full flex-1 group timeline-bar-wrapper" data-decade="${decade.label}">
          <!-- Stacked bar: founded at the base, ceased above it -->
          <div class="w-full mx-[2px] flex flex-col justify-end pointer-events-none" style="height: ${Math.max(barHeightPct, total > 0 ? 2 : 0)}%">
            <div class="w-full bg-thread-500/40" style="height: ${ceasedSegPct}%"></div>
            <div class="w-full bg-stain border-l border-oak-500" style="height: ${foundedSegPct}%"></div>
          </div>

          <!-- Interactive overlay: keyboard + click target. min-w-[44px] widens the hit area
               without widening the visible bar (which is the separate element above). -->
          <button type="button"
                  class="timeline-bar absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-full min-w-[44px] bg-transparent border-0 p-0 cursor-pointer"
                  data-decade="${decade.label}"
                  aria-label="${escapeHtml(ariaLabel)}">
          </button>

          <!-- Tooltip -->
          <div class="timeline-tooltip absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-40 md:w-52 bg-walnut-900 border border-walnut-600 p-3 md:p-4 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-2xl">
            <div class="font-display text-base md:text-lg text-stain mb-1 font-bold">${decade.label}</div>
            <div class="text-xs font-mono text-linen-300 space-y-1 border-t border-walnut-600 pt-2">
              <p><span class="text-linen-50">${decade.foundedCount}</span> founded</p>
              <p><span class="text-linen-50">${decade.ceasedCount}</span> ceased</p>
              <p><span class="text-linen-50">${decade.activeCount}</span> publishing in the ${decade.label}</p>
              <p><span class="text-linen-50">${decade.eventCount}</span> recorded event${decade.eventCount === 1 ? '' : 's'}</p>
            </div>
          </div>
        </div>
      `;
    }).join('');

    const incidentsHtml = decadeData.map(decade => {
      const dots = decade.events.map(evt => {
        return evt.confidence === 'high'
          ? `<span class="w-[5px] h-[5px] rounded-full bg-stain" aria-hidden="true"></span>`
          : `<span class="w-[5px] h-[5px] rounded-full border border-dashed border-stain bg-transparent" aria-hidden="true"></span>`;
      }).join('');

      const incidentAria = decade.eventCount === 0
        ? `${decade.label}: no recorded events.`
        : `${decade.label} events: ${decade.eventCount} recorded, ${decade.highConfidenceCount} high confidence, ` +
          `${decade.mediumConfidenceCount} medium confidence. Press enter to read the list.`;

      return `
        <button type="button"
                class="incident-btn flex-1 flex flex-wrap gap-[2px] content-start justify-center items-start mx-[2px] min-h-[22px] bg-transparent border-0 p-1 ${decade.eventCount === 0 ? 'cursor-default opacity-30' : 'cursor-pointer'}"
                data-decade="${decade.label}"
                aria-label="${escapeHtml(incidentAria)}"
                ${decade.eventCount === 0 ? 'disabled' : ''}>
          ${dots}
        </button>
      `;
    }).join('');

    // Issue #44 finding 4: below 768px the per-decade dot buttons are too
    // narrow to tap (14px wide across 15 decades). Replace them with a
    // stacked list of full-width buttons, one per decade that has events.
    const mobileEventsHtml = decadeData
      .filter(decade => decade.eventCount > 0)
      .map(decade => `
        <button type="button"
                class="mobile-decade-events-btn w-full text-left px-4 py-3 min-h-[44px] bg-walnut-800/60 border border-walnut-600 text-linen-100 font-sans text-sm hover:border-stain transition-colors"
                data-decade="${decade.label}">
          Read the ${decade.eventCount} event${decade.eventCount === 1 ? '' : 's'} from the ${decade.label}
        </button>
      `).join('');

    const labelsHtml = decadeData.map(decade => `
      <span class="flex-1 text-center font-mono text-[8px] md:text-[10px] text-linen-300 whitespace-nowrap">
        ${decade.label}
      </span>
    `).join('');

    const html = `
      <div class="flex items-end justify-between ${chartHeight} w-full ${barGap}">
        ${barsHtml}
      </div>
      <div class="rail-wood w-full mt-2"></div>
      <div class="hidden md:flex items-start justify-between w-full ${barGap} mt-2" role="group" aria-label="Recorded events by decade">
        ${incidentsHtml}
      </div>
      <div class="flex md:hidden flex-col gap-2 mt-4" role="group" aria-label="Recorded events by decade">
        ${mobileEventsHtml || '<p class="font-sans text-sm text-linen-300">No recorded events yet.</p>'}
      </div>
      <div class="flex justify-between w-full ${barGap} mt-2">
        ${labelsHtml}
      </div>
    `;

    container.innerHTML = html;
  }

  function announce(text) {
    const live = document.getElementById('timeline-live');
    if (live) live.textContent = text;
  }

  // Issue #44 finding 8: respect prefers-reduced-motion when scrolling
  // a revealed panel into view.
  function scrollBehavior() {
    const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return reduced ? 'auto' : 'smooth';
  }

  function setupEventListeners() {
    const barButtons = Array.from(document.querySelectorAll('.timeline-bar[data-decade]'));

    barButtons.forEach((btn, index) => {
      btn.addEventListener('click', () => {
        const decade = btn.dataset.decade;
        if (window.njbp && window.njbp.filterByDecade) {
          window.njbp.filterByDecade(decade);
        }
      });

      btn.addEventListener('focus', () => {
        const decade = decadeData.find(d => d.label === btn.dataset.decade);
        if (decade) {
          announce(`${decade.label}: ${decade.foundedCount} founded, ${decade.ceasedCount} ceased, ${decade.activeCount} publishing in the ${decade.label}, ${decade.eventCount} recorded events.`);
        }
      });

      btn.addEventListener('mouseenter', () => {
        const decade = decadeData.find(d => d.label === btn.dataset.decade);
        if (decade) {
          announce(`${decade.label}: ${decade.foundedCount} founded, ${decade.ceasedCount} ceased, ${decade.activeCount} publishing in the ${decade.label}, ${decade.eventCount} recorded events.`);
        }
      });

      btn.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') {
          e.preventDefault();
          const next = barButtons[index + 1];
          if (next) next.focus();
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          const prev = barButtons[index - 1];
          if (prev) prev.focus();
        } else if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          btn.click();
        }
      });
    });

    const incidentButtons = Array.from(document.querySelectorAll('.incident-btn[data-decade]'));
    incidentButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.disabled) return;
        showDecadeEvents(btn.dataset.decade);
      });
      btn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          btn.click();
        }
      });
    });

    // Mobile full-width "Read the N events from the 1930s" buttons (finding 4)
    document.querySelectorAll('.mobile-decade-events-btn[data-decade]').forEach(btn => {
      btn.addEventListener('click', () => showDecadeEvents(btn.dataset.decade));
    });

    // Decade nav buttons
    document.querySelectorAll('.timeline-decade-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const decade = btn.dataset.decade;
        showDecadeDetails(decade);

        // Update active state
        document.querySelectorAll('.timeline-decade-btn').forEach(b => {
             b.classList.remove('border-accent', 'text-accent');
             b.classList.add('border-walnut-600', 'text-paper-300');
        });
        btn.classList.remove('border-walnut-600', 'text-paper-300');
        btn.classList.add('border-accent', 'text-accent');
      });
    });
  }

  function showDecadeDetails(decadeLabel) {
    const details = document.getElementById('timeline-details');
    if (!details) return;

    const decade = decadeData.find(d => d.label === decadeLabel + 's' || d.label === decadeLabel);
    const resolved = decade || decadeData.find(d => d.start === parseInt(decadeLabel, 10));
    if (!resolved) return;

    const pubs = publications.filter(pub => {
      const founded = pub.yearFounded || 9999;
      const ceased = pub.yearCeased || 2026;
      return founded <= resolved.end && ceased >= resolved.start;
    });

    // Show the details panel
    details.classList.remove('hidden');

    details.innerHTML = `
        <header class="flex justify-between items-start mb-6 border-b border-walnut-600 pb-4">
            <div>
                <h4 class="font-display text-3xl text-linen-50 font-bold mb-1">${resolved.label}</h4>
            </div>
            <div class="text-right font-mono text-xs text-paper-300">
                <p><span class="text-linen-50 text-lg">${resolved.activeCount}</span> active</p>
                <p><span class="text-linen-50 text-lg">${resolved.foundedCount}</span> founded</p>
            </div>
        </header>

        ${pubs.length > 0 ? `
          <div>
            <p class="font-mono text-xs text-paper-300 uppercase tracking-widest mb-3">Publications of record</p>
            <div class="flex flex-wrap gap-2">
              ${pubs.slice(0, 15).map(p => `
                <span class="px-3 py-1 bg-walnut-700 border border-walnut-600 hover:border-accent hover:text-linen-50 text-paper-300 text-sm transition-colors cursor-default">${escapeHtml(p.name)}</span>
              `).join('')}
              ${pubs.length > 15 ? `<span class="px-3 py-1 text-paper-300 text-sm">+${pubs.length - 15} more</span>` : ''}
            </div>
          </div>
        ` : '<p class="text-paper-300 font-sans">No publications recorded for this decade.</p>'}

        <div class="mt-8 pt-4 border-t border-walnut-600 text-center md:text-left">
            <button onclick="window.njbp.filterByDecade('${resolved.label}')"
                    class="inline-block px-6 py-3 bg-linen-100 text-walnut-950 hover:bg-stain hover:text-walnut-950 font-mono text-xs font-bold uppercase tracking-widest transition-colors">
            View full decade archive
            </button>
        </div>
    `;

    details.scrollIntoView({ behavior: scrollBehavior(), block: 'nearest' });
  }

  // Issue #44 finding 21: events.json has no separate "sourcing note" field —
  // verification prose (source disagreements, unresolved dates, house boasts
  // the archive hasn't confirmed) is written inline as sentences inside
  // `description`. We detect those sentences by content and move them into
  // a <details> disclosure so the main description reads clean.
  const SOURCING_NOTE_PATTERNS = [
    /sources? (conflict|disagree|differ)/i,
    /no (read )?source (gives|dates|names|confirms)/i,
    /the archive has (not|n't) verified/i,
    /has not been verified/i,
    /is unsettled/i,
    /is not settled/i,
    /not (part of )?this event/i,
    /a house boast/i,
    /remains unclear/i,
    /unverified/i,
    /length of its run is/i
  ];

  function splitSourcingNote(description) {
    if (!description) return { main: '', note: '' };
    // Split into sentences, keeping the trailing period with each sentence.
    const sentences = description.match(/[^.]+\.(?=\s|$)|[^.]+$/g) || [description];
    const main = [];
    const note = [];
    sentences.forEach(sentence => {
      const trimmed = sentence.trim();
      if (!trimmed) return;
      const isNote = SOURCING_NOTE_PATTERNS.some(pattern => pattern.test(trimmed));
      (isNote ? note : main).push(trimmed);
    });
    return { main: main.join(' '), note: note.join(' ') };
  }

  function showDecadeEvents(decadeLabel) {
    const details = document.getElementById('timeline-details');
    if (!details) return;

    const decade = decadeData.find(d => d.label === decadeLabel);
    if (!decade) return;

    details.classList.remove('hidden');

    const listItems = decade.events.map(evt => {
      const isMedium = evt.confidence !== 'high';
      const { main, note } = splitSourcingNote(evt.description);

      // Finding 20: link resolvable publicationIds to their detail page.
      const relatedPubs = (evt.publicationIds || [])
        .map(pid => publications.find(p => p.id === pid))
        .filter(Boolean);
      const relatedHtml = relatedPubs.length > 0
        ? `<p class="font-mono text-xs text-paper-300 mt-2">Publication: ${relatedPubs.map(p =>
            `<a href="publication.html?id=${p.id}" class="link-thread hover:text-accent">${escapeHtml(p.name)}</a>`
          ).join(', ')}</p>`
        : '';

      const noteHtml = note
        ? `<details class="mt-2">
             <summary class="font-mono text-[10px] uppercase tracking-widest text-linen-300 cursor-pointer hover:text-stain">Sourcing note</summary>
             <p class="font-sans text-sm text-paper-300 leading-relaxed mt-2">${escapeHtml(note)}</p>
           </details>`
        : '';

      return `
        <li class="border-b border-walnut-600 py-4 first:pt-0 last:border-0">
          <div class="flex items-baseline gap-3 flex-wrap">
            <span class="font-mono text-xs text-stain">${escapeHtml(evt.date)}</span>
            ${isMedium ? '<span class="font-mono text-[10px] uppercase tracking-widest text-linen-300 border-b border-dashed border-stain pb-0.5">Medium confidence</span>' : ''}
          </div>
          <h5 class="font-display text-lg md:text-xl text-linen-50 font-bold mt-1 mb-1">${escapeHtml(evt.title)}</h5>
          <p class="font-sans text-sm text-paper-300 leading-relaxed">${escapeHtml(main)}</p>
          ${relatedHtml}
          ${noteHtml}
        </li>
      `;
    }).join('');

    details.innerHTML = `
        <header class="flex justify-between items-start mb-6 border-b border-walnut-600 pb-4">
            <div>
                <h4 class="font-display text-3xl text-linen-50 font-bold mb-1">${decade.label} events</h4>
            </div>
            <div class="text-right font-mono text-xs text-paper-300">
                <p><span class="text-linen-50 text-lg">${decade.eventCount}</span> recorded</p>
                <p><span class="text-linen-50 text-lg">${decade.mediumConfidenceCount}</span> medium confidence</p>
            </div>
        </header>

        ${decade.events.length > 0
          ? `<ol class="divide-y divide-walnut-600">${listItems}</ol>`
          : '<p class="text-paper-300 font-sans">No recorded events for this decade.</p>'}
    `;

    details.scrollIntoView({ behavior: scrollBehavior(), block: 'start' });
    announce(`Showing ${decade.eventCount} recorded events for ${decade.label}.`);
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // Expose for the incident row and console debugging
  window.njbpTimeline = { showDecadeEvents, showDecadeDetails };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
