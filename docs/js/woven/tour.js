// Woven — story mode. Camera keyframes, dimming, clipping panels, tour bar.
// Every string the overlay shows comes from a data field. Nothing is composed.

import * as THREE from 'three';
import { PANEL_VERT, PANEL_FRAG } from './shaders.js';
import { announce, syncTwin } from './twin.js';
import { easeInOutCubic, X_PER_YEAR } from './layout.js';

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const DWELL = 3200;
const TRANSIT_MS = 1600;
// The era crossing is the first leg of the next stop's arrival, so it is kept
// short: the reader pressed "next stop", not "watch the loom".
const TRANSIT_TRAVEL_MS = 850;
const MAX_TEXTURES = 4;
// A local scene inside one thread usually moves in a matter of weeks to a
// couple of years. A fixed reference beats measuring each tour against its
// own average: a two-stop tour has no "average" but the one jump it makes,
// and a tour with one big outlier just drags its own average up to meet it.
// Either way the jump stops looking like one.
const NORMAL_STOP_GAP_YEARS = 6;
const LONG_MOVE_YEARS = NORMAL_STOP_GAP_YEARS * 1.5;

export function createTour(app, three, model) {
  const { scene, camera, controls, stateTex, knots } = three;
  const bar = document.getElementById('woven-tourbar');
  const overlay = document.getElementById('woven-overlay');
  const card = document.getElementById('woven-card');

  // A phone gives the card about 250 pixels and a stop can run to 550. The copy
  // scrolls, but a phone draws no scrollbar until you touch it, so a long stop
  // reads as a sentence cut in half. This button says there is more and takes
  // you there.
  //
  // The copy and the button are separate boxes: the copy scrolls, the button
  // does not. A button laid over the scrolling copy cut whatever line happened
  // to be behind it in half, which is the thing it was there to prevent. Both
  // are permanent children of the card, so a stop rewrites the copy and nothing
  // else.
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';
  card.appendChild(cardBody);

  const moreEl = document.createElement('div');
  moreEl.className = 'card-more';
  moreEl.hidden = true;
  moreEl.innerHTML = '<button type="button" class="woven-btn">More ↓</button>';
  moreEl.querySelector('button').addEventListener('click', () => {
    cardBody.scrollBy({ top: cardBody.clientHeight - 40, behavior: 'smooth' });
  });
  card.appendChild(moreEl);
  cardBody.addEventListener('scroll', () => updateMore());

  function updateMore() {
    const room = cardBody.scrollHeight - cardBody.clientHeight;
    const atEnd = cardBody.scrollTop >= room - 4;
    moreEl.hidden = room < 12 || atEnd;
  }

  // An era change is not a stop. It is the opening of the stop that follows it:
  // the camera crosses the gap while this banner names where it is going, and
  // the stop lands at the end of the same move. Read as a stop of its own it was
  // a blank screen with a bare box on it, and it broke the count.
  const transitEl = document.createElement('div');
  transitEl.id = 'woven-transit';
  transitEl.hidden = true;
  three.stage.appendChild(transitEl);

  function showTransit(tr) {
    // The bands group papers by the year they were founded, not by the year of
    // the stop, so the banner says so. "Traveling to 1900 to 1929" over a stop
    // dated 1938 reads as a wrong date.
    const dated = /^\d/.test(tr.toBand);
    transitEl.classList.remove('tr-light');
    transitEl.innerHTML =
      `<span class="tr-eyebrow">${dated ? 'Traveling to papers founded' : 'Traveling to'}</span>` +
      `<b>${esc(tr.toBand)}</b>`;
    transitEl.hidden = false;
  }
  // A move between two stops in the same era band can still be a jump of a
  // decade or two along one thread — a camera crossing that much empty cloth
  // with no signpost reads as nothing happening. This is the same banner, in
  // a lighter voice, naming only the year it is headed to.
  function showLightTransit(lm) {
    transitEl.classList.add('tr-light');
    transitEl.innerHTML =
      `<span class="tr-eyebrow">Moving ahead to</span><b>${esc(lm.label)}</b>`;
    transitEl.hidden = false;
  }
  function hideTransit() { transitEl.hidden = true; transitEl.classList.remove('tr-light'); }

  const cache = new Map(); // webPath -> THREE.Texture, LRU by insertion order
  let panelMesh = null;
  let panelSize = { w: 0, h: 0 };
  let frameLines = null;
  let loadingFrame = null;
  let loadingEdge = null;
  let tour = null;
  let stops = [];
  let index = 0;
  let playing = false;
  let paused = false;
  let timer = null;
  let preTourView = null;
  // The bar reads "end of thread" only once the reader has walked off the last
  // stop. Reading it off the last index instead meant the ninth stop of nine
  // never showed its own number.
  let closed = false;
  // Every stop gets a number. A camera move, an image decode, and an unfurl all
  // finish after the stop that asked for them, so each of them checks this
  // number before it draws. Without it, stop 3's clipping and caption landed on
  // screen while the reader was already at stop 5.
  let run = 0;

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
    closed = false;
    playing = true;
    // A tour always opens paused. The reader drives with "next stop"; the
    // Play button starts autoplay only if they ask for it. Autoplaying on
    // open made a manual "next stop" feel like it had skipped a stop, because
    // the timer was already mid-dwell when the reader pressed it.
    paused = true;
    preTourView = {
      target: [controls.target.x, controls.target.y, 0],
      position: [camera.position.x, camera.position.y, camera.position.z]
    };
    dimForTour(t);
    history.replaceState(null, '', `?story=${encodeURIComponent(t.id)}`);
    app.state.tourId = t.id;
    app.state.stopIndex = 0;
    syncTwin(app.state);
    announce(`Guided thread: ${t.title}. ${t.stops.length} stops, ${t.era}.`);
    renderBar();
    goTo(0);
  }

  // Every entry here is a real stop. Where consecutive stops change era band the
  // crossing is attached to the later stop as its opening move, so the count,
  // the progress rail, and one press of "next stop" all mean the same thing.
  function withTransits(t) {
    return t.stops.map((s, i) => {
      const prevStop = t.stops[i - 1];
      if (!prevStop) return s;
      if (prevStop.band && s.band && prevStop.band !== s.band) {
        const a = model.bands.find((b) => b.key === prevStop.band);
        const b = model.bands.find((b2) => b2.key === s.band);
        if (!a || !b) return s;
        const box = {
          minX: 0, maxX: 73,
          minY: Math.min(a.top - a.height, b.top - b.height),
          maxY: Math.max(a.top, b.top)
        };
        return Object.assign({}, s, {
          transit: {
            tx: (prevStop.tx + s.tx) / 2,
            ty: (prevStop.ty + s.ty) / 2,
            distance: app.fitDistance(box, 0.10),
            fromBand: a.label, toBand: b.label
          }
        });
      }
      // Same band, or one end undated: still flag a jump of years along one
      // thread, so the camera crossing that empty stretch of cloth reads as a
      // deliberate move to somewhere — the 1976 to 1993 jump inside one band
      // showed nothing, because only band crossings got a banner.
      const yearsGap = Math.abs(s.tx - prevStop.tx) / X_PER_YEAR;
      if (yearsGap > LONG_MOVE_YEARS) {
        const year = /^\d{4}/.exec(String(s.dateLabel || ''));
        return Object.assign({}, s, { longMove: { label: year ? year[0] : s.dateLabel } });
      }
      return s;
    });
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
    const my = ++run;
    // Whatever the last stop had queued belongs to the last stop.
    clearTimer();
    const forward = i > index;
    closed = false;
    index = Math.max(0, Math.min(stops.length - 1, i));
    const s = stops[index];
    // The previous stop's evidence goes before the next stop is drawn, never
    // after its camera move lands. Left up, an 1862 stop showed a 1991 citation
    // for the length of the transit, which reads as the wrong source.
    disposePanel();
    hideTransit();
    overlay.hidden = true;
    app.state.stopIndex = tourStopIndex();
    syncTwin(app.state);
    renderBar();
    renderCard(s);
    knots.setTour(new Set(tour.stops.map((x) => x.eventId)), s.eventId);
    app.needsRender = true;
    if (s.transit && forward && !reduced()) {
      showTransit(s.transit);
      announce(`Moving from ${s.transit.fromBand}, to ${s.transit.toBand}.`);
      await app.easeTo([s.transit.tx, s.transit.ty], s.transit.distance, TRANSIT_TRAVEL_MS);
      if (!playing || my !== run) { hideTransit(); return; }
    } else if (s.longMove && forward && !reduced()) {
      showLightTransit(s.longMove);
      announce(`Moving ahead to ${s.longMove.label}.`);
    }
    await app.easeTo([s.tx, s.ty], s.distance, reduced() ? 0 : TRANSIT_MS);
    hideTransit();
    // The reader can leave, or move on, while the camera is still moving or a
    // clipping is still decoding. Once they have, this stop no longer has a
    // place on screen, so it stops here rather than drawing over the new one.
    if (!playing || my !== run) return;
    // The "in view" chip is normally read from the camera's vertical position,
    // which answers "which founding-decade row is this" rather than "what year
    // is this stop" — the two can disagree for a thread whose events range
    // over decades. Now that the camera has landed, the chip is written from
    // the stop itself, so it always names the year the stop card does.
    if (app.setEraNow) app.setEraNow(`In view: ${s.dateLabel || tour.era} · ${tour.stops.length} stop${tour.stops.length === 1 ? '' : 's'} in this thread`);
    await showPanel(s, my);
    if (my !== run) return;
    if (!playing) { disposePanel(); return; }
    announceStop(s);
    // A stop with three paragraphs needs longer than a stop with one. The dwell
    // grows with the copy so no stop is taken away half read.
    if (!paused) schedule(dwellFor(s));
  }

  // 3.2 seconds, plus about a fifth of a second per ten words, capped at nine.
  function dwellFor(s) {
    const words = ((s.event && s.event.description) || '').split(/\s+/).length +
      (index === 0 ? (tour.thread || '').split(/\s+/).length : 0);
    return Math.min(9000, DWELL + words * 22);
  }

  function tourStopIndex() { return index; }

  function announceStop(s) {
    const th = s.threadId != null ? model.byId.get(s.threadId) : null;
    announce(`Stop ${tourStopIndex() + 1} of ${tour.stops.length}. ${s.dateLabel}. ${s.event.title}.` +
      (th ? ` ${th.name}.` : '') + (s.confidence === 'medium' ? ' Medium confidence.' : ''));
  }

  function schedule(ms) {
    clearTimer();
    if (reduced()) return;
    const my = run;
    timer = setTimeout(() => {
      timer = null;
      // The reader may have paused, moved on, or left in the milliseconds
      // between this timer firing and this line running.
      if (!playing || paused || my !== run) return;
      if (index >= stops.length - 1) { renderClose(); return; }
      goTo(index + 1);
    }, ms);
  }

  function clearTimer() { if (timer) { clearTimeout(timer); timer = null; } }

  // Any manual move stops the tour playing itself. Two taps on "next stop"
  // used to land three or four stops on, because the autoplay timer was still
  // counting alongside them.
  function pauseForManual() {
    paused = true;
    clearTimer();
    run++;
  }
  function next() { pauseForManual(); if (index < stops.length - 1) goTo(index + 1); else renderClose(); }
  function prev() { pauseForManual(); goTo(index - 1); }

  function exit() {
    if (!playing) return;
    clearTimer();
    playing = false;
    closed = false;
    tour = null;
    hideTransit();
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

  async function showPanel(s, my) {
    if (my !== run) return;
    disposePanel();
    const clip = s.clipping;
    if (!clip || !clip.webPath || !clip.altText) { renderOverlay(s, null, my); return; }

    // The clipping is sized and placed to fit the view this stop ends at, not to
    // a fixed offset. On the last stop the fixed offset put the page off the
    // right edge, where it is evidence nobody can read. All of this comes from
    // the clipping's own recorded width and height, so it does not wait on the
    // image itself to decode.
    const halfTan = Math.tan((camera.fov * Math.PI) / 360);
    // Measured on the plane the clipping actually sits on, three units in front
    // of the cloth, where it looks bigger than the cloth behind it.
    const viewH = 2 * halfTan * Math.max(4, s.distance - 3.0);
    const viewW = viewH * camera.aspect;
    const ar = (clip.width || 3) / (clip.height || 4);
    // On a phone the stage is a short strip and the story card already holds the
    // foot of it. A clipping at desktop size covered the loom outright, so there
    // was nothing left to place the evidence against. Here it is a thumbnail, and
    // it sits high, so a band of cloth stays in view under it.
    const narrow = three.canvas.getBoundingClientRect().width < 700;
    let h = Math.min(narrow ? 2.6 : 4.5, viewH * (narrow ? 0.34 : 0.62));
    let w = h * ar;
    const maxW = viewW * (narrow ? 0.5 : 0.36);
    if (w > maxW) { w = maxW; h = w / ar; }
    // Always in the right half of the view, and always whole. The story card is
    // anchored to the left edge, so a clipping placed on the left is a clipping
    // behind the card; and a fixed offset ran the last stop off the right edge.
    const pad = 0.35;
    const left = s.tx - viewW / 2 + w / 2 + pad;
    const right = s.tx + viewW / 2 - w / 2 - pad;
    const px = Math.min(right, Math.max(left, s.tx + viewW * 0.25));
    const py = Math.min(s.ty + viewH / 2 - h / 2 - pad,
      Math.max(s.ty - viewH / 2 + h / 2 + pad, s.ty + (narrow ? viewH * 0.2 : 0)));

    let tex = cache.get(clip.webPath);
    if (!tex) {
      // A full-size scan can take a couple of seconds to fetch and decode. An
      // outlined, dimmed frame at the clipping's own size and place says the
      // evidence is coming and where — a blank stretch of loom for those two
      // seconds read as broken instead.
      showLoadingFrame(w, h, px, py);
      try {
        const img = new Image();
        img.src = clip.webPath;
        await img.decode();
        if (my !== run) { hideLoadingFrame(); return; }
        tex = new THREE.Texture(img);
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.generateMipmaps = true;
        tex.minFilter = THREE.LinearMipmapLinearFilter;
        tex.anisotropy = Math.min(4, three.renderer.capabilities.getMaxAnisotropy());
        tex.needsUpdate = true;
      } catch {
        hideLoadingFrame();
        renderOverlay(s, null, my);
        return;
      }
      while (cache.size >= MAX_TEXTURES) {
        const oldest = cache.keys().next().value;
        cache.get(oldest).dispose();
        cache.delete(oldest);
      }
      cache.set(clip.webPath, tex);
    }
    hideLoadingFrame();
    const geo = new THREE.PlaneGeometry(w, h, 8, 6);
    const mat = new THREE.ShaderMaterial({
      vertexShader: PANEL_VERT, fragmentShader: PANEL_FRAG,
      uniforms: { uMap: { value: tex }, uTime: { value: 0 }, uOpacity: { value: 1 } },
      transparent: true, side: THREE.DoubleSide
    });
    panelMesh = new THREE.Mesh(geo, mat);
    panelSize = { w, h };
    panelMesh.position.set(px, py, 3.0);
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
    if (my !== run) { disposePanel(); return; }
    renderOverlay(s, clip, my);
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
    hideLoadingFrame();
  }

  // A dimmed fill and an orange outline, sized and placed exactly where the
  // clipping will land. Shown only while a scan not already in the texture
  // cache is being fetched and decoded, so a repeat visit to the same stop
  // never shows it.
  function showLoadingFrame(w, h, px, py) {
    const geo = new THREE.PlaneGeometry(w, h);
    const mat = new THREE.MeshBasicMaterial({ color: 0x2b2318, transparent: true, opacity: 0.55, side: THREE.DoubleSide });
    loadingFrame = new THREE.Mesh(geo, mat);
    loadingFrame.position.set(px, py, 3.0);
    scene.add(loadingFrame);
    loadingEdge = new THREE.LineSegments(
      new THREE.EdgesGeometry(geo),
      new THREE.LineBasicMaterial({ color: 0xe2662b, transparent: true, opacity: 0.7 })
    );
    loadingEdge.position.copy(loadingFrame.position);
    scene.add(loadingEdge);
    app.needsRender = true;
  }

  function hideLoadingFrame() {
    if (loadingFrame) { scene.remove(loadingFrame); loadingFrame.geometry.dispose(); loadingFrame.material.dispose(); loadingFrame = null; }
    if (loadingEdge) { scene.remove(loadingEdge); loadingEdge.geometry.dispose(); loadingEdge.material.dispose(); loadingEdge = null; }
    app.needsRender = true;
  }

  // ---- DOM overlay and cards. All text lives here, never in the canvas. ----

  function renderOverlay(s, clip, my) {
    if (my !== undefined && my !== run) return;
    if (!clip) {
      // Citation-only stop. The normal case, and it must look deliberate.
      // The description is already the body of the card on the left, so this
      // block carries the citations and nothing else.
      const files = s.event.sourceFiles || [];
      const cites = [...new Set(files.map((f) => model.citeSource(f)).filter(Boolean))];
      // "A printed bibliography" is a claim about the source, so it is made only
      // where the source says so. Most of these stops cite a newspaper page we
      // hold and simply have no picture attached; telling the reader we hold no
      // page for them was false.
      const rights = files.map((f) => model.sourceRights(f));
      const citationOnly = rights.length > 0 && rights.every((r) => r === 'metadata_only');
      overlay.innerHTML = `<figure class="cite-only">
        <hr class="rail-wood">
        ${cites.map((c) => `<cite>Source: ${esc(c)}</cite>`).join('')}
        ${citationOnly ? '<p class="rights">The source is a printed bibliography. We quote it; we do not reproduce the page.</p>' : ''}
      </figure>`;
    } else {
      overlay.innerHTML = `<figure>
        <img src="${esc(clip.webPath)}" alt="${esc(clip.altText)}" width="${clip.width || ''}" height="${clip.height || ''}" hidden>
        <figcaption>${esc(clip.caption)}</figcaption>
        <cite>Source: ${esc(clip.citation)}</cite>
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
    // The keep-out bands are measured and published on the stage, so the caption
    // is clamped to the loom itself. A fixed 72px guess was shorter than the two
    // wrapped control rows, which let the card drift up onto the toolbar strip.
    const px = (name, fallback) => {
      const v = parseFloat(getComputedStyle(three.stage).getPropertyValue(name));
      return Number.isFinite(v) ? v : fallback;
    };
    const minTop = px('--woven-chrome-h', 88) + pad;
    const foot = Math.max(px('--woven-rail-h', 26), px('--woven-tourbar-h', 0)) + pad;
    const maxLeft = Math.max(pad, rect.width - w - pad);
    const maxTop = Math.max(minTop, rect.height - h - foot);
    const clampL = (l) => Math.max(pad, Math.min(maxLeft, l));
    const clampT = (t) => Math.max(minTop, Math.min(maxTop, t));

    const panel = panelMesh ? panelScreenBox() : null;
    let cardBox = null;
    if (!card.hidden) {
      const c = card.getBoundingClientRect();
      cardBox = { left: c.left - rect.left, right: c.right - rect.left, top: c.top - rect.top, bottom: c.bottom - rect.top };
    }

    // A visible publication name is a keep-out too. Without it, a slot picked
    // for being clear of the panel and the card could still land squarely on
    // "The Newark Herald" — clear of the two boxes this code knew about, and
    // reading as a caption that had drifted off its own clipping.
    const labelBoxes = Array.from(three.stage.querySelectorAll('.thread-label')).map((el) => {
      const r = el.getBoundingClientRect();
      return { left: r.left - rect.left, right: r.right - rect.left, top: r.top - rect.top, bottom: r.bottom - rect.top };
    });

    const slots = [];
    if (panel) {
      slots.push([panel.right + pad, clampT(panel.top)]);
      slots.push([panel.left - pad - w, clampT(panel.top)]);
      slots.push([clampL(panel.left), panel.bottom + pad]);
      slots.push([clampL(panel.left), panel.top - pad - h]);
    }
    slots.push([maxLeft, maxTop], [maxLeft, minTop]);

    // First pass keeps clear of the panel, the card, and every name on screen.
    // The second pass drops the name check: a caption anchored beside its own
    // clipping but over a name is still legible and still attached to its
    // evidence, which beats the absolute fallback below losing both.
    for (const strict of [true, false]) {
      for (const [l, t] of slots) {
        if (l < pad || l > maxLeft || t < minTop || t > maxTop) continue;
        const box = { left: l, right: l + w, top: t, bottom: t + h };
        if (panel && overlaps(box, panel)) continue;
        if (cardBox && overlaps(box, cardBox)) continue;
        if (strict && labelBoxes.some((lb) => overlaps(box, lb))) continue;
        place(l, t);
        return;
      }
    }
    place(maxLeft, maxTop);

    function place(l, t) {
      overlay.style.left = `${clampL(l)}px`;
      overlay.style.top = `${clampT(t)}px`;
    }
  }

  function renderCard(s) {
    const th = s.threadId != null ? model.byId.get(s.threadId) : null;
    cardBody.innerHTML = `
      <h3>${esc(s.event.title)}</h3>
      <p>${esc(s.event.description)}</p>
      ${th ? `<p class="band">${esc(th.name)} · ${esc(th.city || 'city unrecorded')}</p>` : '<p class="band">Context — not tied to a specific publication.</p>'}
      ${s.confidence === 'medium' ? '<p class="flag">Medium confidence</p>' : ''}
      ${tour.strength === 'weak' && index === 0 ? '<p class="flag">Thinly sourced. This thread rests on two cover artifacts and one dated clipping. Read it as a lead, not a finding.</p>' : ''}
      ${index === 0 ? `<p>${esc(tour.thread)}</p>` : ''}`;
    card.hidden = false;
    // A long stop scrolls. Every stop starts at its own first line, never part
    // way down where the last one was left.
    cardBody.scrollTop = 0;
    updateMore();
  }

  function renderClose() {
    clearTimer();
    // The way out of the end state is one control, in the bar, and it reads
    // "back to the loom". A second button beside it doing the same thing under
    // a different name is a choice the reader does not have.
    run++;
    closed = true;
    disposePanel();
    hideTransit();
    cardBody.innerHTML = `
      <h3>${esc(tour.title)}</h3>
      <p>${esc(tour.thread)}</p>
      <p><button type="button" class="woven-btn" data-act="ghost">Show what did not survive</button></p>`;
    card.hidden = false;
    cardBody.scrollTop = 0;
    updateMore();
    cardBody.querySelector('[data-act="ghost"]').addEventListener('click', () => { exit(); app.showGhost(); });
    overlay.hidden = true;
    renderBar();
  }

  function renderBar(focusAct) {
    const total = tour.stops.length;
    const n = tourStopIndex() + 1;
    // Under reduced motion nothing plays itself, so there is no play control at
    // all — the reader advances with "next stop". Otherwise the one control
    // names the action it is about to take, not the state it happens to be
    // in: "Play" starts autoplay, "Pause" stops it, and the label switches
    // the instant the state does. A tour opens paused, so this is the first
    // thing the reader sees, and it must say "Play" — a button that says
    // "Pause" on a tour that never started playing is a false signal.
    // On the last stop there is nowhere further to go, so "next stop" is not
    // offered as a control that does nothing. The end of a thread is a place,
    // and it says so and gives the reader the way out.
    const atEnd = closed;
    bar.innerHTML = `
      ${reduced() || atEnd ? '' : `<button type="button" class="woven-btn" data-act="play" aria-pressed="${paused ? 'false' : 'true'}">${paused ? 'Play' : 'Pause'}</button>`}
      <button type="button" class="woven-btn" data-act="prev"${index === 0 ? ' disabled' : ''}>Previous stop</button>
      ${atEnd
        ? '<button type="button" class="woven-btn" data-act="end">Back to the loom</button>'
        : '<button type="button" class="woven-btn" data-act="next">Next stop</button>'}
      <span class="tour-title">${esc(tour.title)}${tour.strength === 'weak' ? ' · Thinly sourced' : ''}</span>
      <span class="tour-counter">${atEnd ? 'End of thread' : `Stop ${n} of ${total}`} · ${esc(stops[index].dateLabel || '')}</span>
      <span id="woven-rail" aria-hidden="true">${Array.from({ length: total }, (_, i) => `<i class="${i < n ? 'on' : ''}"></i>`).join('')}</span>
      ${atEnd ? '' : '<button type="button" class="woven-btn" data-act="exit" aria-label="Exit this thread"><span class="lbl-full">Exit this thread</span><span class="lbl-short">Exit</span></button>'}`;
    bar.hidden = false;
    const end = bar.querySelector('[data-act="end"]');
    if (end) end.addEventListener('click', exit);
    const nextBtn = bar.querySelector('[data-act="next"]');
    if (nextBtn) nextBtn.addEventListener('click', next);
    const play = bar.querySelector('[data-act="play"]');
    if (play) {
      play.addEventListener('click', () => {
        paused = !paused;
        clearTimer();
        renderBar('play');
        if (!paused) schedule(dwellFor(stops[index]));
      });
    }
    bar.querySelector('[data-act="prev"]').addEventListener('click', prev);
    const exitBtn = bar.querySelector('[data-act="exit"]');
    if (exitBtn) exitBtn.addEventListener('click', exit);
    if (focusAct) {
      const back = bar.querySelector(`[data-act="${focusAct}"]`);
      if (back) back.focus();
    }
  }

  controls.addEventListener('change', () => { if (playing && !overlay.hidden) positionOverlay(); });

  return api;
}
