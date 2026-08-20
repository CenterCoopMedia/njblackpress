// Woven — entry point. Capability test, scene, render loop, router.

import { loadModel } from './data.js';
import { buildTwin, syncTwin, announce, announceAssertive, promoteTwin } from './twin.js';
import {
  fitDistance, boxCenter, easeInOutCubic
} from './layout.js';

const params = new URLSearchParams(location.search);

const escapeHtml = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function hasWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch { return false; }
}

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

const state = {
  selectedId: null, hoverId: null, tourId: null, stopIndex: 0,
  ghostGroup: null, scrollTwin: false
};

const app = {
  model: null, three: null, state, reduceMotion,
  needsRender: true, tween: null, tour: null, ghost: null
};

boot();

async function boot() {
  let model;
  try {
    model = await loadModel();
  } catch (e) {
    console.error('Woven: data load failed', e);
    return;
  }
  app.model = model;

  document.querySelectorAll('[data-count]').forEach((el) => {
    el.textContent = model.counts[el.dataset.count === 'still' ? 'stillPublishing' : el.dataset.count];
  });

  buildTwin(model, {
    select: (id) => app.select && app.select(id, { fromTwin: true }),
    playStory: (id) => app.playStory && app.playStory(id)
  });

  console.info('[woven] counts', model.counts);

  if (params.get('nogl') === '1' || !hasWebGL()) {
    const { startFallback } = await import('./fallback.js');
    const api = startFallback(model, 'nogl');
    app.select = (id) => api.open(id);
    app.playStory = (id) => api.playStory(id);
    app.showGhost = () => api.showGhost();
    return;
  }
  if (params.get('twin') === '1') document.getElementById('woven-twin').classList.add('twin-visible');

  await startScene(model);
}

