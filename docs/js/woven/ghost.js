// Woven — the ghost cloth. Nobody gets ambushed by a memorial: every trigger
// is explicit and the sequence is interruptible at any moment.

import { announce, syncTwin } from './twin.js';

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const GROUP = 6;
const GROUP_MS = 2400;

export function createGhost(app, three, model) {
  const { stateTex, weftGhost } = three;
  const cardEl = document.getElementById('woven-ghostcard');
  const namesEl = document.getElementById('woven-ghostnames');

  const ghosts = model.threads
    .filter((t) => t.ghost)
    .sort((a, b) => (a.yearFounded ?? 9999) - (b.yearFounded ?? 9999) || a.name.localeCompare(b.name));

  let playing = false;
  let timer = null;
  let preView = null;
  let groupIndex = 0;

  const api = {
    get isPlaying() { return playing; },
    get userMoved() { return playing && groupIndex > 0; },
    start, exit
  };

  function reduced() { return app.reduceMotion.matches; }

  async function start() {
    if (playing) return;
    playing = true;
    groupIndex = 0;
    app.userMoved = false;
    preView = {
      target: [three.controls.target.x, three.controls.target.y, 0],
      position: [three.camera.position.x, three.camera.position.y, three.camera.position.z]
    };
    history.replaceState(null, '', '?ghost=1');

    showCard('open');
    announce(`${model.counts.ghost} of these papers exist now as a single line in a catalog. Their names follow.`);

    // Dim everything that is not a ghost.
    for (const t of model.threads) {
      stateTex.set(t.threadIndex, 1, t.ghost ? 0 : 224);
      stateTex.set(t.threadIndex, 0, 0);
      stateTex.set(t.threadIndex, 2, t.ghost ? 255 : 0);
    }
    stateTex.commit();
    app.needsRender = true;

    if (reduced()) {
      // One state change plus the full list. No camera move, no timed reveal.
      weftGhost.material.uniforms.uFrayCut.value = 0.35;
      renderNames(ghosts, true);
      cardEl.hidden = true;
      namesEl.hidden = false;
      return;
    }

    await app.easeTo(
      [(app.loomBox.minX + app.loomBox.maxX) / 2, (app.loomBox.minY + app.loomBox.maxY) / 2],
      app.fitDistance(app.loomBox, 0.02), 1400
    );
    await animateFray();
    cardEl.hidden = true;
    namesEl.hidden = false;
    runGroups();
  }

  function animateFray() {
    return new Promise((resolve) => {
      const t0 = performance.now();
      const tick = () => {
        if (!playing) return resolve();
        const k = Math.min(1, (performance.now() - t0) / 600);
        weftGhost.material.uniforms.uFrayCut.value = 0.35 * k;
        app.needsRender = true;
        if (k < 1) requestAnimationFrame(tick); else resolve();
      };
      requestAnimationFrame(tick);
    });
  }

  function runGroups() {
    if (!playing) return;
    const slice = ghosts.slice(groupIndex * GROUP, groupIndex * GROUP + GROUP);
    if (!slice.length) { showCard('close'); return; }
    stateTex.clear(0, 0);
    for (const t of slice) stateTex.set(t.threadIndex, 0, 180);
    stateTex.commit();
    app.needsRender = true;
    renderNames(slice, false);
    app.state.ghostGroup = slice.map((t) => t.id);
    syncTwin(app.state);
    announce(slice.map((t) => t.name).join('. '));
    groupIndex++;
    timer = setTimeout(runGroups, GROUP_MS);
  }

  function renderNames(list, all) {
    namesEl.innerHTML = `<ol>${list.map((t) => `<li><span class="g-name">${esc(t.name)}</span>
      <span class="g-place">${esc(t.city || 'city unrecorded')}${t.yearFounded ? ` · ${t.yearFounded}` : ''}</span></li>`).join('')}</ol>`
      + (all ? '' : `<p class="g-place">${(groupIndex + 1) * GROUP} of ${ghosts.length}</p>`);
  }

  function showCard(which) {
    if (which === 'open') {
      cardEl.innerHTML = `<div class="inner">
        <h3>What did not survive</h3>
        <p>${model.counts.ghost} of these papers exist now as a single line in a catalog — a title, a city, a range of years, recorded by a librarian who held the issue we cannot find. No page, no masthead, no photograph. They are woven into the same cloth as everything else, thin and unfinished, because an absence in the record is not an absence in the history. Their names follow.</p>
        <p><button type="button" class="woven-btn" data-act="skip">Skip to the list</button></p>
      </div>`;
      cardEl.hidden = false;
      cardEl.querySelector('[data-act="skip"]').addEventListener('click', () => {
        cardEl.hidden = true;
        namesEl.hidden = false;
      });
    } else {
      cardEl.innerHTML = `<div class="inner">
        <h3>That is what the record lost.</h3>
        <p>It is not the same as what happened.</p>
        <p><button type="button" class="woven-btn" data-act="back">Return to the loom</button>
           <button type="button" class="woven-btn" data-act="list">Read the list again</button></p>
      </div>`;
      cardEl.hidden = false;
      cardEl.querySelector('[data-act="back"]').addEventListener('click', exit);
      cardEl.querySelector('[data-act="list"]').addEventListener('click', () => {
        exit();
        document.getElementById('woven-twin-ghost').scrollIntoView({ block: 'start' });
      });
      cardEl.querySelector('[data-act="back"]').focus();
    }
  }

  function exit() {
    if (!playing) return;
    playing = false;
    if (timer) { clearTimeout(timer); timer = null; }
    cardEl.hidden = true;
    namesEl.hidden = true;
    weftGhost.material.uniforms.uFrayCut.value = 0.22;
    stateTex.clear(0, 0);
    stateTex.clear(1, 0);
    stateTex.clear(2, 0);
    stateTex.commit();
    app.state.ghostGroup = null;
    syncTwin(app.state);
    history.replaceState(null, '', location.pathname);
    if (preView) app.applyView(preView);
    app.needsRender = true;
  }

  return api;
}
