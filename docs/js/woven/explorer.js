// Direct access to every thread, without requiring precision canvas picking.
export function createExplorer(app, model) {
  const stage = document.getElementById('woven-stage');
  const browse = document.getElementById('btn-browse');
  const desktop = window.matchMedia('(min-width: 900px)');
  const element = document.createElement('aside');
  element.id = 'woven-legend';
  element.innerHTML = `
    <div class="explorer-heading"><h2>Follow a thread</h2>
      <button type="button" class="woven-btn lg-toggle">Close</button></div>
    <div class="lg-body">
      <p class="explorer-instruction">Choose a founding era or a publication.</p>
      <div class="woven-era-grid" role="group" aria-label="Founding era"></div>
      <p class="explorer-scope" role="status"></p>
      <ol class="explorer-list" aria-label="Publications"></ol>
      <details class="explorer-key"><summary>How to read the threads</summary>
        <p>Left to right is time. Color identifies the founding era. Thickness shows the number of evidence records.</p>
        <ul>
          <li><span class="key-line"></span>Solid: recorded dates</li>
          <li><span class="key-line key-dash"></span>Dashed: end date unknown</li>
          <li><span class="key-line key-faint"></span>Faint: no evidence cleared for display</li>
        </ul>
        <p>Loose ends: still publishing. Rings: documented events. Undated titles appear as separated stitches.</p>
        <p>A dashed span does not establish continuous publication. Display rights do not tell us how much material survives.</p>
      </details>
    </div>`;
  stage.appendChild(element);
  const eraGrid = element.querySelector('.woven-era-grid');
  const list = element.querySelector('.explorer-list');
  const scopeLabel = element.querySelector('.explorer-scope');
  let lastSelection = null;
  let lastHover = null;
  let open = false;
  const buttons = new Map();

  function setOpen(value, restoreFocus = false) {
    open = value;
    element.dataset.collapsed = String(!desktop.matches && !open);
    browse.setAttribute('aria-expanded', String(desktop.matches || open));
    if (restoreFocus) browse.focus({ preventScroll: true });
  }
  browse.addEventListener('click', () => {
    setOpen(!open);
    if (open) element.querySelector('.lg-toggle').focus({ preventScroll: true });
  });
  element.querySelector('.lg-toggle').addEventListener('click', () => setOpen(false, true));
  element.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !desktop.matches) {
      event.stopPropagation();
      setOpen(false, true);
    }
  });
  desktop.addEventListener('change', () => setOpen(false));
  setOpen(false);

  for (const band of [{ key: 'all', count: model.counts.total }, ...model.bands.filter((b) => b.count)]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'era-choice';
    button.dataset.band = band.key;
    const swatch = document.createElement('span');
    swatch.className = 'era-swatch';
    swatch.setAttribute('aria-hidden', 'true');
    swatch.style.background = band.threads?.[0]?.dye || '#f5f6f8';
    const label = document.createElement('span');
    label.textContent = band.key === 'all' ? 'All years' : band.from == null ? 'Undated' : `${band.from}–${band.to}`;
    const count = document.createElement('span');
    count.className = 'era-count';
    count.textContent = band.count;
    button.append(swatch, label, count);
    button.addEventListener('click', () => {
      if (band.key === 'all') app.resetView();
      else app.focusBand(band.key);
    });
    eraGrid.appendChild(button);
  }

  function scope(key) {
    const band = model.bands.find((b) => b.key === key);
    const threads = band ? band.threads : model.layout.slots;
    eraGrid.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.band === key)));
    scopeLabel.textContent = `${threads.length} publication${threads.length === 1 ? '' : 's'}${band ? ` · ${band.from == null ? 'Undated' : band.label}` : ' · All years'}`;
    list.replaceChildren();
    buttons.clear();
    for (const t of threads) {
      const row = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'explorer-publication';
      const name = document.createElement('strong');
      name.textContent = t.name;
      const meta = document.createElement('span');
      const end = t.endState === 'still' ? 'present' : t.yearCeased ?? '?';
      meta.textContent = `${t.city || 'City unrecorded'} · ${t.yearFounded == null ? 'Undated' : `${t.yearFounded}–${end}`}`;
      button.append(name, meta);
      button.addEventListener('click', () => {
        if (!desktop.matches) setOpen(false);
        app.select(t.id, {});
      });
      buttons.set(t.id, button);
      row.appendChild(button);
      list.appendChild(row);
    }
    lastSelection = null;
    lastHover = null;
    sync(true);
  }

  function sync(force = false) {
    const { selectedId, hoverId } = app.state;
    if (!force && selectedId === lastSelection && hoverId === lastHover) return;
    for (const [id, button] of buttons) {
      button.setAttribute('aria-pressed', String(id === selectedId));
      button.classList.toggle('is-hover', id === hoverId);
    }
    if (selectedId !== lastSelection) {
      const button = buttons.get(selectedId);
      if (button) list.scrollTop += button.getBoundingClientRect().top - list.getBoundingClientRect().top - 12;
    }
    lastSelection = selectedId;
    lastHover = hoverId;
  }
  scope('all');
  return { element, scope, sync };
}