async function startScene(model) {
  const THREE = await import('three');
  const { OrbitControls } = await import('three/addons/controls/OrbitControls.js');
  const { buildWeft, buildWarp, createStateTexture, createClothMaterial, pluckUniforms, weaveUniform, minHalfWidth } = await import('./cloth.js');
  const { buildLoom, buildLights } = await import('./loom.js');
  const { buildKnots } = await import('./knots.js');
  const { createPicker } = await import('./picking.js');
  const panel = await import('./panel.js');

  const canvas = document.getElementById('woven-canvas');
  const stage = document.getElementById('woven-stage');

  const renderer = new THREE.WebGLRenderer({
    canvas, antialias: window.devicePixelRatio < 2,
    powerPreference: 'high-performance', alpha: false, stencil: false, depth: true
  });
  let pixelRatio = Math.min(window.devicePixelRatio, 2);
  renderer.setPixelRatio(pixelRatio);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x0b0806, 1);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.5, 400);
  scene.add(buildLights());
  scene.add(buildLoom(model));

  const stateTex = createStateTexture(model.threads.length);
  const geos = buildWeft(model);
  const matSolid = createClothMaterial(stateTex);
  const matGhost = createClothMaterial(stateTex, { depthWrite: false });
  const weftSolid = new THREE.Mesh(geos.solid, matSolid);
  const weftGhost = new THREE.Mesh(geos.ghost, matGhost);
  weftGhost.renderOrder = 2;
  weftSolid.name = 'weft-solid';
  weftGhost.name = 'weft-ghost';
  scene.add(weftSolid, weftGhost);

  const warpFull = new THREE.Mesh(buildWarp(model, 1, 1), createClothMaterial(stateTex, { depthWrite: false }));
  const warpCoarse = new THREE.Mesh(buildWarp(model, 4, 4), createClothMaterial(stateTex, { depthWrite: false }));
  warpFull.material.uniforms.uGhostAlpha.value = 0.55;
  warpCoarse.material.uniforms.uGhostAlpha.value = 0.55;
  warpFull.renderOrder = 1;
  warpCoarse.renderOrder = 1;
  warpFull.visible = false;
  scene.add(warpFull, warpCoarse);

  const knots = buildKnots(model);
  knots.meshes.forEach((m) => scene.add(m));

  // The camera never turns. Turning the cloth added no information and cost the
  // reader their bearings, so the view is locked perpendicular to the cloth and
  // the only moves are pan and zoom. The angle limits pin the orbit to the axis
  // even if something else writes a camera position.
  const controls = new OrbitControls(camera, canvas);
  Object.assign(controls, {
    enableDamping: true, dampingFactor: 0.08,
    enableRotate: false,
    minPolarAngle: Math.PI / 2, maxPolarAngle: Math.PI / 2,
    // A hair either side of zero, not zero twice: OrbitControls only clamps the
    // azimuth when the minimum is strictly below the maximum.
    minAzimuthAngle: -1e-4, maxAzimuthAngle: 1e-4,
    // The far limit has to clear the whole cloth on a 375px window, where the
    // frustum is narrow and fitting 146 years across takes a long lens.
    minDistance: 8, maxDistance: 260,
    enablePan: true, screenSpacePanning: true,
    zoomSpeed: 0.7
  });
  // A drag pans, with one finger as well as two. Without this a phone would
  // have no way to move across the cloth at all.
  controls.mouseButtons = {
    LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN
  };
  controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_PAN };

  const clothBox = model.layout.bounds;
  // The default framing shows the whole loom, including the loose strands that
  // run past the right post. It stops just under the last row rather than at the
  // foot of the frame: three units of bare wood is three units of empty black.
  const loomBox = {
    minX: -3.2, maxX: 79.0,
    minY: clothBox.minY - 0.5, maxY: 1.6
  };
  const centre = boxCenter(loomBox);
  app.loomBox = loomBox;
  app.fitDistance = (box, margin) => fitDistance(box, margin, camera);
  const padX = (clothBox.maxX - clothBox.minX) * 0.1;
  // Vertical slack has to cover the offset the default framing applies to clear
  // the control bars, so it is generous rather than a tenth of the cloth.
  const padY = (clothBox.maxY - clothBox.minY) * 0.1 + 8;

  controls.addEventListener('change', () => {
    const t = controls.target;
    t.x = Math.min(clothBox.maxX + padX, Math.max(clothBox.minX - padX, t.x));
    t.y = Math.min(clothBox.maxY + padY, Math.max(clothBox.minY - padY, t.y));
    t.z = 0;
    app.needsRender = true;
    if (app.ghost && app.ghost.isPlaying && app.ghost.userMoved) app.ghost.exit();
  });

  const three = {
    THREE, renderer, scene, camera, controls, stateTex, knots, panel,
    weftSolid, weftGhost, warpFull, warpCoarse, materials: [matSolid, matGhost],
    stage, canvas
  };
  app.three = three;

  // The keep-out bands: the control bars at the top and the year rail at the
  // foot. Type and cloth share one canvas, so the cloth is fitted into what is
  // left between them rather than into the whole rectangle.
  function keepOut() {
    const r = canvas.getBoundingClientRect();
    const chromeEl = document.getElementById('woven-chrome');
    const railEl = document.getElementById('woven-yearrail');
    const top = (chromeEl ? chromeEl.getBoundingClientRect().height : 88) + 10;
    const bottom = (railEl ? railEl.getBoundingClientRect().height : 26) + 10;
    const height = Math.max(1, Math.round(r.height));
    return { width: Math.max(1, Math.round(r.width)), height, top, bottom };
  }

  // The default framing. Every one of the publications is on screen at once,
  // whole, inside the free band — that is the only view in which the shape of
  // the archive is legible. Reading the names is what zooming in is for.
  function wholeLoomFraming() {
    const k = keepOut();
    const freeH = Math.max(60, k.height - k.top - k.bottom);
    const w = (loomBox.maxX - loomBox.minX) * 1.06;
    const h = (loomBox.maxY - loomBox.minY) * 1.06;
    const vFov = (camera.fov * Math.PI) / 180;
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
    // Fitting the height into the free band, not the canvas, costs exactly the
    // ratio between them.
    const dV = ((h / 2) / Math.tan(vFov / 2)) * (k.height / freeH);
    const dH = (w / 2) / Math.tan(hFov / 2);
    const d = Math.max(controls.minDistance, Math.min(controls.maxDistance, Math.max(dV, dH)));
    const worldPerPx = (2 * Math.tan(vFov / 2) * d) / k.height;
    // The centre of the cloth is put at the centre of the free band, which sits
    // below the centre of the canvas by however much taller the bars are.
    const offsetPx = (k.top + freeH / 2) - k.height / 2;
    const ty = centre[1] + offsetPx * worldPerPx;
    return { target: [centre[0], ty, 0], position: [centre[0], ty, d] };
  }

  function readingFraming(bandKey) {
    const bands = model.bands.filter((b) => b.count);
    const band = bands.find((b) => b.key === (bandKey || 'C')) || bands[0];
    const mid = band.top - band.height / 2;
    const spans = band.threads.map((t) => t.x0);
    const x0 = Math.min(...spans);
    const d = 15;
    return {
      band: band.key,
      target: [Math.min(66, x0 + 9), mid, 0],
      position: [Math.min(66, x0 + 9), mid, d]
    };
  }

  let readingBand = 'C';
  // Declared up here because the first framing is applied long before the era
  // chip's own section, and applying a framing rewrites the chip.
  let eraNowText = '';
  function defaultFraming() { return wholeLoomFraming(); }

  // A camera move already in flight would overwrite whatever this sets on the
  // next frame, so applying a view cancels it. This is what stopped "reset the
  // view" from restoring the zoom: the tween from the last selection won.
  function applyView(view) {
    app.tween = null;
    controls.target.set(view.target[0], view.target[1], view.target[2] ?? 0);
    camera.position.set(view.position[0], view.position[1], view.position[2]);
    controls.update();
    // A second pass, because the target clamp on the change event can move the
    // target after the first one and leave the distance off by that much.
    camera.position.set(controls.target.x, controls.target.y, view.position[2]);
    controls.update();
    app.needsRender = true;
    if (app.labels) app.labels.update();
    updateEraNow();
  }

  app.defaultFraming = defaultFraming;
  app.applyView = applyView;

  app.easeTo = function easeTo(target, distance, ms) {
    const from = {
      tx: controls.target.x, ty: controls.target.y,
      px: camera.position.x, py: camera.position.y, pz: camera.position.z
    };
    const to = {
      tx: target[0], ty: target[1],
      px: target[0], py: target[1], pz: distance
    };
    if (reduceMotion.matches || ms === 0) {
      applyView({ target: [to.tx, to.ty, 0], position: [to.px, to.py, to.pz] });
      return Promise.resolve();
    }
    return new Promise((resolve) => {
      const t0 = performance.now();
      app.tween = () => {
        const k = Math.min(1, (performance.now() - t0) / ms);
        const e = easeInOutCubic(k);
        controls.target.set(from.tx + (to.tx - from.tx) * e, from.ty + (to.ty - from.ty) * e, 0);
        camera.position.set(
          from.px + (to.px - from.px) * e,
          from.py + (to.py - from.py) * e,
          from.pz + (to.pz - from.pz) * e
        );
        app.needsRender = true;
        if (k >= 1) { app.tween = null; resolve(); }
      };
    });
  };

  function resize() {
    // Measure the canvas, not the stage: above 900px the key is docked beside
    // the canvas, so the two are different widths.
    const r = canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(r.width));
    const h = Math.max(1, Math.round(r.height));
    let px = Math.min(window.devicePixelRatio, 2);
    if (w * h * px * px > 2.2e6) px = 1.5;
    pixelRatio = px;
    canvasCssHeight = h;
    renderer.setPixelRatio(px);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    // The fine warp is 40k triangles of detail nobody can see on a 375px screen,
    // so a narrow window gets the coarse warp. A window can be narrowed after
    // load, so this is decided on every resize, not once. Once the frame timer
    // has asked for the coarse warp it stays coarse.
    app.forceCoarseWarp = coarseFromDegrade || window.innerWidth < 700;
    app.needsRender = true;
    // Names, era markers, and the year rail are DOM in canvas pixels, so they
    // are re-placed against the new rect before the next frame is drawn.
    if (app.labels) app.labels.update();
  }
  let coarseFromDegrade = false;
  let canvasCssHeight = 1;

  // How thin a thread is allowed to get. At the default framing a real thread is
  // about a fifth of a pixel wide, which the rasteriser drops outright, so a band
  // of three papers drew as empty black. The floor is 1.9 screen pixels, capped
  // well under the 0.16-unit row pitch so a crowded band still reads as separate
  // threads rather than as a slab.
  const MIN_THREAD_PX = 1.9;
  // Four fifths of the 0.16-unit row pitch. At the default framing the rows are
  // only about 1.4 pixels apart, so this is as wide as a thread can be drawn and
  // still leave a gap to the next one.
  const MAX_MIN_HALF_W = 0.064;
  function updateThreadFloor(dist) {
    const worldPerPx = (2 * Math.tan((camera.fov * Math.PI) / 360) * dist) / Math.max(1, canvasCssHeight);
    const want = Math.min(MAX_MIN_HALF_W, (worldPerPx * MIN_THREAD_PX) / 2);
    if (Math.abs(minHalfWidth.value - want) > 1e-5) {
      minHalfWidth.value = want;
      app.needsRender = true;
    }
  }

  const { createLabels } = await import('./labels.js');
  const labels = createLabels(app, three, model);
  app.labels = labels;

  // Until the reader moves the camera themselves, a resize re-fits the default
  // framing. Turning a phone would otherwise leave the cloth half off screen.
  let userMoved = false;
  // "You start zoomed out" stops being true the moment the reader zooms, so the
  // line is shown until they do and never after. It is a starting instruction,
  // not a status.
  const eranavNote = document.getElementById('woven-eranav-note');
  function markInteracted() {
    userMoved = true;
    if (eranavNote && !eranavNote.hidden) {
      eranavNote.hidden = true;
      if (app.labels) app.labels.update();
    }
  }
  app.markInteracted = markInteracted;
  controls.addEventListener('start', markInteracted);
  canvas.addEventListener('wheel', markInteracted, { passive: true });

  window.addEventListener('resize', () => {
    resize();
    if (!userMoved) applyView(defaultFraming());
    else updateEraNow();
  });
  resize();
  labels.update();
  applyView(defaultFraming());
  labels.update();

  // ---- picking, hover, selection ----
  const pick = createPicker(model, camera, knots, controls);
  const tip = document.getElementById('woven-tip');
  let pending = null;
  let hoverTarget = null;

  canvas.addEventListener('pointermove', (e) => {
    pending = { x: e.clientX, y: e.clientY, touch: e.pointerType === 'touch' };
  });
  canvas.addEventListener('pointerleave', () => {
    pending = null; hoverTarget = null; tip.hidden = true;
    state.hoverId = null; writeHover(null); syncTwin(state); app.needsRender = true;
  });
  // A pan ends with a click on the canvas. Without this the reader drags across
  // the cloth and lands on a publication panel they never asked for, which on a
  // phone covers the whole stage.
  let downAt = null;
  // A click event does not always carry a pointer type, so the type is taken
  // from the press that produced it. Getting this wrong costs a finger the
  // larger hit slab, which is the whole reason a tap ever lands.
  const coarsePointer = window.matchMedia('(pointer: coarse)');
  let downCoarse = coarsePointer.matches;
  canvas.addEventListener('pointerdown', (e) => {
    downAt = { x: e.clientX, y: e.clientY };
    downCoarse = e.pointerType === 'touch' || e.pointerType === 'pen' || coarsePointer.matches;
  });
  canvas.addEventListener('click', (e) => {
    if (downAt && Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y) > 8) return;
    const r = canvas.getBoundingClientRect();
    const h = pick(e.clientX, e.clientY, r, downCoarse || e.pointerType === 'touch');
    if (!h) return;
    // The tooltip has done its job the moment a panel opens. Left up, it hangs
    // over the cloth with no pointer under it and no way to dismiss it.
    hideTip();
    if (h.kind === 'knot') openKnot(h.knot);
    else app.select(h.thread.id, {});
  });

  function hideTip() {
    tip.hidden = true;
    hoverTarget = null;
    pending = null;
    if (state.hoverId != null) {
      state.hoverId = null;
      stateTex.clear(3, 0);
      paintBase(null);
      stateTex.commit();
      syncTwin(state);
      app.needsRender = true;
    }
  }
  app.hideTip = hideTip;

  function processHover() {
    if (!pending) return;
    const r = canvas.getBoundingClientRect();
    const h = pick(pending.x, pending.y, r, pending.touch);
    const key = h ? (h.kind === 'knot' ? `k${h.knot.index}` : `t${h.thread.id}`) : null;
    if (key !== hoverTarget) {
      hoverTarget = key;
      state.hoverId = h && h.kind === 'thread' ? h.thread.id : null;
      // Only a mouse plucks on hover. A finger has no hover, and a stylus
      // sweeping the cloth would set every thread ringing at once.
      if (h && h.kind === 'thread' && canHover.matches && !pending.touch) pluck(h.thread);
      writeHover(h);
      syncTwin(state);
      app.needsRender = true;
    }
    if (h) {
      tip.hidden = false;
      const left = Math.min(pending.x - r.left + 14, r.width - tip.offsetWidth - 8);
      const top = Math.min(pending.y - r.top + 14, r.height - tip.offsetHeight - 8);
      tip.style.left = `${Math.max(8, left)}px`;
      tip.style.top = `${Math.max(8, top)}px`;
    } else {
      tip.hidden = true;
    }
    pending = null;
  }

  // How far the rest of the cloth is pushed back. Capped: the subject has to
  // stand out, but the cloth behind it has to stay a cloth. Dimmed to nothing is
  // the same picture as one thread on a black field, which is not the picture.
  const HOVER_DIM = 110;
  const SEARCH_DIM = 130;
  let searchMatches = null;

  // One place writes the highlight and dim channels, from selection, hover, and
  // the search field together. Tours and the ghost sequence own these channels
  // while they run, so this stands aside for them.
  function paintBase(h) {
    if ((app.tour && app.tour.isPlaying) || (app.ghost && app.ghost.isPlaying)) return;
    const hoverId = h && h.kind === 'thread' ? h.thread.id : null;
    for (const t of model.threads) {
      let dim = 0;
      if (hoverId !== null) dim = t.id === hoverId ? 0 : HOVER_DIM;
      else if (searchMatches) dim = searchMatches.has(t.id) ? 0 : SEARCH_DIM;
      stateTex.set(t.threadIndex, 1, dim);
      let hi = 0;
      if (state.selectedId === t.id) hi = 255;
      else if (searchMatches && searchMatches.has(t.id)) hi = 165;
      stateTex.set(t.threadIndex, 0, hi);
    }
  }

  function writeHover(h) {
    stateTex.clear(3, 0);
    paintBase(h);
    if (!h) { stateTex.commit(); return; }
    if (h.kind === 'thread') {
      const t = h.thread;
      const years = t.yearFounded
        ? `${t.yearFounded}–${t.yearCeased ?? (t.endState === 'still' ? 'now' : '?')}`
        : 'founding year unrecorded';
      const third = t.ghost ? 'catalog entry only'
        : `${t.evidenceCount} item${t.evidenceCount === 1 ? '' : 's'} of evidence`;
      tip.innerHTML = '';
      addLine(tip, 'tip-name', t.name);
      addLine(tip, 'tip-meta', `${t.city || 'city unrecorded'} · ${years}`);
      addLine(tip, 'tip-ev', third);
      if (t.endState === 'unrecorded') addLine(tip, 'tip-ev', 'end date unrecorded');
      if (t.endState === 'still') addLine(tip, 'tip-ev', 'still publishing');
      stateTex.set(t.threadIndex, 3, 2);
    } else {
      const k = h.knot;
      tip.innerHTML = '';
      addLine(tip, 'tip-name', k.event.title);
      addLine(tip, 'tip-meta', k.event.date);
      if (k.confidence === 'medium') addLine(tip, 'tip-ev', 'medium confidence');
      if (k.context) addLine(tip, 'tip-ev', 'context — not tied to a specific publication');
    }
    stateTex.commit();
  }

  function addLine(parent, cls, text) {
    const s = document.createElement('span');
    s.className = cls;
    s.textContent = text;
    parent.appendChild(s);
  }

  // ---- pluck ----
  // Picking a thread plucks it. The wave runs in the vertex shader off three
  // uniforms, so a pluck adds no draw call and no CPU work per frame beyond
  // writing its age. Under reduced motion the amplitude is zero and the
  // highlight lands at once instead.
  const canHover = window.matchMedia('(hover: hover) and (pointer: fine)');
  let pluckStart = -1;

  function applyMotionPref() {
    pluckUniforms.uPluckAmp.value = reduceMotion.matches ? 0 : 1;
    if (reduceMotion.matches) { pluckStart = -1; pluckUniforms.uPluckAge.value = 99; }
  }
  applyMotionPref();
  reduceMotion.addEventListener('change', () => { applyMotionPref(); app.needsRender = true; });

  function pluck(t) {
    if (!t || reduceMotion.matches) return;
    const slots = model.layout.slots;
    const above = slots[t.globalIndex - 1];
    const below = slots[t.globalIndex + 1];
    pluckUniforms.uPluckIdx.value.set(
      t.threadIndex,
      above ? above.threadIndex : -1,
      below ? below.threadIndex : -1
    );
    // The ripple is sized in screen pixels, so a thread moves about ten pixels
    // whatever the zoom. It is capped, because at the widest view ten pixels of
    // travel would be three decades of rows.
    const rect = canvas.getBoundingClientRect();
    const dist = camera.position.distanceTo(controls.target);
    const worldPerPx = (2 * Math.tan((camera.fov * Math.PI) / 360) * dist) / Math.max(1, rect.height);
    pluckUniforms.uPluckScale.value = Math.max(0.5, Math.min(2.5, worldPerPx * 50));
    pluckUniforms.uPluckAge.value = 0;
    pluckStart = performance.now();
    app.needsRender = true;
  }
  app.pluck = pluck;

  // ---- the growing edge ----
  // The cloth draws itself in as the reader moves right. Panning left never
  // undoes it: once a year has been seen it stays drawn for the session. Nothing
  // rides the edge — the reveal is the effect, and it carries no data of its own.
  const CLOTH_MAX_X = 73;
  let weaveMax = 0;

  function updateWeave() {
    const dist = camera.position.distanceTo(controls.target);
    const halfW = Math.tan((camera.fov * Math.PI) / 360) * camera.aspect * dist;
    const lead = controls.target.x + halfW * 0.88;
    const want = Math.max(0, Math.min(1, lead / CLOTH_MAX_X));
    if (want > weaveMax) weaveMax = want;
    const busy = (app.tour && app.tour.isPlaying) || (app.ghost && app.ghost.isPlaying);
    const cur = weaveUniform.value;
    if (cur < weaveMax) {
      // A tour or the ghost sequence drives the camera itself. There the cloth
      // is already there before the camera arrives; nobody is doing the weaving.
      const snap = busy || reduceMotion.matches;
      const next = snap ? weaveMax : cur + (weaveMax - cur) * 0.12;
      weaveUniform.value = weaveMax - next < 0.0006 ? weaveMax : next;
      app.needsRender = true;
    }
  }

  app.select = async function select(id, opts) {
    const t = model.byId.get(id);
    if (!t) return;
    // Already the selected thread, already framed. The reader clicking it again
    // wants the record back, not a camera move that goes nowhere — which is what
    // clicking the thread a search had just jumped to used to do.
    if (state.selectedId === id && !opts.silent && !panel.isOpen()) {
      hideTip();
      panel.openPublication(t, model, { playStory: (s) => app.playStory(s) });
      return;
    }
    markInteracted();
    state.selectedId = id;
    state.scrollTwin = !!opts.fromTwin;
    hideTip();
    paintBase(null);
    stateTex.commit();
    app.needsRender = true;
    syncTwin(state);
    history.replaceState(null, '', `?pub=${id}`);
    const box = {
      minX: t.unknownFounding ? 0 : t.x0, maxX: t.unknownFounding ? 73 : Math.max(t.x1, t.x0 + 4),
      minY: t.y - 1.2, maxY: t.y + 1.2
    };
    await app.easeTo([(box.minX + box.maxX) / 2, t.y], fitDistance(box, 0.2, camera), 700);
    // Struck after the camera lands, so the ripple is sized for the zoom the
    // reader ends up at rather than the one they started from.
    pluck(t);
    if (!opts.silent) panel.openPublication(t, model, { playStory: (s) => app.playStory(s) });
    announce(`${t.name}. ${t.city || 'city unrecorded'}. ${t.yearFounded ?? 'founding year unrecorded'}.`);
  };

  function openKnot(k) {
    panel.openEvent(k, model, {});
    announce(`${k.event.title}. ${k.event.date}.`);
  }

  panel.initPanel(() => { app.needsRender = true; });

  // ---- top bar ----
  // Reset means reset: the framing, the zoom, any camera move still running, the
  // search, the tooltip, and the panels. Half a reset is a bug report.
  function resetView() {
    if (app.tour && app.tour.isPlaying) app.tour.exit();
    if (app.ghost && app.ghost.isPlaying) app.ghost.exit();
    panel.closePanel();
    hideCards();
    clearSearch();
    hideTip();
    state.selectedId = null;
    paintBase(null);
    stateTex.clear(3, 0);
    stateTex.commit();
    syncTwin(state);
    userMoved = false;
    applyView(defaultFraming());
    announce(`The whole loom. ${model.counts.total} publications, 1880 to 2026.`);
  }
  document.getElementById('btn-reset').addEventListener('click', resetView);
  document.getElementById('btn-whole').addEventListener('click', () => {
    applyView(wholeLoomFraming());
    announce(`The whole loom. ${model.counts.total} publications, 1880 to 2026.`);
  });
  document.getElementById('btn-era-prev').addEventListener('click', () => stepReadingBand(-1));
  document.getElementById('btn-era-next').addEventListener('click', () => stepReadingBand(1));

  // Which decades are actually on screen, top to bottom, measured against the
  // free band between the control bars and the year rail.
  function visibleBands() {
    const k = keepOut();
    const dist = camera.position.distanceTo(controls.target);
    const worldPerPx = (2 * Math.tan((camera.fov * Math.PI) / 360) * dist) / k.height;
    const yTop = controls.target.y + (k.height / 2 - k.top) * worldPerPx;
    const yBot = controls.target.y - (k.height / 2 - k.bottom) * worldPerPx;
    const live = model.bands.filter((b) => b.count);
    const seen = live.filter((b) => b.top >= yBot && b.top - b.height <= yTop);
    if (seen.length) return seen;
    // Between two bands: report the nearest one rather than nothing.
    const mid = controls.target.y;
    let best = live[0];
    for (const b of live) {
      const c = b.top - b.height / 2;
      if (Math.abs(c - mid) < Math.abs(best.top - best.height / 2 - mid)) best = b;
    }
    return [best];
  }

  // The chip says what the reader is looking at, so it is written from the
  // camera, not from the last button anyone pressed. Nothing about the counts is
  // typed into the page; the data says how many.
  function updateEraNow() {
    const seen = visibleBands();
    const count = seen.reduce((s, b) => s + b.count, 0);
    const dated = seen.filter((b) => b.from !== null);
    let label;
    if (!dated.length) label = seen[0].label;
    else if (dated.length === seen.length && dated.length === 1) label = dated[0].label;
    else label = `${dated[0].from} to ${dated[dated.length - 1].to}`;
    if (seen.some((b) => b.from === null) && dated.length) label += ' and undated';
    // Named, because beside the era buttons and the search count a bare range
    // and a bare number read as one more total rather than as what is on screen.
    const text = `In view: ${label} · ${count} of ${model.counts.total}`;
    // The reading band follows the view, so "earlier" and "later" step from
    // where the reader is rather than from where they last were.
    readingBand = seen[0].key;
    if (text === eraNowText) return;
    eraNowText = text;
    document.getElementById('woven-era-now').textContent = text;
  }

  function stepReadingBand(d) {
    markInteracted();
    const keys = model.bands.filter((b) => b.count).map((b) => b.key);
    let i = keys.indexOf(readingBand);
    i = Math.min(keys.length - 1, Math.max(0, i + d));
    readingBand = keys[i];
    applyView(readingFraming(readingBand));
    const band = model.bands.find((b) => b.key === readingBand);
    announce(`${band.label}. ${band.count} publications.`);
  }
  document.getElementById('btn-help').addEventListener('click', toggleHelp);
  document.getElementById('btn-ghost').addEventListener('click', () => app.showGhost());

  // ---- guided threads picker ----
  // This used to send the reader to the list far below the stage. Scrolling
  // eight thousand pixels away from the thing you just clicked reads as a crash,
  // so the picker opens over the loom and the document never moves.
  const tourPicker = document.getElementById('woven-tourpicker');
  const btnTours = document.getElementById('btn-tours');

  function renderTourPicker() {
    tourPicker.innerHTML = `<div class="inner">
      <h3>Guided threads</h3>
      <p>Each one walks the loom through a run of documented events, stopping at the evidence.</p>
      <ul>${model.tours.map((t) => `<li>
        <span class="tp-title">${escapeHtml(t.title)}</span>
        <span class="tp-meta">${escapeHtml(t.era)} · ${t.stops.length} stop${t.stops.length === 1 ? '' : 's'}${t.strength === 'weak' ? ' · thinly sourced' : ''}</span>
        <button type="button" class="woven-btn" data-play="${escapeHtml(t.id)}">Play this thread</button>
      </li>`).join('')}</ul>
      <p><button type="button" class="woven-btn" data-close>Close</button></p>`;
    tourPicker.querySelectorAll('[data-play]').forEach((b) => {
      b.addEventListener('click', () => {
        closeTourPicker();
        app.playStory(b.dataset.play);
      });
    });
    tourPicker.querySelector('[data-close]').addEventListener('click', closeTourPicker);
  }

  function closeTourPicker() {
    tourPicker.hidden = true;
    btnTours.setAttribute('aria-expanded', 'false');
    btnTours.focus({ preventScroll: true });
  }

  btnTours.addEventListener('click', () => {
    if (!tourPicker.hidden) { closeTourPicker(); return; }
    if (!tourPicker.innerHTML) renderTourPicker();
    hideCards();
    tourPicker.hidden = false;
    btnTours.setAttribute('aria-expanded', 'true');
    const first = tourPicker.querySelector('[data-play]');
    if (first) first.focus({ preventScroll: true });
  });

  // ---- search ----
  // A contains match over the names the model already holds. Typing lights the
  // matches and pushes the rest back; enter goes to the best one.
  const searchInput = document.getElementById('woven-search');
  const searchCount = document.getElementById('woven-search-count');
  const searchForm = document.getElementById('woven-searchform');

  function matchesFor(q) {
    const needle = q.trim().toLowerCase();
    if (needle.length < 2) return null;
    return model.threads.filter((t) =>
      String(t.name || '').toLowerCase().includes(needle) ||
      String(t.alternateName || '').toLowerCase().includes(needle) ||
      String(t.city || '').toLowerCase().includes(needle));
  }

  // Best is the shortest name that starts with what was typed, else the shortest
  // name that contains it. No scoring anybody has to trust.
  function bestMatch(list, q) {
    const needle = q.trim().toLowerCase();
    const starts = list.filter((t) => String(t.name || '').toLowerCase().startsWith(needle));
    const pool = starts.length ? starts : list;
    return pool.slice().sort((a, b) => a.name.length - b.name.length || a.name.localeCompare(b.name))[0];
  }

  // Lighting the matches and saying how many is not an answer if the reader is
  // looking at a different part of the cloth. Typing moves the view to the best
  // match on its own; enter is the same move without the wait.
  function runSearch(jump) {
    const q = searchInput.value;
    const list = matchesFor(q);
    searchMatches = list && list.length ? new Set(list.map((t) => t.id)) : null;
    if (!list) searchCount.textContent = '';
    else if (!list.length) searchCount.textContent = 'no match';
    else searchCount.textContent = `${list.length} found · enter to jump`;
    stateTex.clear(3, 0);
    paintBase(null);
    stateTex.commit();
    app.needsRender = true;
    if (app.labels) app.labels.update();
    if (jump && list && list.length) goToMatch(list, q);
  }

  function goToMatch(list, q) {
    const t = bestMatch(list, q);
    // Selected, so the thread is highlighted and named, but the record panel is
    // not thrown over the cloth while the reader is still typing.
    app.select(t.id, { silent: true });
    announce(`${t.name}. ${t.city || 'city unrecorded'}. ${list.length} match${list.length === 1 ? '' : 'es'}.`);
  }

  let searchTimer = null;
  function onSearchInput() {
    runSearch(false);
    if (searchTimer) clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchTimer = null;
      const list = matchesFor(searchInput.value);
      if (list && list.length) goToMatch(list, searchInput.value);
    }, 250);
  }

  function clearSearch() {
    if (searchTimer) { clearTimeout(searchTimer); searchTimer = null; }
    if (!searchInput) return;
    searchInput.value = '';
    searchMatches = null;
    searchCount.textContent = '';
  }

  searchInput.addEventListener('input', onSearchInput);
  searchInput.addEventListener('search', onSearchInput);
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (searchTimer) { clearTimeout(searchTimer); searchTimer = null; }
    const list = matchesFor(searchInput.value);
    if (!list || !list.length) { announce('No publication matches that.'); return; }
    goToMatch(list, searchInput.value);
  });

  // ---- fullscreen ----
  // The stage holds the canvas, the chrome, the key dock, and every panel, so
  // fullscreening the stage keeps all of them usable instead of leaving them
  // behind as siblings.
  const btnFullscreen = document.getElementById('btn-fullscreen');
  if (document.fullscreenEnabled || document.webkitFullscreenEnabled) {
    btnFullscreen.hidden = false;
    btnFullscreen.addEventListener('click', () => {
      const fsEl = document.fullscreenElement || document.webkitFullscreenElement;
      if (fsEl) {
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
      } else if (stage.requestFullscreen) {
        stage.requestFullscreen();
      } else if (stage.webkitRequestFullscreen) {
        stage.webkitRequestFullscreen();
      }
    });
    const onFullscreenChange = () => {
      const isFull = (document.fullscreenElement || document.webkitFullscreenElement) === stage;
      btnFullscreen.textContent = isFull ? 'Exit fullscreen' : 'Fullscreen';
      btnFullscreen.setAttribute('aria-label', isFull ? 'Exit fullscreen' : 'Enter fullscreen');
      // Escape exits fullscreen natively; this just keeps the renderer in sync
      // with the size change that follows.
      resize();
    };
    document.addEventListener('fullscreenchange', onFullscreenChange);
    document.addEventListener('webkitfullscreenchange', onFullscreenChange);
  }

  // ---- keyboard ----
  canvas.addEventListener('keydown', onKey);

  function focusedThreadIndex() {
    const id = state.selectedId ?? model.layout.slots[0].id;
    const t = model.byId.get(id);
    return t ? t.globalIndex : 0;
  }

  function onKey(e) {
    const slots = model.layout.slots;
    let handled = true;
    switch (e.key) {
      case 'ArrowDown': step(1); break;
      case 'ArrowUp': step(-1); break;
      case 'ArrowRight': stepEvent(1); break;
      case 'ArrowLeft': stepEvent(-1); break;
      case 'PageDown': stepBand(1); break;
      case 'PageUp': stepBand(-1); break;
      case 'Home': app.select(slots[0].id, { silent: true }); break;
      case 'End': app.select(slots[slots.length - 1].id, { silent: true }); break;
      case 'Enter': case ' ':
        if (state.selectedId != null) panel.openPublication(model.byId.get(state.selectedId), model, { playStory: (s) => app.playStory(s) });
        break;
      case 'Escape':
        if (!panel.closePanel()) {
          if (!document.getElementById('woven-tourpicker').hidden) closeTourPicker();
          else if (app.tour && app.tour.isPlaying) app.tour.exit();
          else if (app.ghost && app.ghost.isPlaying) app.ghost.exit();
          else hideCards();
        }
        break;
      case 't': case 'T': document.getElementById('btn-tours').click(); break;
      case 'g': case 'G': app.showGhost(); break;
      case '+': case '=': dolly(1 / 1.3); break;
      case '-': case '_': dolly(1.3); break;
      case '0': resetView(); break;
      case '?': toggleHelp(); break;
      default: handled = false;
    }
    if (handled) e.preventDefault();

    function step(d) {
      const i = Math.min(slots.length - 1, Math.max(0, focusedThreadIndex() + d));
      app.select(slots[i].id, { silent: true });
    }
    function stepBand(d) {
      const cur = model.byId.get(state.selectedId ?? slots[0].id);
      const bands = model.bands.filter((b) => b.count);
      let bi = bands.findIndex((b) => b.key === cur.bandKey);
      bi = Math.min(bands.length - 1, Math.max(0, bi + d));
      app.select(bands[bi].threads[0].id, { silent: true });
      announce(`${bands[bi].label}. ${bands[bi].count} publications.`);
    }
    function stepEvent(d) {
      const t = model.byId.get(state.selectedId ?? slots[0].id);
      if (!t) return;
      const evs = t.events || [];
      if (!evs.length) {
        const yr = (t.yearFounded ?? 1880) + d * 5;
        announce(`No documented events on this title. ${yr}.`);
        return;
      }
      t._ei = Math.min(evs.length - 1, Math.max(0, (t._ei ?? -1) + d));
      const k = evs[t._ei];
      app.easeTo([k.x, k.y], 14, 250);
      announce(`${k.event.date}. ${k.event.title}.${k.confidence === 'medium' ? ' Medium confidence.' : ''}`);
    }
  }

  function dolly(f) {
    markInteracted();
    const dir = camera.position.clone().sub(controls.target);
    const d = Math.min(130, Math.max(8, dir.length() * f));
    camera.position.copy(controls.target).add(dir.setLength(d));
    controls.update();
    app.needsRender = true;
  }

  // ---- tour and ghost, loaded on demand ----
  // Everything a tour does happens on the cloth. The list that starts a tour is
  // far below the stage, so the stage comes back into view before it plays.
  function showStage() {
    const r = stage.getBoundingClientRect();
    if (r.top >= 72 && r.bottom <= window.innerHeight) return;
    const y = window.scrollY + r.top - 84;
    window.scrollTo({ top: Math.max(0, y), behavior: reduceMotion.matches ? 'auto' : 'smooth' });
  }
  app.showStage = showStage;

  app.playStory = async function playStory(id) {
    showStage();
    if (!app.tour) {
      const { createTour } = await import('./tour.js');
      app.tour = createTour(app, three, model);
    }
    app.tour.start(id);
  };
  app.showGhost = async function showGhost() {
    showStage();
    if (!app.ghost) {
      const { createGhost } = await import('./ghost.js');
      app.ghost = createGhost(app, three, model);
    }
    app.ghost.start();
  };
  window.njbpWoven = {
    open: (id) => app.select(id, {}),
    playStory: (id) => app.playStory(id),
    showGhost: () => app.showGhost(),
    exit: () => { panel.closePanel(); if (app.tour) app.tour.exit(); if (app.ghost) app.ghost.exit(); }
  };

  // ---- adaptive degrade ----
  const times = [];
  let degradeStep = 0;
  let badWindows = 0;
  function sample(dt) {
    times.push(dt);
    if (times.length < 60) return;
    times.sort((a, b) => a - b);
    const median = times[30];
    times.length = 0;
    if (median > 22) badWindows++; else badWindows = 0;
    if (badWindows >= 2 && degradeStep < 4) { badWindows = 0; degrade(++degradeStep); }
  }
  function degrade(stepN) {
    if (stepN === 1) { coarseFromDegrade = true; app.forceCoarseWarp = true; }
    if (stepN === 2) { renderer.setPixelRatio(1.25); }
    if (stepN === 3) app.noDecoration = true;
    if (stepN === 4) {
      const n = document.getElementById('woven-notice');
      n.hidden = false;
      n.textContent = 'Simplified the drawing to keep it smooth.';
      announceAssertive('Simplified the drawing to keep it smooth.');
    }
  }

  // ---- render loop ----
  let last = performance.now();
  function frame(now) {
    requestAnimationFrame(frame);
    processHover();
    if (app.tween) app.tween();
    if (pluckStart >= 0) {
      const age = (now - pluckStart) / 1000;
      pluckUniforms.uPluckAge.value = age;
      if (age > 1.25) { pluckStart = -1; pluckUniforms.uPluckAge.value = 99; }
      app.needsRender = true;
    }
    updateWeave(now);
    const dist = camera.position.distanceTo(controls.target);
    updateThreadFloor(dist);
    const wantFull = dist < 45 && !app.forceCoarseWarp;
    if (warpFull.visible !== wantFull) {
      warpFull.visible = wantFull;
      warpCoarse.visible = !wantFull;
      app.needsRender = true;
    }
    const damping = controls.update();
    const active = damping || app.tween || (app.tour && app.tour.isAnimating) ||
      (app.ghost && app.ghost.isPlaying);
    if (!app.needsRender && !active) { last = now; return; }
    renderer.render(scene, camera);
    if (app.labels) app.labels.update();
    // The decade chip is written from the camera, so it is refreshed on every
    // frame that actually changed something. It writes to the DOM only when the
    // text differs.
    updateEraNow();
    app.needsRender = false;
    sample(now - last);
    last = now;
  }
  requestAnimationFrame(frame);

  canvas.addEventListener('webglcontextlost', async () => {
    if (app.tour && app.tour.isPlaying) app.tour.exit();
    const { startFallback } = await import('./fallback.js');
    const api = startFallback(model, 'lost');
    app.select = (id) => api.open(id);
    app.playStory = (id) => api.playStory(id);
    app.showGhost = () => api.showGhost();
    if (state.selectedId != null) api.open(state.selectedId);
  });

  // ---- deep links ----
  if (params.get('pub')) app.select(+params.get('pub'), {});
  if (params.get('story')) app.playStory(params.get('story'));
  if (params.get('ghost') === '1') app.showGhost();

  // Debug handle. Nothing on the page reads it; it exists so the loom can be
  // driven and measured from outside without a second copy of the maths.
  window.__woven = { app, renderer, scene, camera, model, controls, THREE, pick };
}

