// Woven — DOM labels, era markers, and the legend.
// All type is HTML. Nothing is ever drawn into the canvas.

import * as THREE from 'three';
import { x as xOf, YEAR_MIN, YEAR_MAX } from './layout.js';

const MAX_LABELS = 26;
const LABEL_DISTANCE = 26;   // beyond this the cloth is a shape, not a list
const MIN_ROW_PX = 24;       // a label is 23px tall, so anything less overlaps
const MIN_COMPACT_PX = 17;   // the compact era marker is 16px tall

export function createLabels(app, three, model) {
  const stage = document.getElementById('woven-stage');

  const layer = document.createElement('div');
  layer.id = 'woven-labels';
  layer.setAttribute('aria-hidden', 'true');
  stage.appendChild(layer);

  const eraLayer = document.createElement('div');
  eraLayer.id = 'woven-eras';
  eraLayer.setAttribute('aria-hidden', 'true');
  stage.appendChild(eraLayer);

  const legend = document.createElement('div');
  legend.id = 'woven-legend';
  // The toggle is the first child, so on a narrow window — where the key floats
  // over the cloth and the copy runs longer than the panel is tall — the way to
  // close it is at the top rather than under a scroll nobody can see.
  legend.innerHTML = `
    <button type="button" class="woven-btn lg-toggle" aria-expanded="true">Hide the key</button>
    <div class="lg-body">
      <p class="lg-lede">Each horizontal thread is one publication. It starts the year the paper was founded and ends the year it stopped. Left to right is 1880 to 2026.</p>
      <ul>
        <li><span class="lg-swatch lg-thick"></span>Thicker thread — more surviving material we can show you</li>
        <li><span class="lg-swatch lg-ghost"></span>Faint and frayed — ${model.counts.ghost} titles we know only from a catalog line</li>
        <li><span class="lg-swatch lg-loose"></span>Runs past the right post — the ${model.counts.stillPublishing} papers still publishing</li>
        <li><span class="lg-swatch lg-knot"></span>Knot — a documented event, ${model.counts.events} in all</li>
      </ul>
      <p class="lg-rows">Rows are grouped by the decade each paper began. Names appear when you are close enough to read them.</p>
      <p class="lg-rows">Drag to move across the cloth. Scroll or pinch to zoom. Type a name in the search field and the loom goes to the closest match; press enter to go there at once.</p>
    </div>`;
  stage.appendChild(legend);

  // Above 900px the key is docked in its own column beside the canvas and is
  // always open. Below that it floats over the cloth, so it starts closed and
  // the toggle reports the state it is actually in. The window can cross that
  // line at any moment, so the state follows the media query, not the width the
  // page happened to load at.
  const toggle = legend.querySelector('.lg-toggle');
  const dock = window.matchMedia('(min-width: 900px)');
  let openedByReader = false;

  function setCollapsed(collapsed) {
    legend.dataset.collapsed = String(collapsed);
    toggle.textContent = collapsed ? 'Show the key' : 'Hide the key';
    toggle.setAttribute('aria-expanded', String(!collapsed));
  }

  function applyDock() {
    // Docked: always open, and the toggle is hidden. Floating: closed unless the
    // reader opened it at this width, because an open key covers the cloth.
    setCollapsed(dock.matches ? false : !openedByReader);
  }

  toggle.addEventListener('click', () => {
    const nowCollapsed = legend.dataset.collapsed !== 'true';
    openedByReader = !nowCollapsed;
    setCollapsed(nowCollapsed);
    update();
  });

  dock.addEventListener('change', () => {
    openedByReader = false;
    applyDock();
    update();
  });
  applyDock();

  const v = new THREE.Vector3();
  let rect = null;
  let eraBoxes = [];
  // The band of canvas that type may occupy, measured from the control bars and
  // the year rail. The bars wrap to two rows on a narrow window, so their height
  // is read, never assumed.
  let guard = { top: 92, bottom: 44 };

  // The bars wrap and the tour bar comes and goes, so every keep-out band is
  // measured, never assumed. The measurements are also published on the stage as
  // custom properties: the cards, the ghost list, and the notice are positioned
  // from them in CSS, so nothing is ever printed under a control.
  function measureGuard() {
    const chrome = document.getElementById('woven-chrome');
    const rail = document.getElementById('woven-yearrail');
    const tourbar = document.getElementById('woven-tourbar');
    const chromeH = chrome ? chrome.getBoundingClientRect().height : 88;
    const railH = rail ? rail.getBoundingClientRect().height : 26;
    const tourH = tourbar && !tourbar.hidden ? tourbar.getBoundingClientRect().height : 0;
    stage.style.setProperty('--woven-chrome-h', `${Math.round(chromeH)}px`);
    stage.style.setProperty('--woven-rail-h', `${Math.round(railH)}px`);
    stage.style.setProperty('--woven-tourbar-h', `${Math.round(tourH)}px`);
    guard = { top: chromeH + 6, bottom: Math.max(railH, tourH) + 18 };
  }
  app.measureChrome = measureGuard;

  function project(x, y) {
    v.set(x, y, 0).project(three.camera);
    return {
      x: ((v.x + 1) / 2) * rect.width,
      y: ((1 - v.y) / 2) * rect.height,
      onScreen: v.z < 1 && v.x > -1.1 && v.x < 1.1 && v.y > -1.1 && v.y < 1.1
    };
  }

  function update() {
    rect = three.canvas.getBoundingClientRect();
    measureGuard();
    const dist = three.camera.position.distanceTo(three.controls.target);
    const busy = !!(app.tour && app.tour.isPlaying) || !!(app.ghost && app.ghost.isPlaying);
    const widthChanged = stage.classList.contains('woven-legend-hidden') !== busy;
    stage.classList.toggle('woven-legend-hidden', busy);
    legend.hidden = busy;
    if (widthChanged && app.resize) requestAnimationFrame(() => app.resize());
    const ghosting = !!(app.ghost && app.ghost.isPlaying);
    // The era markers stay through the ghost roll. They are the only thing
    // saying which decade each name belongs to, and the roll is a list of names.
    if (ghosting) { layer.textContent = ''; eraBoxes = []; drawEras(); drawYears(); return; }
    drawEras();
    drawYears();
    if (busy && app.tour && app.tour.isPlaying) {
      // During a tour only the tour's own threads are named. Everything else is
      // already dimmed; naming it would fight the story for attention.
      drawNames(dist, new Set(model.tours.find((t) => t.id === app.state.tourId)?.threadIds || []));
      layer.dataset.mode = 'tour';
      cullEras();
      return;
    }
    if (dist > LABEL_DISTANCE) {
      layer.textContent = '';
      layer.dataset.mode = 'far';
      cullEras();
      return;
    }
    layer.dataset.mode = 'near';
    drawNames(dist);
    cullEras();
  }

  // A publication name carries a title, a city, and two dates; a group label
  // carries a decade and a count. Where the two land on the same line the name
  // wins and the group label is taken away for that frame.
  function cullEras() {
    const marks = Array.from(eraLayer.children);
    if (!marks.length) return;
    const names = Array.from(layer.children).map((el) => el.getBoundingClientRect());
    for (const m of marks) {
      let hidden = false;
      if (names.length) {
        const b = m.getBoundingClientRect();
        hidden = names.some((l) =>
          l.left < b.right + 6 && l.right > b.left - 6 &&
          l.top < b.bottom + 2 && l.bottom > b.top - 2);
      }
      m.style.visibility = hidden ? 'hidden' : '';
    }
  }

  // A marker's height depends on its own text, on the type size in force, and on
  // how wide the stage is, because on a phone it wraps. It is measured once for
  // each of those combinations and remembered, so a camera move does not remeasure
  // the whole column every frame.
  const markerH = new Map();
  function measureMarker(text, compact) {
    const key = `${compact ? 'c' : 'f'}|${Math.round(rect.width)}|${text}`;
    let h = markerH.get(key);
    if (h == null) {
      const probe = document.createElement('span');
      probe.className = compact ? 'era-marker is-compact' : 'era-marker';
      probe.textContent = text;
      probe.style.top = '-9999px';
      probe.style.visibility = 'hidden';
      eraLayer.appendChild(probe);
      h = probe.offsetHeight || (compact ? MIN_COMPACT_PX : MIN_ROW_PX);
      probe.remove();
      markerH.set(key, h);
    }
    return h;
  }

  function drawEras() {
    // Every era band that holds publications gets a label wherever there is room
    // for it whole. A marker is not 23 pixels tall everywhere: on a phone it
    // wraps to two or three lines, so the row pitch is measured from the markers
    // that were actually drawn, never assumed. Where the column still will not
    // fit, markers are dropped rather than printed through one another — a
    // sliced count reads as broken, a missing one reads as crowding.
    const live = model.bands.filter((b) => b.count);
    if (!live.length) { eraLayer.textContent = ''; eraBoxes = []; return; }

    const top = guard.top;
    let bottom = rect.height - guard.bottom;
    let freeH = Math.max(1, bottom - top);

    const GAP = 3;
    const label = (band) => `${band.label} · ${band.count}`;
    const stackH = (bs, compact) =>
      bs.reduce((sum, b) => sum + measureMarker(label(b), compact), 0) + GAP * (bs.length - 1);

    let bands = live;
    let compact = stackH(live, false) > freeH;
    // A compact stack that still overflows is allowed to run down over the year
    // rail before any band loses its name.
    if (compact && stackH(live, true) > freeH) {
      bottom = Math.max(bottom, rect.height - 4);
      freeH = Math.max(1, bottom - top);
    }
    // Still too tall: thin the column out, keeping an even spread.
    let loops = 0;
    while (stackH(bands, compact) > freeH && bands.length > 1 && loops++ < 8) {
      const keep = bands.filter((_, i) => i % 2 === 0);
      bands = keep.length === bands.length ? bands.slice(0, -1) : keep;
    }

    const frag = document.createDocumentFragment();
    const els = bands.map((band) => {
      const el = document.createElement('span');
      el.className = compact ? 'era-marker is-compact' : 'era-marker';
      el.textContent = label(band);
      frag.appendChild(el);
      return el;
    });
    eraLayer.textContent = '';
    eraLayer.appendChild(frag);

    const heights = bands.map((b) => measureMarker(label(b), compact));
    const ys = bands.map((band) => project(three.controls.target.x, band.top - band.height / 2).y);
    // Forward pass pushes each marker below the one above it, backward pass
    // pulls the stack back inside the free band. Order is never changed, so the
    // markers stay in the same sequence as the bands they name.
    let prev = -Infinity;
    for (let i = 0; i < ys.length; i++) {
      const need = prev === -Infinity ? -Infinity : prev + heights[i - 1] / 2 + GAP + heights[i] / 2;
      ys[i] = Math.max(ys[i], need, top + heights[i] / 2);
      prev = ys[i];
    }
    let nextY = Infinity;
    for (let i = ys.length - 1; i >= 0; i--) {
      const cap = nextY === Infinity ? Infinity : nextY - heights[i + 1] / 2 - GAP - heights[i] / 2;
      ys[i] = Math.min(ys[i], cap, bottom - heights[i] / 2);
      nextY = ys[i];
    }
    els.forEach((el, i) => { el.style.top = `${Math.round(ys[i])}px`; });

    // Measured after layout so a thread label can be pushed clear of an era
    // marker instead of printing through it.
    eraBoxes = Array.from(eraLayer.children).map((el) => {
      const r = el.getBoundingClientRect();
      return { top: r.top - rect.top, bottom: r.bottom - rect.top, right: r.right - rect.left };
    });
  }

  // The year rail tracks the camera, so a label always sits over its own column.
  function drawYears() {
    const rail = document.getElementById('woven-yearrail');
    const frag = document.createDocumentFragment();
    const spanPx = Math.abs(project(xOf(YEAR_MAX), 0).x - project(xOf(YEAR_MIN), 0).x);
    const stepYears = spanPx > 2600 ? 10 : spanPx > 1100 ? 20 : 40;
    let lastX = -999;
    for (let y = YEAR_MIN; y <= YEAR_MAX; y += stepYears) {
      const p = project(xOf(y), three.controls.target.y);
      if (p.x < 8 || p.x > rect.width - 46) continue;
      if (p.x - lastX < 54) continue;
      lastX = p.x;
      const el = document.createElement('span');
      el.textContent = String(y);
      el.style.position = 'absolute';
      el.style.left = `${p.x}px`;
      frag.appendChild(el);
    }
    rail.textContent = '';
    rail.style.position = 'absolute';
    rail.style.height = '26px';
    rail.appendChild(frag);
  }

  function drawNames(dist, only) {
    const ty = three.controls.target.y;
    const candidates = model.layout.slots
      .filter((t) => !only || only.has(t.id))
      .map((t) => ({ t, d: Math.abs(t.y - ty) }))
      .sort((a, b) => a.d - b.d)
      .slice(0, MAX_LABELS * 2);

    // Never place a name under the key; a label half-covered is worse than no
    // label. When the key is docked beside the canvas it overlaps nothing, so
    // it takes no space away from the names.
    const lr = legend.hidden ? null : legend.getBoundingClientRect();
    const overlapsCanvas = lr && lr.left < rect.right && lr.right > rect.left &&
      lr.top < rect.bottom && lr.bottom > rect.top;
    const keep = overlapsCanvas
      ? { left: lr.left - rect.left - 8, top: lr.top - rect.top - 6 }
      : { left: 1e6, top: 1e6 };

    const placed = [];
    const frag = document.createDocumentFragment();
    for (const { t } of candidates) {
      if (placed.length >= MAX_LABELS) break;
      const startX = t.unknownFounding ? 4 : t.x0;
      const p = project(startX, t.y);
      if (!p.onScreen || p.y < guard.top || p.y > rect.height - guard.bottom) continue;
      if (p.y > keep.top && p.x + 214 > keep.left) continue;
      if (placed.some((q) => Math.abs(q - p.y) < MIN_ROW_PX)) continue;

      // An era marker sits on the left edge at the middle of its band. A name on
      // the same row starts after it, never through it. What is left between
      // that marker and the right edge of the canvas is all the room this label
      // will ever have; too little and no label is better than a clipped one.
      let minLeft = 6;
      for (const b of eraBoxes) {
        if (p.y + 10 > b.top && p.y - 10 < b.bottom) minLeft = Math.max(minLeft, b.right + 8);
      }
      const room = rect.width - minLeft - 6;
      if (room < 96) continue;
      const maxLabel = Math.min(220, rect.width * 0.6, room);
      placed.push(p.y);

      const el = document.createElement('span');
      el.className = 'thread-label';
      if (t.ghost) el.classList.add('is-ghost');
      if (app.state.selectedId === t.id) el.classList.add('is-selected');
      if (app.state.hoverId === t.id) el.classList.add('is-hover');
      const years = t.yearFounded
        ? `${t.yearFounded}–${t.yearCeased ?? (t.endState === 'still' ? 'now' : 'unrecorded')}`
        : 'year unrecorded';
      el.innerHTML = '';
      const n = document.createElement('b');
      n.textContent = t.name;
      const y = document.createElement('i');
      y.textContent = years;
      el.append(n, y);
      el.style.top = `${p.y}px`;
      el.style.maxWidth = `${maxLabel}px`;
      el.style.left = `${Math.max(minLeft, p.x + 8)}px`;
      el.dataset.minLeft = String(minLeft);
      frag.appendChild(el);
    }
    layer.textContent = '';
    layer.appendChild(frag);

    // The right edge is the canvas edge, which above 900px is the dock edge, not
    // the window edge. Measured after layout so a short name is not pushed left
    // for room it never needed.
    for (const el of layer.children) {
      const w = el.getBoundingClientRect().width;
      const left = parseFloat(el.style.left);
      const room = rect.width - 6 - w;
      if (left > room) el.style.left = `${Math.max(+el.dataset.minLeft, room)}px`;
    }
  }

  function setDensityNote(text) {
    const note = legend.querySelector('.lg-rows');
    note.textContent = text;
  }

  return { update, setDensityNote, legend };
}
