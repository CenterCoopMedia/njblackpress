// Woven — DOM labels, era markers, and the legend.
// All type is HTML. Nothing is ever drawn into the canvas.

import * as THREE from 'three';
import { x as xOf, YEAR_MIN, YEAR_MAX } from './layout.js';

const MAX_LABELS = 26;
const LABEL_DISTANCE = 26;   // beyond this the cloth is a shape, not a list
const MIN_ROW_PX = 24;       // a label is 23px tall, so anything less overlaps

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
  legend.innerHTML = `
    <p class="lg-lede">Each horizontal thread is one publication. It starts the year the paper was founded and ends the year it stopped. Left to right is 1880 to 2026.</p>
    <ul>
      <li><span class="lg-swatch lg-thick"></span>Thicker thread — more surviving material we can show you</li>
      <li><span class="lg-swatch lg-ghost"></span>Faint and frayed — ${model.counts.ghost} titles we know only from a catalog line</li>
      <li><span class="lg-swatch lg-loose"></span>Runs past the right post — the ${model.counts.stillPublishing} papers still publishing</li>
      <li><span class="lg-swatch lg-knot"></span>Knot — a documented event, ${model.counts.events} in all</li>
    </ul>
    <p class="lg-rows">Rows are grouped by the decade each paper began. Names appear when you are close enough to read them.</p>
    <button type="button" class="woven-btn lg-toggle" aria-expanded="true">Hide the key</button>`;
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

  function measureGuard() {
    const chrome = document.getElementById('woven-chrome');
    const rail = document.getElementById('woven-yearrail');
    guard = {
      top: (chrome ? chrome.getBoundingClientRect().height : 88) + 6,
      bottom: (rail ? rail.getBoundingClientRect().height : 26) + 18
    };
  }

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
    legend.hidden = busy;
    const ghosting = !!(app.ghost && app.ghost.isPlaying);
    eraLayer.hidden = ghosting;
    if (ghosting) { layer.textContent = ''; eraBoxes = []; drawYears(); return; }
    drawEras();
    drawYears();
    if (busy && app.tour && app.tour.isPlaying) {
      // During a tour only the tour's own threads are named. Everything else is
      // already dimmed; naming it would fight the story for attention.
      drawNames(dist, new Set(model.tours.find((t) => t.id === app.state.tourId)?.threadIds || []));
      layer.dataset.mode = 'tour';
      return;
    }
    if (dist > LABEL_DISTANCE) {
      layer.textContent = '';
      layer.dataset.mode = 'far';
      return;
    }
    layer.dataset.mode = 'near';
    drawNames(dist);
  }

  function drawEras() {
    const frag = document.createDocumentFragment();
    for (const band of model.bands) {
      if (!band.count) continue;
      const mid = band.top - band.height / 2;
      const p = project(three.controls.target.x, mid);
      if (p.y < guard.top || p.y > rect.height - guard.bottom) continue;
      const el = document.createElement('span');
      el.className = 'era-marker';
      el.textContent = `${band.label} · ${band.count}`;
      el.style.top = `${p.y}px`;
      frag.appendChild(el);
    }
    eraLayer.textContent = '';
    eraLayer.appendChild(frag);

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