function hideCards() {
  document.getElementById('woven-help-card').hidden = true;
  document.getElementById('woven-ghostcard').hidden = true;
  const picker = document.getElementById('woven-tourpicker');
  if (picker) picker.hidden = true;
}

// The button says "about this loom", so the panel answers that first and gives
// the controls second. Instructions only; nothing here restates the metaphor.
function toggleHelp() {
  const card = document.getElementById('woven-help-card');
  if (!card.innerHTML) {
    // Close sits at the top, above the copy, because the copy is longer than a
    // phone screen and a way out that is below the fold is not a way out. The
    // panel scrolls inside itself rather than growing past the stage.
    card.innerHTML = `<div class="inner">
      <div class="card-head">
        <h3>About this loom</h3>
        <button type="button" class="woven-btn" data-close>Close</button>
      </div>
      <p>This is every Black-owned and Black-focused publication we have found in New Jersey, drawn on one axis of time. Left to right is 1880 to 2026. Each horizontal thread is one publication, running from the year it was founded to the year it stopped, and the rows are grouped by the decade each paper began. A thicker thread means more surviving material we can show you. A faint, frayed one means the paper survives only as a line in a catalog.</p>
      <h4>By pointer</h4>
      <dl>
        <dt>Drag</dt><dd>move across the cloth, left, right, up, or down</dd>
        <dt>Scroll or pinch</dt><dd>zoom in to read names, out to see the whole span</dd>
        <dt>Point at a thread</dt><dd>read its name, city, and dates</dd>
        <dt>Click a thread</dt><dd>open that publication</dd>
        <dt>Search field</dt><dd>type a name, press enter to go to it</dd>
      </dl>
      <h4>By keyboard</h4>
      <dl>
        <dt>Up and down</dt><dd>move between publications</dd>
        <dt>Left and right</dt><dd>move between events on this publication</dd>
        <dt>Page up and page down</dt><dd>move between decades</dd>
        <dt>Enter</dt><dd>open this publication</dd>
        <dt>Escape</dt><dd>go back</dd>
        <dt>T · G · 0</dt><dd>guided threads · what did not survive · reset the view</dd>
        <dt>Escape</dt><dd>close this panel</dd>
      </dl>
    </div>`;
    card.querySelector('[data-close]').addEventListener('click', () => { card.hidden = true; });
  }
  card.hidden = !card.hidden;
  if (!card.hidden) card.querySelector('[data-close]').focus({ preventScroll: true });
}

// Escape closes whatever is over the stage, wherever the focus happens to be.
// Bound to the document because these panels take focus off the canvas, and the
// canvas was the only thing listening.
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  const help = document.getElementById('woven-help-card');
  const picker = document.getElementById('woven-tourpicker');
  const ghostCard = document.getElementById('woven-ghostcard');
  let closed = false;
  if (help && !help.hidden) { help.hidden = true; closed = true; }
  if (picker && !picker.hidden) {
    picker.hidden = true;
    closed = true;
    const btn = document.getElementById('btn-tours');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }
  if (ghostCard && !ghostCard.hidden) { ghostCard.hidden = true; closed = true; }
  if (closed) {
    e.stopPropagation();
    const canvas = document.getElementById('woven-canvas');
    if (canvas) canvas.focus({ preventScroll: true });
  }
});
