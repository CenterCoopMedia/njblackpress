// Woven — entry point. Capability test, scene, render loop, router.

import { loadModel } from './data.js';
import { buildTwin, syncTwin, announce, announceAssertive, promoteTwin } from './twin.js';
import {
  fitDistance, boxCenter, easeInOutCubic
} from './layout.js';

const params = new URLSearchParams(location.search);

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
  const { buildWeft, buildWarp, createStateTexture, createClothMaterial } = await import('./cloth.js');
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

  const controls = new OrbitControls(camera, canvas);
  Object.assign(controls, {
    enableDamping: true, dampingFactor: 0.08,
    minPolarAngle: 0.96, maxPolarAngle: 1.75,
    minAzimuthAngle: -0.61, maxAzimuthAngle: 0.61,
    minDistance: 8, maxDistance: 130,
    enablePan: true, screenSpacePanning: true,
    rotateSpeed: 0.45, zoomSpeed: 0.7
  });

  const clothBox = model.layout.bounds;
  // The default framing shows the whole loom, including the posts and the loose
  // strands that run past the right post. Those crossings are the point.
  const loomBox = {
    minX: -3.2, maxX: 79.0,
    minY: Math.min(clothBox.minY, -30.2), maxY: 1.6
  };
  const centre = boxCenter(loomBox);
  app.loomBox = loomBox;
  app.fitDistance = (box, margin) => fitDistance(box, margin, camera);
  const padX = (clothBox.maxX - clothBox.minX) * 0.1;
  const padY = (clothBox.maxY - clothBox.minY) * 0.1;

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

  // Two framings. The reading window is the default because every row across a
  // 146-year axis cannot be legible at once; the whole loom is one click away.
  function wholeLoomFraming() {
    const d = fitDistance(loomBox, 0.06, camera);
    return { target: [centre[0], centre[1], 0], position: [centre[0], centre[1] + d * 0.12, d] };
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
      position: [Math.min(66, x0 + 9), mid + d * 0.12, d]
    };
  }

  let readingBand = 'C';
  function defaultFraming() { return readingFraming(readingBand); }

  function applyView(view) {
    controls.target.set(view.target[0], view.target[1], view.target[2] ?? 0);
    camera.position.set(view.position[0], view.position[1], view.position[2]);
    controls.update();
    app.needsRender = true;
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
      px: target[0], py: target[1] + distance * 0.12, pz: distance
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

  const { createLabels } = await import('./labels.js');
  const labels = createLabels(app, three, model);
  app.labels = labels;

  window.addEventListener('resize', resize);
  resize();
  applyView(defaultFraming());
  setEraNow();
  labels.update();

  // ---- picking, hover, selection ----
  const pick = createPicker(model, camera, knots);
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
  // A rotate ends with a click on the canvas. Without this the reader turns the
  // cloth and lands on a publication panel they never asked for, which on a
  // phone covers the whole stage.
  let downAt = null;
  canvas.addEventListener('pointerdown', (e) => { downAt = { x: e.clientX, y: e.clientY }; });
  canvas.addEventListener('click', (e) => {
    if (downAt && Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y) > 5) return;
    const r = canvas.getBoundingClientRect();
    const h = pick(e.clientX, e.clientY, r, e.pointerType === 'touch');
    if (!h) return;
    if (h.kind === 'knot') openKnot(h.knot);
    else app.select(h.thread.id, {});
  });

  function processHover() {
    if (!pending) return;
    const r = canvas.getBoundingClientRect();
    const h = pick(pending.x, pending.y, r, pending.touch);
    const key = h ? (h.kind === 'knot' ? `k${h.knot.index}` : `t${h.thread.id}`) : null;
    if (key !== hoverTarget) {
      hoverTarget = key;
      state.hoverId = h && h.kind === 'thread' ? h.thread.id : null;
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

  function writeHover(h) {
    stateTex.clear(3, 0);
    // Hover isolates: everything that is not the hovered thread dims, so one
    // thread can be read out of the whole cloth. Selection does not dim; only
    // hover and tours do.
    if (!(app.tour && app.tour.isPlaying) && !(app.ghost && app.ghost.isPlaying)) {
      const dimAll = h && h.kind === 'thread';
      for (const t of model.threads) {
        stateTex.set(t.threadIndex, 1, dimAll && t.id !== h.thread.id ? 208 : 0);
      }
    }
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

  app.select = async function select(id, opts) {
    const t = model.byId.get(id);
    if (!t) return;
    state.selectedId = id;
    state.scrollTwin = !!opts.fromTwin;
    stateTex.clear(0, 0);
    stateTex.set(t.threadIndex, 0, 255);
    stateTex.commit();
    app.needsRender = true;
    syncTwin(state);
    history.replaceState(null, '', `?pub=${id}`);
    const box = {
      minX: t.unknownFounding ? 0 : t.x0, maxX: t.unknownFounding ? 73 : Math.max(t.x1, t.x0 + 4),
      minY: t.y - 1.2, maxY: t.y + 1.2
    };
    await app.easeTo([(box.minX + box.maxX) / 2, t.y], fitDistance(box, 0.2, camera), 700);
    if (!opts.silent) panel.openPublication(t, model, { playStory: (s) => app.playStory(s) });
    announce(`${t.name}. ${t.city || 'city unrecorded'}. ${t.yearFounded ?? 'founding year unrecorded'}.`);
  };

  function openKnot(k) {
    panel.openEvent(k, model, {});
    announce(`${k.event.title}. ${k.event.date}.`);
  }

  panel.initPanel(() => { app.needsRender = true; });

  // ---- top bar ----
  document.getElementById('btn-reset').addEventListener('click', () => applyView(defaultFraming()));
  document.getElementById('btn-whole').addEventListener('click', () => {
    applyView(wholeLoomFraming());
    announce(`The whole loom. ${model.counts.total} publications, 1880 to 2026.`);
  });
  document.getElementById('btn-era-prev').addEventListener('click', () => stepReadingBand(-1));
  document.getElementById('btn-era-next').addEventListener('click', () => stepReadingBand(1));

  // The era label is written from the band the reader is on. Nothing about the
  // counts is typed into the page; the data says how many.
  function setEraNow() {
    const band = model.bands.find((b) => b.key === readingBand);
    if (!band) return null;
    document.getElementById('woven-era-now').textContent = `${band.label} · ${band.count}`;
    return band;
  }

  function stepReadingBand(d) {
    const keys = model.bands.filter((b) => b.count).map((b) => b.key);
    let i = keys.indexOf(readingBand);
    i = Math.min(keys.length - 1, Math.max(0, i + d));
    readingBand = keys[i];
    applyView(readingFraming(readingBand));
    const band = setEraNow();
    announce(`${band.label}. ${band.count} publications.`);
  }
  document.getElementById('btn-help').addEventListener('click', toggleHelp);
  document.getElementById('btn-ghost').addEventListener('click', () => app.showGhost());
  document.getElementById('btn-tours').addEventListener('click', () => {
    document.getElementById('woven-twin-tours').scrollIntoView({ block: 'start' });
    const first = document.querySelector('#woven-twin-tours .t-play');
    if (first) first.focus();
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
          if (app.tour && app.tour.isPlaying) app.tour.exit();
          else if (app.ghost && app.ghost.isPlaying) app.ghost.exit();
          else hideCards();
        }
        break;
      case 't': case 'T': document.getElementById('btn-tours').click(); break;
      case 'g': case 'G': app.showGhost(); break;
      case '+': case '=': dolly(1 / 1.3); break;
      case '-': case '_': dolly(1.3); break;
      case '0': applyView(defaultFraming()); break;
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
    const dist = camera.position.distanceTo(controls.target);
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

  window.__woven = { app, renderer, scene, camera, model, controls };
}

function hideCards() {
  document.getElementById('woven-help-card').hidden = true;
  document.getElementById('woven-ghostcard').hidden = true;
}

function toggleHelp() {
  const card = document.getElementById('woven-help-card');
  if (!card.innerHTML) {
    card.innerHTML = `<div class="inner">
      <h3>Moving through the loom</h3>
      <dl>
        <dt>Up and down</dt><dd>move between publications</dd>
        <dt>Left and right</dt><dd>move between events on this publication</dd>
        <dt>Page up and page down</dt><dd>move between decades</dd>
        <dt>Enter</dt><dd>open this publication</dd>
        <dt>Escape</dt><dd>go back</dd>
        <dt>T · G · 0</dt><dd>guided threads · what did not survive · reset the view</dd>
      </dl>
      <p><button type="button" class="woven-btn" data-close>Close</button></p>
    </div>`;
    card.querySelector('[data-close]').addEventListener('click', () => { card.hidden = true; });
  }
  card.hidden = !card.hidden;
  if (!card.hidden) card.querySelector('[data-close]').focus();
}
