// Woven — story mode. Camera keyframes, dimming, clipping panels, tour bar.
// Every string the overlay shows comes from a data field. Nothing is composed.

import * as THREE from 'three';
import { PANEL_VERT, PANEL_FRAG } from './shaders.js';
import { announce, syncTwin } from './twin.js';
import { easeInOutCubic } from './layout.js';

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const DWELL = 3200;
const TRANSIT_MS = 1600;
const MAX_TEXTURES = 4;

export function createTour(app, three, model) {
  const { scene, camera, controls, stateTex, knots } = three;
  const bar = document.getElementById('woven-tourbar');
  const overlay = document.getElementById('woven-overlay');
  const card = document.getElementById('woven-card');

  const cache = new Map(); // webPath -> THREE.Texture, LRU by insertion order
  let panelMesh = null;
  let panelSize = { w: 0, h: 0 };
  let frameLines = null;
  let tour = null;
  let stops = [];
  let index = 0;
  let playing = false;
  let paused = false;
  let timer = null;
  let preTourView = null;

  const api = {
    get isPlaying() { return playing; },
    get isAnimating() { return playing && !!app.tween; },
    start, exit, next, prev, goTo
  };

  function reduced() { return app.reduceMotion.matches; }

  function start(id) {
    const t = model.tours.find((x) => x.id === id);
    if (!t) return;
    if (playing) clearTimer();
    tour = t;
    stops = withTransits(t);
    index = 0;
    playing = true;
    paused = reduced();
    preTourView = {
      target: [controls.target.x, controls.target.y, 0],
      position: [camera.position.x, camera.position.y, camera.position.z]
    };
    dimForTour(t);
    history.replaceState(null, '', `?story=${t.id}`);
    app.state.tourId = t.id;
    app.state.stopIndex = 0;
    syncTwin(app.state);
    announce(`Guided thread: ${t.title}. ${t.stops.length} stops, ${t.era}.`);
    renderBar();
    goTo(0);
  }

  // Insert a transit stop wherever consecutive stops change era band.
  function withTransits(t) {
    const out = [];
    t.stops.forEach((s, i) => {
      const prevStop = t.stops[i - 1];
      if (prevStop && prevStop.band && s.band && prevStop.band !== s.band) {
        const a = model.bands.find((b) => b.key === prevStop.band);
        const b = model.bands.find((b2) => b2.key === s.band);
        const box = {
          minX: 0, maxX: 73,
          minY: Math.min(a.top - a.height, b.top - b.height),
          maxY: Math.max(a.top, b.top)
        };
        out.push({
          kind: 'transit',
          tx: (prevStop.tx + s.tx) / 2,
          ty: (prevStop.ty + s.ty) / 2,
          distance: app.fitDistance(box, 0.10),
          fromBand: a.label, toBand: b.label,
          dateLabel: s.dateLabel, band: s.band, event: null, clipping: null
        });
      }
      out.push(s);
    });
    return out;
  }

  function dimForTour(t) {
    const ids = new Set(t.threadIds);
    stateTex.clear(0, 0);
    stateTex.clear(1, 0);
    for (const th of model.threads) {
      if (ids.has(th.id)) {
        stateTex.set(th.threadIndex, 0, 200);
        stateTex.set(th.threadIndex, 1, 0);
      } else {
        stateTex.set(th.threadIndex, 0, 0);
        stateTex.set(th.threadIndex, 1, 217);
      }
    }
    stateTex.commit();
    app.needsRender = true;
    const evIds = new Set(t.stops.map((s) => s.eventId));
    knots.setTour(evIds, null);
  }

  async function goTo(i) {
    if (!playing) return;
    index = Math.max(0, Math.min(stops.length - 1, i));
    const s = stops[index];
    app.state.stopIndex = tourStopIndex();
    syncTwin(app.state);
    renderBar();
    renderCard(s);
    if (s.kind !== 'transit') {
      knots.setTour(new Set(tour.stops.map((x) => x.eventId)), s.eventId);
      app.needsRender = true;
    }
    await app.easeTo([s.tx, s.ty], s.distance, reduced() ? 0 : TRANSIT_MS);
    // The reader can leave while the camera is still moving or a clipping is
    // still decoding. Once they have, this stop no longer has a tour to belong
    // to, so it stops here rather than talking about one.
    if (!playing) return;
    if (s.kind === 'transit') {
      announce(`Moving from ${s.fromBand}, to ${s.toBand}.`);
      if (!paused) schedule(600 + 900);
      return;
    }
    await showPanel(s);
    if (!playing) { disposePanel(); return; }
    announceStop(s);
    if (!paused) schedule(DWELL);
  }

  function tourStopIndex() {
    let n = -1;
    for (let i = 0; i <= index; i++) if (stops[i].kind !== 'transit') n++;
    return Math.max(0, n);
  }

  function announceStop(s) {
    const th = s.threadId != null ? model.byId.get(s.threadId) : null;
    announce(`Stop ${tourStopIndex() + 1} of ${tour.stops.length}. ${s.dateLabel}. ${s.event.title}.` +
      (th ? ` ${th.name}.` : '') + (s.confidence === 'medium' ? ' Medium confidence.' : ''));
  }

  function schedule(ms) {
    clearTimer();
    if (reduced()) return;
    timer = setTimeout(() => {
      if (index >= stops.length - 1) { renderClose(); return; }
      goTo(index + 1);
    }, ms);
  }

  function clearTimer() { if (timer) { clearTimeout(timer); timer = null; } }

  function next() { paused = true; clearTimer(); if (index < stops.length - 1) goTo(index + 1); else renderClose(); }
  function prev() { paused = true; clearTimer(); goTo(index - 1); }

  function exit() {
    if (!playing) return;
    clearTimer();
    playing = false;
    tour = null;
    bar.hidden = true;
    overlay.hidden = true;
    card.hidden = true;
    stateTex.clear(0, 0);
    stateTex.clear(1, 0);
    stateTex.commit();
    knots.reset();
    disposePanel();
    app.state.tourId = null;
    syncTwin(app.state);
    history.replaceState(null, '', location.pathname);
    if (preTourView) app.applyView(preTourView);
    app.needsRender = true;
  }

  // ---- clipping panels ----

  async function showPanel(s) {
    disposePanel();
    const clip = s.clipping;
    if (!clip || !clip.webPath || !clip.altText) { renderOverlay(s, null); return; }
    let tex = cache.get(clip.webPath);
    if (!tex) {
      try {
        const img = new Image();
        img.src = clip.webPath;
        await img.decode();
        tex = new THREE.Texture(img);
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.generateMipmaps = true;
        tex.minFilter = THREE.LinearMipmapLinearFilter;
        tex.anisotropy = Math.min(4, three.renderer.capabilities.getMaxAnisotropy());
        tex.needsUpdate = true;
      } catch {
        renderOverlay(s, null);
        return;
      }
      while (cache.size >= MAX_TEXTURES) {
        const oldest = cache.keys().next().value;
        cache.get(oldest).dispose();
        cache.delete(oldest);
      }
      cache.set(clip.webPath, tex);
    }
    const h = 4.5;
    const w = h * ((clip.width || 3) / (clip.height || 4));
    const geo = new THREE.PlaneGeometry(w, h, 8, 6);
    const mat = new THREE.ShaderMaterial({
      vertexShader: PANEL_VERT, fragmentShader: PANEL_FRAG,
      uniforms: { uMap: { value: tex }, uTime: { value: 0 }, uOpacity: { value: 1 } },
      transparent: true, side: THREE.DoubleSide
    });
    panelMesh = new THREE.Mesh(geo, mat);
    panelSize = { w, h };
    panelMesh.position.set(s.tx + 5, s.ty, 3.0);
    panelMesh.scale.y = reduced() ? 1 : 0.001;
    scene.add(panelMesh);
    if (s.clipping.rightsStatus === 'crop_first') {
      frameLines = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.PlaneGeometry(w - 0.08, h - 0.08)),
        new THREE.LineBasicMaterial({ color: 0xe2662b })
      );
      frameLines.position.copy(panelMesh.position);
      scene.add(frameLines);
    }
    if (!reduced()) await unfurl(panelMesh);
    renderOverlay(s, clip);
    app.needsRender = true;
  }

  function unfurl(mesh) {
    return new Promise((resolve) => {
      const t0 = performance.now();
      const tick = () => {
        const k = Math.min(1, (performance.now() - t0) / 500);
        mesh.scale.y = easeInOutCubic(k) * (1 + 0.04 * Math.sin(k * Math.PI));
        app.needsRender = true;
        if (k < 1) requestAnimationFrame(tick); else { mesh.scale.y = 1; resolve(); }
      };
      requestAnimationFrame(tick);
    });
  }

  function disposePanel() {
    if (panelMesh) { scene.remove(panelMesh); panelMesh.geometry.dispose(); panelMesh.material.dispose(); panelMesh = null; panelSize = { w: 0, h: 0 }; }
    if (frameLines) { scene.remove(frameLines); frameLines.geometry.dispose(); frameLines.material.dispose(); frameLines = null; }
  }

  // ---- DOM overlay and cards. All text lives here, never in the canvas. ----

  function renderOverlay(s, clip) {
    if (!clip) {
      // Citation-only stop. The normal case, and it must look deliberate.
      // The description is already the body of the card on the left, so this
      // block carries the citations and nothing else.
      const cites = [...new Set((s.event.sourceFiles || [])
        .map((f) => model.citeSource(f))
        .filter(Boolean))];
      overlay.innerHTML = `<figure class="cite-only">
        <hr class="rail-wood">
        ${cites.map((c) => `<cite>${esc(c)}</cite>`).join('')}
        <p class="rights">The source is a printed bibliography. We quote it; we do not reproduce the page.</p>
      </figure>`;
    } else {
      overlay.innerHTML = `<figure>
        <img src="${esc(clip.webPath)}" alt="${esc(clip.altText)}" width="${clip.width || ''}" height="${clip.height || ''}" hidden>
        <figcaption>${esc(clip.caption)}</figcaption>
        <cite>${esc(clip.citation)}</cite>
        ${clip.rightsStatus === 'crop_first' ? '<p class="rights">clip · Cropped detail. Full page not reproduced.</p>' : ''}
      </figure>`;
    }
    overlay.hidden = false;
    positionOverlay();
  }

  // Screen-space box of the clipping panel, from its four corners.
  function panelScreenBox() {
    const rect = three.canvas.getBoundingClientRect();
    const p = panelMesh.position;
    const hw = panelSize.w / 2;
    const hh = panelSize.h / 2;
    const box = { left: Infinity, right: -Infinity, top: Infinity, bottom: -Infinity };
    for (const dx of [-hw, hw]) {
      for (const dy of [-hh, hh]) {
        const v = new THREE.Vector3(p.x + dx, p.y + dy, p.z).project(camera);
        const px = ((v.x + 1) / 2) * rect.width;
        const py = ((1 - v.y) / 2) * rect.height;
        box.left = Math.min(box.left, px);
        box.right = Math.max(box.right, px);
        box.top = Math.min(box.top, py);
        box.bottom = Math.max(box.bottom, py);
      }
    }
    return box;
  }

  const overlaps = (a, b) =>
    a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;

  // The caption sits beside the clipping and clear of the stop card, never over
  // either. Reading the evidence is the point of the stop; the words can move.
  function positionOverlay() {
    const rect = three.canvas.getBoundingClientRect();
    const pad = 16;
    const w = overlay.offsetWidth;
    const h = overlay.offsetHeight;
    const minTop = 72;
    const maxLeft = Math.max(pad, rect.width - w - pad);
    const maxTop = Math.max(minTop, rect.height - h - 96);
    const clampL = (l) => Math.max(pad, Math.min(maxLeft, l));
    const clampT = (t) => Math.max(minTop, Math.min(maxTop, t));

    const panel = panelMesh ? panelScreenBox() : null;
    let cardBox = null;
    if (!card.hidden) {
      const c = card.getBoundingClientRect();
      cardBox = { left: c.left - rect.left, right: c.right - rect.left, top: c.top - rect.top, bottom: c.bottom - rect.top };
    }

    const slots = [];
    if (panel) {
      slots.push([panel.right + pad, clampT(panel.top)]);
      slots.push([panel.left - pad - w, clampT(panel.top)]);
      slots.push([clampL(panel.left), panel.bottom + pad]);
      slots.push([clampL(panel.left), panel.top - pad - h]);
    }
    slots.push([maxLeft, maxTop], [maxLeft, minTop]);

    for (const [l, t] of slots) {
      if (l < pad || l > maxLeft || t < minTop || t > maxTop) continue;
      const box = { left: l, right: l + w, top: t, bottom: t + h };
      if (panel && overlaps(box, panel)) continue;
      if (cardBox && overlaps(box, cardBox)) continue;
      place(l, t);
      return;
    }
    place(maxLeft, maxTop);

    function place(l, t) {
      overlay.style.left = `${clampL(l)}px`;
      overlay.style.top = `${clampT(t)}px`;
    }
  }

  function renderCard(s) {
    if (s.kind === 'transit') {
      card.innerHTML = `<span class="band">${esc(s.fromBand)} → ${esc(s.toBand)}</span>`;
      card.hidden = false;
      return;
    }
    const th = s.threadId != null ? model.byId.get(s.threadId) : null;
    card.innerHTML = `
      <h3>${esc(s.event.title)}</h3>
      <p>${esc(s.event.description)}</p>
      ${th ? `<p class="band">${esc(th.name)} · ${esc(th.city || 'city unrecorded')}</p>` : '<p class="band">Context — not tied to a specific publication.</p>'}
      ${s.confidence === 'medium' ? '<p class="flag">Medium confidence</p>' : ''}
      ${tour.strength === 'weak' && index === 0 ? '<p class="flag">Thinly sourced. This thread rests on two cover artifacts and one dated clipping. Read it as a lead, not a finding.</p>' : ''}
      ${index === 0 ? `<p>${esc(tour.thread)}</p>` : ''}`;
    card.hidden = false;
  }

  function renderClose() {
    clearTimer();
    card.innerHTML = `
      <h3>${esc(tour.title)}</h3>
      <p>${esc(tour.thread)}</p>
      <p><button type="button" class="woven-btn" data-act="ghost">Show what did not survive</button>
         <button type="button" class="woven-btn" data-act="exit">Exit this thread</button></p>`;
    card.hidden = false;
    card.querySelector('[data-act="ghost"]').addEventListener('click', () => { exit(); app.showGhost(); });
    card.querySelector('[data-act="exit"]').addEventListener('click', exit);
    overlay.hidden = true;
  }

  function renderBar(focusAct) {
    const total = tour.stops.length;
    const n = tourStopIndex() + 1;
    // Under reduced motion nothing plays itself, so there is no play control at
    // all — the reader advances with "next stop". Otherwise the one control
    // reads "pause" while it runs and "resume" once it is stopped. Never two
    // buttons with the same label.
    bar.innerHTML = `
      ${reduced() ? '' : `<button type="button" class="woven-btn" data-act="play" aria-pressed="${paused ? 'true' : 'false'}">${paused ? 'Resume' : 'Pause'}</button>`}
      <button type="button" class="woven-btn" data-act="prev">Previous stop</button>
      <button type="button" class="woven-btn" data-act="next">Next stop</button>
      <span class="tour-title">${esc(tour.title)}${tour.strength === 'weak' ? ' · Thinly sourced' : ''}</span>
      <span class="tour-counter">Stop ${n} of ${total} · ${esc(stops[index].dateLabel || '')}</span>
      <span id="woven-rail" aria-hidden="true">${Array.from({ length: total }, (_, i) => `<i class="${i < n ? 'on' : ''}"></i>`).join('')}</span>
      <button type="button" class="woven-btn" data-act="exit">Exit this thread</button>`;
    bar.hidden = false;
    const play = bar.querySelector('[data-act="play"]');
    if (play) {
      play.addEventListener('click', () => {
        paused = !paused;
        clearTimer();
        renderBar('play');
        if (!paused) schedule(DWELL);
      });
    }
    bar.querySelector('[data-act="prev"]').addEventListener('click', prev);
    bar.querySelector('[data-act="next"]').addEventListener('click', next);
    bar.querySelector('[data-act="exit"]').addEventListener('click', exit);
    if (focusAct) {
      const back = bar.querySelector(`[data-act="${focusAct}"]`);
      if (back) back.focus();
    }
  }

  controls.addEventListener('change', () => { if (playing && !overlay.hidden) positionOverlay(); });

  return api;
}
