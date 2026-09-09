// History hall — mount, dispose, and the wiring between the state, the room,
// and the page.
//
// This module owns nothing the other modules own. It reads the layout, holds
// the one authoritative state, and translates every control, deep link, and
// history event into the same commands. Animation is a consequence of a state
// change here, never the owner of what the visitor selected.

import * as THREE from 'three';
import { buildHallLayout } from './layout.js';
import { createHallState } from './state.js';
import * as links from './links.js';
import { createAssets } from './assets.js';
import { buildSpace } from './space.js';
import { buildSheets } from './sheets.js';
import { buildVolumes } from './volumes.js';
import { createRail, attachRailInput } from './rail.js';
import { createReader } from './reader.js';
import { whenFontsReady } from './paint.js';
import { buildPublicationViews, buildStoryViews } from './views.js';
import { publicationYears } from '../woven/records.js';
import { mountExplorer } from '../woven/explorer.js';
import { announce, syncTwin } from '../woven/twin.js';

export async function mountHall(app, params) {
  const { model, three } = app;
  const { renderer, canvas, stage, controls, panel } = three;
  const flat = stage.dataset.renderer === 'flat';
  const original = { select: app.select, playStory: app.playStory, showGhost: app.showGhost };
  const aborter = new AbortController();
  const listen = (target, type, handler, options = {}) =>
    target.addEventListener(type, handler, { ...options, signal: aborter.signal });

  // Read before anything can rewrite the address bar: the hall replaces the
  // current entry as soon as it settles at the entrance, and the visitor's own
  // link has to be read first.
  const initialSearch = location.search;
  const narrow = window.matchMedia('(max-width: 899px)');
  const viewButtons = [...document.querySelectorAll('[data-woven-view]')];
  const hallControls = document.getElementById('woven-hall-controls');
  const decadeSelect = document.getElementById('hall-decade');
  const whereEl = document.getElementById('hall-where');
  const noticeEl = document.getElementById('woven-notice');
  const scrollToggle = document.getElementById('hall-scroll-toggle');
  const readerRoot = document.getElementById('hall-reader');
  const inspectorRoot = document.getElementById('hall-inspector');
  const canvasLabel = {
    hall: 'History hall of New Jersey Black publications',
    timeline: 'Interactive timeline of New Jersey Black publications'
  };

  let active = false;
  let disposed = false;
  let dirty = true;
  let visible = true;
  let last = 0;
  let poolZ = -999;
  let poolSelected = null;
  let routing = false;
  // Declared before the index mounts, because the index calls back into the
  // scene as soon as it renders its first list.
  let sheets = null;
  let volumes = null;
  let rail = null;
  let input = null;
  let reader = null;
  let space = null;

  // ---- the archive as the hall reads it -----------------------------------
  const layout = buildHallLayout(model);
  const assets = createAssets({ generation: () => state.generation() });
  const stopsFor = (storyId) => (storyViews.get(storyId)?.stops || []).map((stop) => stop.key);
  const state = createHallState({ stopsForStory: stopsFor });

  // Filled in once the wall copy manifest has been read, because what a sheet
  // shows depends on whether a copy is cleared for it.
  let views = new Map();
  let storyViews = new Map();

  // ---- the flat timeline path --------------------------------------------
  // Without WebGL the hall cannot be built at all. The page keeps its flat
  // timeline, its index, and tour.js as the story path, and the hall button
  // says why it is unavailable.
  const explorer = mountExplorer(app, {
    highlight: (id) => { if (sheets) sheets.setHover(id); },
    filter: (ids) => {
      if (sheets) sheets.setMatches(ids);
      app.setExploreMatches?.(ids);
    },
    focusEra: (key) => {
      if (!active) { app.focusBand(key); return; }
      const section = sectionForBand(key);
      if (section) moveToSection(section, { immediate: true });
    },
    open: (id) => app.select(id, {})
  });
  app.explorer = explorer;

  if (flat) {
    const hallButton = document.querySelector('[data-woven-view="hall"]');
    if (hallButton) hallButton.disabled = true;
    const note = document.getElementById('woven-renderer-note');
    if (note) note.hidden = false;
    stage.dataset.view = 'timeline';
    setCanvasRole('timeline');
    viewButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.wovenView === 'timeline')));
    document.getElementById('woven-loading').hidden = true;
    return {
      get active() { return false; },
      frame() {},
      resize() {},
      setMode() {},
      layout,
      dispose() {
        aborter.abort();
        explorer.dispose();
      }
    };
  }

  await assets.loadManifest();
  views = buildPublicationViews(model, assets);
  storyViews = buildStoryViews(model, assets);

  // ---- the room ------------------------------------------------------------
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#0b0806');
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 320);
  const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const invalidate = () => { dirty = true; };
  space = buildSpace(layout, { anisotropy });
  sheets = buildSheets(layout, views, assets, { anisotropy, invalidate });
  volumes = buildVolumes(layout, storyViews, assets, {
    anisotropy, invalidate, reduceMotion: app.reduceMotion
  });
  scene.add(space.group, sheets.group, volumes.group);

  // Decision 6: the first settled view stands in the 1880s bay looking down the
  // hall, with that section's sheets on both walls at reading distance.
  const firstSlot = layout.slots[0];
  rail = createRail(camera, layout, {
    keepOut, invalidate, reduceMotion: app.reduceMotion, onSettle: settled,
    entranceTarget: firstSlot ? firstSlot.z : null
  });
  input = attachRailInput(canvas, rail, {
    signal: aborter.signal,
    enabled: () => active && state.getState().mode !== 'story' && state.getState().mode !== 'clipping',
    onActivate: activate,
    onHover: hover,
    onScrollModeEnd: () => syncScrollToggle()
  });

  reader = createReader({
    root: readerRoot,
    inspector: inspectorRoot,
    narrow,
    onPrevious: () => state.prevStop(),
    onNext: () => state.nextStop(),
    onClose: () => closeTop(),
    onGotoStop: (key) => state.gotoStop(key),
    onSelectPublication: (id) => app.select(id, {}),
    copyLink: () => new URL(links.format(state.getState()), location.href).toString()
  });

  const stopFonts = whenFontsReady(() => {
    // The faces were painted with the fallback stack; repaint them now that the
    // real faces are here. Entry never waited for this.
    sheets.repaint();
    dirty = true;
  });

  // ---- view switching -----------------------------------------------------
  function setCanvasRole(view) {
    if (view === 'hall') {
      // The hall has a complete DOM equivalent, so the canvas is not a control
      // and is not announced.
      canvas.removeAttribute('role');
      canvas.removeAttribute('tabindex');
      canvas.setAttribute('aria-hidden', 'true');
    } else {
      canvas.setAttribute('role', 'application');
      canvas.setAttribute('tabindex', '0');
      canvas.removeAttribute('aria-hidden');
      canvas.setAttribute('aria-label', canvasLabel.timeline);
    }
  }

  function applyView(view) {
    active = view === 'hall';
    stage.dataset.view = view;
    controls.enabled = !active;
    setCanvasRole(view);
    viewButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.wovenView === view)));
    hallControls.hidden = !active;
    input.setScrollMode(false);
    if (!active) {
      reader.close();
      volumes.closeVolume();
      app.focusBand(explorer.era() || 'all');
      const selected = state.getState().selectedPublicationId;
      if (selected != null) original.select(selected, { silent: true });
    }
    app.resize();
    dirty = true;
    app.needsRender = true;
  }

  function keepOut() {
    const rect = canvas.getBoundingClientRect();
    const height = Math.max(1, rect.height);
    const controlsHeight = hallControls.hidden ? 0 : hallControls.getBoundingClientRect().height;
    const chrome = document.getElementById('woven-chrome');
    const top = (chrome ? chrome.getBoundingClientRect().height : 80) + controlsHeight + 12;
    const bottom = 56;
    return { height, top, bottom, free: Math.max(60, height - top - bottom) };
  }

  // ---- movement and selection ---------------------------------------------
  function sectionForBand(key) {
    if (key === 'all' || !key) return layout.sections[0];
    const band = model.bands.find((item) => item.key === key);
    if (!band || !band.threads || !band.threads.length) return null;
    const first = band.threads.slice().sort((a, b) => (a.yearFounded ?? 9999) - (b.yearFounded ?? 9999))[0];
    const slot = layout.slotByPublicationId.get(first.id);
    return slot ? layout.sectionById.get(slot.sectionId) : null;
  }

  function moveToSection(section, options = {}) {
    if (!section) return;
    rail.goToSection(section, options);
    state.moveTo({ kind: 'section', id: section.id, z: section.entryAnchor.position.z });
  }

  function settled() {
    updatePool(false);
    const section = rail.section;
    if (whereEl) {
      whereEl.textContent = section.empty
        ? `${section.label}. No titles recorded.`
        : `${section.label}. ${section.count} publication${section.count === 1 ? '' : 's'}.`;
    }
    if (decadeSelect && decadeSelect.value !== section.id && document.activeElement !== decadeSelect) {
      decadeSelect.value = section.id;
    }
    const current = state.getState();
    if (current.mode === 'browse' && current.anchor?.id !== section.id) {
      state.moveTo({ kind: 'section', id: section.id, z: section.startZ });
    }
    space.follow(rail.z);
    dirty = true;
  }

  // Reassigning the painted pool means sorting every slot, so it happens when
  // the visitor has actually moved or chosen something, not on every pointer
  // event during a drag.
  function updatePool(force) {
    const selected = state.getState().selectedPublicationId ?? null;
    if (!force && selected === poolSelected && Math.abs(rail.z - poolZ) < 1.2) return;
    poolZ = rail.z;
    poolSelected = selected;
    sheets.updatePool(rail.z, selected);
  }

  function hover(event) {
    if (!active) return;
    const rect = canvas.getBoundingClientRect();
    const hit = sheets.pick(event.clientX - rect.left, event.clientY - rect.top, rect, camera);
    sheets.setHover(hit ? hit.publicationId : null);
    dirty = true;
  }

  // Whichever of the two is actually in front takes the click. Without the
  // comparison a volume on a table would take a click aimed at a sheet behind it.
  function activate(event) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const book = pickBook(x, y, rect);
    const sheet = sheets.pick(x, y, rect, camera);
    if (book && (!sheet || book.distance <= sheet.distance)) { app.playStory(book.storyId); return; }
    if (sheet) app.select(sheet.publicationId, {});
  }

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  function pickBook(x, y, rect) {
    pointer.set((x / rect.width) * 2 - 1, -(y / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(volumes.pickables(), false);
    return hits.length ? { storyId: hits[0].object.userData.storyId, distance: hits[0].distance } : null;
  }

  function closeTop() {
    if (reader.inspectorOpen) { reader.closeInspector(); return; }
    const current = state.getState();
    if (current.mode === 'story' || current.mode === 'publication') {
      panel.closePanel();
      state.close();
      return;
    }
    rail.toEntrance();
  }

  // ---- the one place that reacts to a state change ------------------------
  function react(next, before) {
    dirty = true;
    if (next.view !== before.view) {
      applyView(next.view);
      pushRoute();
      return;
    }
    if (next.mode === 'publication' && next.selectedPublicationId !== before.selectedPublicationId) {
      const slot = layout.slotByPublicationId.get(next.selectedPublicationId);
      if (slot) rail.focusSlot(slot);
      sheets.setSelected(next.selectedPublicationId);
      updatePool(true);
      app.state.selectedId = next.selectedPublicationId;
      syncTwin(app.state);
      explorer.syncSelected();
      const publication = model.byId.get(next.selectedPublicationId);
      if (publication) {
        announce(`${publication.name}. ${publication.city || 'City unrecorded'}. ${publicationYears(publication)}.`);
      }
      pushRoute();
      return;
    }
    if (next.mode === 'story' && next.storyId !== before.storyId) {
      openStoryScene(next.storyId, next.stopId);
      pushRoute();
      return;
    }
    if (next.mode === 'story' && next.stopId !== before.stopId) {
      const story = storyViews.get(next.storyId);
      const stop = story.stops.find((item) => item.key === next.stopId);
      const previous = story.stops.find((item) => item.key === before.stopId) || null;
      volumes.showStop(stop, { previous });
      reader.setStop(stop);
      announce(`Stop ${stop.index + 1} of ${story.stopCount}. ${stop.date}. ${stop.title}.`);
      replaceRoute();
      return;
    }
    if (next.mode !== before.mode) {
      if (next.mode === 'browse') {
        reader.close();
        volumes.closeVolume();
        panel.closePanel();
        sheets.setSelected(next.selectedPublicationId);
        app.state.selectedId = next.selectedPublicationId ?? null;
        app.state.tourId = null;
        syncTwin(app.state);
        explorer.syncSelected();
        replaceRoute();
      } else if (next.mode === 'publication') {
        reader.close();
        volumes.closeVolume();
        const slot = layout.slotByPublicationId.get(next.selectedPublicationId);
        if (slot) rail.focusSlot(slot);
        sheets.setSelected(next.selectedPublicationId);
      } else if (next.mode === 'story') {
        openStoryScene(next.storyId, next.stopId);
      }
    }
    if (next.anchor !== before.anchor && next.mode === 'browse') replaceRoute();
    dirty = true;
  }

  function openStoryScene(storyId, stopId) {
    const story = storyViews.get(storyId);
    if (!story) return;
    panel.closePanel();
    const stop = story.stops.find((item) => item.key === stopId) || story.stops[0];
    // The text is usable now. The book catches up with it.
    reader.open(story, stop);
    const slot = layout.bookSlotByStoryId.get(storyId);
    if (slot) rail.focusBook(slot);
    volumes.openVolume(storyId, stop);
    app.state.tourId = storyId;
    app.state.stopIndex = stop.index;
    syncTwin(app.state);
    announce(`${story.title}. ${story.stopCount} stop${story.stopCount === 1 ? '' : 's'}. ${story.era}.`);
    if (state.getState().unknownStop) {
      notice('That stop is not part of this story, so it opens at the first stop.');
    }
    dirty = true;
  }

  function notice(message) {
    if (!noticeEl) return;
    noticeEl.hidden = !message;
    noticeEl.textContent = message || '';
  }

  state.subscribe(react);

  // ---- routes and history --------------------------------------------------
  function routeUrl() {
    const current = state.getState();
    return links.format({
      view: current.view,
      storyId: current.storyId,
      stopId: current.stopId,
      selectedPublicationId: current.selectedPublicationId,
      anchor: current.anchor
    });
  }

  function pushRoute() {
    if (routing) return;
    const url = routeUrl();
    if (url !== `${location.search}`) history.pushState(null, '', url);
  }

  function replaceRoute() {
    if (routing) return;
    history.replaceState(null, '', routeUrl());
  }

  function applyRoute(search, { initial = false } = {}) {
    const parsed = links.parse(search);
    const checked = links.validate(parsed, model, layout);
    const view = links.resolveView(parsed, { canRenderHall: true });
    notice(checked.issues.length ? checked.issues[0].message : '');
    routing = true;
    if (view === 'text') {
      applyView('timeline');
      state.setView('timeline');
      routing = false;
      return;
    }
    applyView(view === 'timeline' ? 'timeline' : 'hall');
    state.setView(view === 'timeline' ? 'timeline' : 'hall');
    routing = false;
    if (view === 'timeline') return;
    const target = checked.target;
    if (target.kind === 'story') state.openStory(target.id, target.stop);
    else if (target.kind === 'publication') app.select(target.id, {});
    else if (target.kind === 'decade') moveToSection(layout.sectionById.get(target.id), { immediate: true });
    else if (initial) rail.toEntrance({ immediate: true });
  }

  listen(window, 'popstate', () => {
    // Back and forward restore the state; they never create a new entry.
    routing = true;
    const parsed = links.parse(location.search);
    const checked = links.validate(parsed, model, layout);
    const view = links.resolveView(parsed, { canRenderHall: true });
    if (view !== state.getState().view) { applyView(view === 'hall' ? 'hall' : 'timeline'); state.setView(view === 'hall' ? 'hall' : 'timeline'); }
    if (checked.target.kind === 'story') state.openStory(checked.target.id, checked.target.stop);
    else if (checked.target.kind === 'publication') state.selectPublication(checked.target.id);
    else if (checked.target.kind === 'decade') moveToSection(layout.sectionById.get(checked.target.id), { immediate: true });
    else state.close();
    routing = false;
  });

  // ---- controls -------------------------------------------------------------
  viewButtons.forEach((button) => listen(button, 'click', () => {
    if (app.tour?.isPlaying) app.tour.exit();
    if (app.ghost?.isPlaying) app.ghost.exit();
    state.setView(button.dataset.wovenView === 'hall' ? 'hall' : 'timeline');
  }));

  if (decadeSelect) {
    decadeSelect.replaceChildren(...layout.sections.map((section) => {
      const option = document.createElement('option');
      option.value = section.id;
      option.textContent = section.empty ? `${section.label} (no titles)` : `${section.label} (${section.count})`;
      return option;
    }));
    listen(decadeSelect, 'change', () => {
      moveToSection(layout.sectionById.get(decadeSelect.value), { immediate: true });
    });
  }

  function stepDecade(direction) {
    const index = layout.sections.findIndex((section) => section.id === rail.section.id);
    const next = layout.sections[Math.min(layout.sections.length - 1, Math.max(0, index + direction))];
    moveToSection(next, { immediate: Math.abs(direction) > 1 });
  }
  listen(document.getElementById('hall-previous-decade'), 'click', () => stepDecade(-1));
  listen(document.getElementById('hall-next-decade'), 'click', () => stepDecade(1));
  listen(document.getElementById('hall-entrance'), 'click', () => {
    panel.closePanel();
    state.close();
    rail.toEntrance({ immediate: true });
    announce('Back at the entrance of the hall.');
  });

  function syncScrollToggle() {
    if (!scrollToggle) return;
    scrollToggle.setAttribute('aria-pressed', String(input.scrollMode));
    scrollToggle.textContent = input.scrollMode ? 'Stop scrolling to move' : 'Use scroll to move';
  }
  if (scrollToggle) {
    listen(scrollToggle, 'click', () => {
      input.setScrollMode(!input.scrollMode);
      syncScrollToggle();
    });
    syncScrollToggle();
  }

  listen(document, 'keydown', (event) => {
    if (!active || event.key !== 'Escape') return;
    if (reader.inspectorOpen || reader.isOpen || panel.isOpen() || state.getState().mode !== 'browse') {
      event.stopPropagation();
      closeTop();
    }
  }, { capture: true });

  // ---- overrides -----------------------------------------------------------
  app.select = async function open(id, opts = {}) {
    const publication = model.byId.get(id);
    if (!publication) return;
    explorer.reveal(id);
    if (!active) return original.select(id, opts);
    panel.closePanel();
    state.selectPublication(id, {});
    sheets.setSelected(id);
    if (!opts.silent && !opts.fromTwin) {
      panel.openPublication(publication, model, { playStory: (story) => app.playStory(story) });
    }
    app.state.selectedId = id;
    syncTwin(app.state);
    explorer.syncSelected();
  };

  app.playStory = function playStory(id, options = {}) {
    if (!active) return original.playStory(id);
    app.showStage?.();
    state.openStory(id, options.stop || null, {});
    return undefined;
  };

  app.showGhost = function showGhost() {
    // The gaps sequence belongs to the flat timeline, so the view changes first.
    panel.closePanel();
    state.setView('timeline');
    return original.showGhost();
  };

  // ---- frame loop -----------------------------------------------------------
  const observer = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    last = 0;
    dirty = true;
  });
  observer.observe(stage);
  listen(document, 'visibilitychange', () => { last = 0; dirty = true; });

  function resize() {
    const rect = canvas.getBoundingClientRect();
    camera.aspect = Math.max(0.2, rect.width / Math.max(1, rect.height));
    // A tall, narrow window sees a much narrower slice of a six metre corridor,
    // so a portrait screen gets a wider lens and can stand closer to the sheets.
    camera.fov = camera.aspect < 1 ? 71 : 50;
    camera.updateProjectionMatrix();
    const current = state.getState();
    if (current.mode === 'publication' && current.selectedPublicationId != null) {
      const slot = layout.slotByPublicationId.get(current.selectedPublicationId);
      if (slot) rail.refocus(rail.poseForSlot(slot));
    } else if (current.mode === 'story' && current.storyId) {
      const slot = layout.bookSlotByStoryId.get(current.storyId);
      if (slot) rail.refocus(rail.poseForBook(slot));
    } else {
      rail.apply();
    }
    dirty = true;
  }
  const sizeObserver = new ResizeObserver(() => resize());
  sizeObserver.observe(canvas);

  function frame(now) {
    if (!active || disposed || !visible || document.hidden) { last = 0; return; }
    let busy = rail.frame(now);
    if (volumes.frame(now)) busy = true;
    if (sheets.work()) busy = true;
    if (!dirty && !busy) { last = now; return; }
    renderer.render(scene, camera);
    dirty = false;
    // The page's adaptive sampler only sees frames the hall actually drew, so
    // an idle hall never counts as a slow one.
    if (last) app.sampleFrameInterval?.(now - last);
    last = now;
  }

  // ---- entry ---------------------------------------------------------------
  resize();
  rail.toEntrance({ immediate: true });
  updatePool(true);
  settled();
  applyRoute(initialSearch, { initial: true });
  document.getElementById('woven-loading').hidden = true;

  return {
    get active() { return active; },
    frame,
    resize,
    setMode(view) { state.setView(view === 'hall' || view === '3d' ? 'hall' : 'timeline'); },
    layout,
    state,
    scene,
    camera,
    rail,
    sheets,
    volumes,
    reader,
    assets,
    dispose() {
      if (disposed) return;
      disposed = true;
      active = false;
      aborter.abort();
      observer.disconnect();
      sizeObserver.disconnect();
      stopFonts();
      reader.dispose();
      explorer.dispose();
      sheets.dispose();
      volumes.dispose();
      space.dispose();
      assets.dispose();
      scene.clear();
      hallControls.hidden = true;
      setCanvasRole('timeline');
      // The page's own handlers come back exactly as they were.
      app.select = original.select;
      app.playStory = original.playStory;
      app.showGhost = original.showGhost;
    }
  };
}
