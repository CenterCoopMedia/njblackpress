import * as THREE from 'three';
import { YEAR_MIN, YEAR_MAX } from './layout.js';
import { timelinePoint, distanceToSegment, publicationYears, threadColor, threadSpans } from './exhibit-geometry.js';
import { mountExplorer } from './explorer.js';
import { announce, syncTwin } from './twin.js';

// Two views share the renderer, data adapter, record panel,
// stories, accessible twin, and recorded publication spans.
export function mountExhibit(app, params) {
  if (params.get('view') === 'woven') params.set('view', '3d');
  const { model, three } = app;
  const { renderer, canvas, stage, controls, panel } = three;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#14100b');
  const flat = stage.dataset.renderer === 'flat';
  if (flat) {
    document.querySelector('[data-woven-view="3d"]').disabled = true;
    document.getElementById('woven-renderer-note').hidden = false;
  }
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 500);
  const gallery = new THREE.Group();
  scene.add(gallery);
  const nodes = [];
  const resources = [];
  const caption = document.getElementById('woven-exhibit-caption');
  const axis = document.getElementById('woven-exhibit-axis');
  const years = [YEAR_MIN, 1920, 1960, 2000, YEAR_MAX].map((year) => {
    const label = document.createElement('span');
    label.textContent = String(year);
    axis.append(label);
    return { year, label };
  });
  const motionButton = document.getElementById('woven-motion');
  const tip = document.getElementById('woven-tip');
  const modeButtons = [...document.querySelectorAll('[data-woven-view]')];
  const original = { select: app.select, playStory: app.playStory, showGhost: app.showGhost };
  const aborter = new AbortController();
  const listen = (target, type, handler, options = {}) => target.addEventListener(type, handler, { ...options, signal: aborter.signal });
  let active = false, dirty = true, visible = true, disposed = false;
  let motion = !app.reduceMotion.matches;
  let hovered = null, matches = null, pending = null;
  let yaw = -0.23, last = 0, elapsed = 0;
  let rect = canvas.getBoundingClientRect();
  let down = null;
  const vector = new THREE.Vector3();
  const bottom = model.layout.bounds.minY;

  const vertexShader = `varying vec3 n; varying vec2 tex;
    void main(){ n=normalize(normalMatrix*normal); tex=uv;
      gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`;
  const fragmentShader = `precision highp float;
    uniform vec3 dye; uniform float alpha; uniform float emphasis;
    uniform float ghost; uniform float unknown; uniform float segments;
    varying vec3 n; varying vec2 tex;
    void main(){
      float dash=fract(tex.x*segments);

      if(unknown>0.5 && tex.x>0.035 && dash>0.60) discard;
      float light=0.38+0.62*max(0.0,dot(normalize(n),normalize(vec3(-0.4,0.8,1.0))));
      float sheen=pow(max(0.0,dot(normalize(n),normalize(vec3(0.3,0.7,1.0)))),12.0)*0.32;
      vec3 color=dye*(light+sheen);
      color=mix(color,vec3(1.0,0.91,0.70),emphasis*0.75);
      gl_FragColor=vec4(color,alpha);
      #include <colorspace_fragment>
    }`;

  function material(color, ghost = false, unknown = false, segments = 40) {
    const value = new THREE.ShaderMaterial({
      vertexShader, fragmentShader,
      uniforms: {
        dye: { value: new THREE.Color(color) }, alpha: { value: ghost ? 0.58 : 1 },
        emphasis: { value: 0 }, ghost: { value: Number(ghost) },
        unknown: { value: Number(unknown) }, segments: { value: segments }
      },
      transparent: true, depthWrite: !ghost, side: THREE.DoubleSide
    });
    resources.push(value);
    return value;
  }
  for (const thread of flat ? [] : model.threads) {
    const mat = material(threadColor(thread), thread.ghost, thread.endState === 'unrecorded',
      Math.max(2, ((thread.yearCeased ?? YEAR_MAX) - (thread.yearFounded ?? YEAR_MIN)) / 2));
    const curves = [];
    for (const [start, end] of threadSpans(thread)) {
      const from = new THREE.Vector3(...timelinePoint(start, thread.y, bottom));
      const to = new THREE.Vector3(...timelinePoint(end, thread.y, bottom));
      const geometry = new THREE.BoxGeometry(to.x - from.x, Math.max(0.20, thread.width * 3), 0.65);
      resources.push(geometry);
      const bar = new THREE.Mesh(geometry, mat);
      bar.position.copy(from).lerp(to, 0.5);
      gallery.add(bar);
      curves.push([from, to]);
    }
    if (thread.endState === 'still') {
      const geometry = new THREE.ConeGeometry(0.25, 0.65, 3);
      resources.push(geometry);
      const arrow = new THREE.Mesh(geometry, mat);
      arrow.rotation.z = -Math.PI / 2;
      arrow.position.set(...timelinePoint(YEAR_MAX + 7, thread.y, bottom));
      gallery.add(arrow);
    }
    nodes.push({ thread, material: mat, curves, projected: [] });
  }

  function updateHighlights() {
    const focus = hovered ?? app.state.selectedId;
    for (const node of nodes) {
      const isMatch = !matches || matches.has(node.thread.id);
      const selected = node.thread.id === focus;
      node.material.uniforms.emphasis.value = selected ? 1 : 0;
      node.material.uniforms.alpha.value = (node.thread.ghost ? 0.58 : 1) *
        (isMatch ? 1 : 0.13) * (focus != null && !selected ? 0.48 : 1);
      if (selected) node.material.uniforms.alpha.value = isMatch ? 1 : 0.28;
    }
    dirty = true;
  }
  function highlight(id) { hovered = id; updateHighlights(); }
  function filter(ids) { matches = ids; updateHighlights(); app.setExploreMatches?.(ids); }
  function resetPose() { yaw = -0.23; elapsed = 0; dirty = true; }

  function resize() {
    rect = canvas.getBoundingClientRect();
    camera.aspect = Math.max(0.2, rect.width / Math.max(1, rect.height));
    const usable = Math.max(0.32, (rect.height - 150) / Math.max(1, rect.height));
    const distance = Math.max(41 / (2 * Math.tan(Math.PI * 35 / 360)) / usable,
      110 / (2 * Math.tan(Math.PI * 35 / 360) * camera.aspect));
    camera.position.set(0, 2.5, distance);
    camera.lookAt(0, 2.5, 0);
    camera.updateProjectionMatrix();
    dirty = true;
  }

  function setMode(next, { updateURL = true } = {}) {
    if (flat) next = 'timeline';
    active = next === '3d';
    stage.dataset.view = active ? '3d' : 'timeline';
    controls.enabled = !active;
    modeButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.wovenView === next)));
    motionButton.hidden = !active;
    document.getElementById('woven-turn-controls').hidden = !active;
    tip.hidden = true;
    hovered = null;
    pending = null;
    canvas.setAttribute('aria-label', active ? 'Three-dimensional timeline of New Jersey Black publications' : 'Interactive timeline of New Jersey Black publications');
    caption.textContent = active
      ? 'Left to right is time. Drag sideways to turn. Select a publication or title to read its dates.'
      : 'Left to right is time. Drag to move; scroll or pinch to zoom. Select a publication to read its record.';
    if (updateURL) {
      const url = new URL(location.href);
      url.searchParams.set('view', next);
      history.replaceState(null, '', url);
    }
    app.resize();
    if (!active) {
      app.focusBand(explorer?.era() || 'all');
      if (app.state.selectedId != null) original.select(app.state.selectedId, { silent: true });
    }
    updateHighlights();
    explorer?.syncSelected();
    app.needsRender = true;
  }

  async function open(id, opts = {}) {
    const thread = model.byId.get(id);
    if (!thread) return;
    explorer.reveal(id);
    if (!active) return original.select(id, opts);
    app.state.selectedId = id;
    hovered = null;
    tip.hidden = true;
    pending = null;
    updateHighlights();
    const url = new URL(location.href);
    url.searchParams.set('view', '3d');
    url.searchParams.set('pub', String(id));
    url.searchParams.delete('story');
    url.searchParams.delete('ghost');
    history.replaceState(null, '', url);
    syncTwin(app.state);
    if (!opts.fromTwin && !opts.silent) panel.openPublication(thread, model, { playStory: (story) => app.playStory(story) });
    explorer.syncSelected();
    announce(`${thread.name}. ${thread.city || 'City unrecorded'}. ${publicationYears(thread)}.`);
  }
  const explorer = mountExplorer(app, { highlight, filter, focusEra: (key) => {
    if (!active) app.focusBand(key);
  }, open: (id) => app.select(id, {}) });
  app.explorer = explorer;
  app.select = open;
  app.playStory = (id) => { panel.closePanel(); explorer.reset(); setMode('timeline'); return original.playStory(id); };
  app.showGhost = () => { panel.closePanel(); explorer.reset(); setMode('timeline'); return original.showGhost(); };

  function syncMotion() {
    motionButton.textContent = motion ? 'Pause motion' : 'Play motion';
    motionButton.setAttribute('aria-pressed', String(motion));
    dirty = true;
  }
  listen(motionButton, 'click', () => { motion = !motion; syncMotion(); });
  listen(app.reduceMotion, 'change', () => { motion = !app.reduceMotion.matches; syncMotion(); });
  modeButtons.forEach((button) => listen(button, 'click', () => {
    if (app.tour?.isPlaying) app.tour.exit();
    if (app.ghost?.isPlaying) app.ghost.exit();
    setMode(button.dataset.wovenView);
  }));
  document.querySelectorAll('[data-woven-turn]').forEach((button) => listen(button, 'click', () => {
    yaw = Math.max(-0.7, Math.min(0.7, yaw + Number(button.dataset.wovenTurn) * 0.14));
    dirty = true;
  }));
  for (const id of ['btn-era-prev', 'btn-era-next', 'btn-whole']) {
    listen(document.getElementById(id), 'click', () => setMode('timeline'), { capture: true });
  }
  listen(document.getElementById('btn-reset'), 'click', () => {
    explorer.reset(); resetPose();
    const url = new URL(location.href);
    for (const key of ['pub', 'story', 'ghost']) url.searchParams.delete(key);
    history.replaceState(null, '', url);
    setMode(active ? '3d' : 'timeline');
  });
  function pointerPoint(event, radius) {
    const current = canvas.getBoundingClientRect();
    return { x: event.clientX - current.left, y: event.clientY - current.top, radius };
  }
  listen(canvas, 'pointermove', (event) => {
    if (!active) return;
    if (down && event.buttons) {
      const dx = event.clientX - down.x;
      if (Math.abs(dx) > 7) {
        yaw = Math.max(-0.7, Math.min(0.7, down.yaw + dx / Math.max(1, rect.width) * 1.4));
        dirty = true; pending = null; tip.hidden = true;
      }
      return;
    }
    if (event.pointerType !== 'touch') pending = pointerPoint(event, 11);
  });
  listen(canvas, 'pointerleave', () => { if (active) { pending = null; tip.hidden = true; highlight(null); } });
  listen(canvas, 'pointerdown', (event) => { down = { x: event.clientX, y: event.clientY, yaw }; });
  listen(canvas, 'pointercancel', () => { down = null; });
  listen(canvas, 'click', (event) => {
    if (!active || (down && Math.hypot(event.clientX - down.x, event.clientY - down.y) > 8)) return;
    const point = pointerPoint(event, event.pointerType === 'touch' ? 22 : 11);
    const id = pick(point.x, point.y, point.radius);
    if (id != null) open(id);
  });
  listen(canvas, 'keydown', (event) => {
    if (!active || !['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter', 'Home', 'Escape'].includes(event.key)) return;
    event.preventDefault(); event.stopImmediatePropagation();
    if (event.key === 'Home') resetPose();
    else if (event.key === 'Escape') {
      panel.closePanel(); hovered = null; app.state.selectedId = null;
      const url = new URL(location.href); url.searchParams.delete('pub');
      history.replaceState(null, '', url);
      syncTwin(app.state); explorer.syncSelected(); updateHighlights();
    }
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      yaw = Math.max(-0.7, Math.min(0.7, yaw + (event.key === 'ArrowRight' ? 0.12 : -0.12))); dirty = true;
    } else if (event.key === 'Enter') { if (hovered != null) open(hovered); }
    else {
      const records = explorer.records();
      if (!records.length) return;
      let index = records.findIndex((thread) => thread.id === (hovered ?? app.state.selectedId));
      index = (index + (event.key === 'ArrowUp' ? -1 : 1) + records.length) % records.length;
      highlight(records[index].id);
      announce(`${records[index].name}. ${publicationYears(records[index])}. Press Enter to read the record.`);
    }
  }, { capture: true });

  function project(point) {
    vector.copy(point).applyMatrix4(gallery.matrixWorld).project(camera);
    return { x: (vector.x + 1) * rect.width / 2, y: (1 - vector.y) * rect.height / 2 };
  }
  function pick(x, y, radius) {
    let nearest = null, best = radius;
    for (const node of nodes) {
      if (matches && !matches.has(node.thread.id)) continue;
      for (const curve of node.projected) for (let i = 1; i < curve.length; i++) {
        const a = curve[i - 1], b = curve[i];
        const distance = distanceToSegment(x, y, a.x, a.y, b.x, b.y);
        if (distance < best) { best = distance; nearest = node.thread.id; }
      }
    }
    return nearest;
  }
  function showTip(id, point) {
    if (id == null) { tip.hidden = true; return; }
    const thread = model.byId.get(id);
    tip.replaceChildren();
    for (const [className, text] of [['tip-name', thread.name], ['tip-meta', `${thread.city || 'City unrecorded'} · ${publicationYears(thread)}`]]) {
      const line = document.createElement('span'); line.className = className; line.textContent = text; tip.append(line);
    }
    tip.hidden = false;
    tip.style.left = `${Math.max(8, Math.min(point.x + 14, rect.width - tip.offsetWidth - 8))}px`;
    tip.style.top = `${Math.max(70, Math.min(point.y + 14, rect.height - tip.offsetHeight - 48))}px`;
  }

  const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; dirty = true; last = 0; });
  observer.observe(stage);
  listen(document, 'visibilitychange', () => { last = 0; dirty = true; });
  const sizeObserver = new ResizeObserver(resize);
  sizeObserver.observe(canvas);
  function frame(now) {
    if (!active || disposed || !visible || document.hidden) { last = 0; return; }
    const delta = last ? Math.min(0.05, (now - last) / 1000) : 0;
    last = now;
    if (motion && !panel.isOpen() && hovered == null) { elapsed += delta; dirty = true; }
    if (dirty) {
      gallery.rotation.set(0.18, yaw + Math.sin(elapsed * 0.25) * 0.035, -0.06);
      gallery.updateMatrixWorld(true);
      camera.updateMatrixWorld(true);
      for (const { year, label } of years) {
        const point = project(new THREE.Vector3(...timelinePoint(year, 1.4, bottom)));
        label.hidden = rect.width < 600 && (year === 1920 || year === 2000);
        label.style.left = `${Math.max(24, Math.min(rect.width - 24, point.x))}px`;
        label.style.top = `${point.y - 20}px`;
      }
      for (const node of nodes) node.projected = node.curves.map((curve) => curve.map(project));
      renderer.render(scene, camera);
      dirty = false;
    }
    if (pending) {
      const point = pending; pending = null;
      const id = pick(point.x, point.y, point.radius);
      if (id !== hovered) highlight(id);
      showTip(id, point);
    }
  }
  syncMotion();
  const narrative = params.has('story') || params.has('ghost');
  const legacyPublication = params.has('pub') && params.get('view') !== '3d';
  setMode(params.get('view') === 'timeline' || narrative || legacyPublication ? 'timeline' : '3d', { updateURL: false });
  document.getElementById('woven-loading').hidden = true;
  return {
    get active() { return active; }, get motion() { return motion; },
    frame, resize, setMode, nodes, scene, camera,
    dispose() {
      if (disposed) return;
      disposed = true; active = false;
      aborter.abort(); observer.disconnect(); sizeObserver.disconnect(); explorer.dispose();
      resources.forEach((resource) => resource.dispose());
      axis.replaceChildren();
      scene.clear();
    }
  };
}
