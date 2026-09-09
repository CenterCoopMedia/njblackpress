// History hall — where the camera may stand and how it gets there.
//
// The visitor travels along one centre line and stops at authored poses. There
// is no free walking, no head bob, no roll, and no camera turn on hover. Every
// move ends somewhere the layout says is a valid place to stand, which is how
// the camera can never pass through a wall, a frame, or a reading table.

import * as THREE from 'three';

export const RAIL_CONFIG = {
  // Prototyped against real content: long enough to read as a move, short
  // enough that nobody waits for it. Text never waits for either.
  nearMoveMs: 420,
  focusMs: 520,
  // Anything further than this is a jump, not a walk, so it cuts straight there
  // rather than travelling through the decades in between.
  cutDistance: 14,
  metresPerPixel: 0.028,
  wheelMetresPerUnit: 0.02,
  maxWheelStep: 2.4,
  dragThreshold: 8,
  margin: 1.14,
  minFocusDistance: 1.5,
  maxFocusDistance: 4.4
};

const easeOut = (k) => 1 - Math.pow(1 - k, 3);

export function createRail(camera, layout, options = {}) {
  const config = layout.config;
  const keepOut = options.keepOut || (() => ({ height: 1, free: 1, top: 0, bottom: 0 }));
  const invalidate = options.invalidate || (() => {});
  const reduceMotion = options.reduceMotion || { matches: false };
  const onSettle = options.onSettle || (() => {});

  const minZ = 0.6;
  // Where the hall begins for the visitor. The distance is not a constant: a
  // narrow phone window sees a much narrower slice of the hall, so the entrance
  // stands back far enough for the first section's sheets on both walls to be
  // in view at reading distance whatever the shape of the window.
  const entranceTarget = options.entranceTarget ?? null;
  const maxZ = Math.max(minZ + 1, layout.length - 1.2);
  const position = new THREE.Vector3(0, config.eyeHeight, minZ);
  const look = new THREE.Vector3(0, config.eyeHeight, minZ + 4);
  let from = null;
  let to = null;
  let started = 0;
  let duration = 0;
  let settled = true;

  function entranceZ() {
    if (entranceTarget == null) return layout.sections[0]?.entryAnchor.position.z ?? minZ;
    const halfHorizontal = Math.atan(Math.tan((camera.fov * Math.PI) / 360) * camera.aspect);
    // Far enough back that the nearest sheet on each wall is whole in the view,
    // and no further: standing off in the distance turns the entrance into an
    // empty corridor. The cap keeps a tall, narrow window close enough to read.
    const clear = config.frame.width / 2 + (config.wallX + 0.1) / Math.tan(halfHorizontal);
    return Math.max(minZ, entranceTarget - Math.min(7, Math.max(4.5, clear)));
  }

  function apply() {
    camera.position.copy(position);
    camera.up.set(0, 1, 0);
    camera.lookAt(look);
    invalidate();
  }

  /**
   * The visible band of the canvas, once the hall's own controls at the top and
   * the line of text at the foot are taken out. A sheet is fitted into what is
   * left, never into the whole rectangle.
   */
  function fitDistance(width, height) {
    const box = keepOut();
    const ratio = Math.max(1, box.height / Math.max(40, box.free));
    const vFov = (camera.fov * Math.PI) / 180;
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * camera.aspect);
    const vertical = ((height / 2) / Math.tan(vFov / 2)) * ratio;
    const horizontal = (width / 2) / Math.tan(hFov / 2);
    return Math.max(vertical, horizontal) * RAIL_CONFIG.margin;
  }

  /** The sheet's centre is put in the middle of that free band, not the canvas. */
  function verticalOffset(distance) {
    const box = keepOut();
    const worldPerPixel = (2 * Math.tan((camera.fov * Math.PI) / 360) * distance) / Math.max(1, box.height);
    const offsetPixels = (box.top + box.free / 2) - box.height / 2;
    return offsetPixels * worldPerPixel;
  }

  function poseForSlot(slot) {
    const sign = slot.wall === 'left' ? -1 : 1;
    const wallFace = sign * config.wallX;
    const raw = fitDistance(config.frame.width, config.frame.height);
    const distance = Math.min(RAIL_CONFIG.maxFocusDistance, Math.max(RAIL_CONFIG.minFocusDistance, raw));
    const offset = verticalOffset(distance);
    return {
      position: new THREE.Vector3(wallFace - sign * distance, config.eyeHeight, slot.z),
      look: new THREE.Vector3(wallFace, slot.y + offset, slot.z)
    };
  }

  // A reader standing in the corridor beside the table, far enough back that
  // both pages of the spread are in view at once.
  function poseForBook(book) {
    const sign = book.wall === 'left' ? -1 : 1;
    const look = new THREE.Vector3(book.position.x, config.table.height + 0.16, book.position.z);
    // The open spread runs along the table, so what has to fit across the view
    // is its length, and the visitor stands in the corridor opposite it.
    // Close enough that the spread fills the band the controls leave clear and
    // the headline on the right page can be read.
    const raw = fitDistance(book.size.width * 1.85, book.size.height * 0.8);
    const distance = Math.min(4.2, Math.max(1.5, raw));
    const x = Math.max(-(config.corridorHalfWidth - 0.1), Math.min(config.corridorHalfWidth - 0.1, look.x - sign * distance));
    // The controls cover the top of the canvas, so the spread is aimed into the
    // band that is left, exactly as a sheet is.
    look.y += verticalOffset(distance);
    return {
      position: new THREE.Vector3(x, config.eyeHeight, book.position.z),
      look
    };
  }

  // Six metres ahead is where the sheets a visitor is walking toward sit, so the
  // level view is aimed into the band of canvas the controls leave clear.
  const BROWSE_REFERENCE = 6;

  function poseForZ(z) {
    const clamped = Math.min(maxZ, Math.max(minZ, z));
    return {
      position: new THREE.Vector3(0, config.eyeHeight, clamped),
      look: new THREE.Vector3(
        0,
        config.eyeHeight - 0.04 + verticalOffset(BROWSE_REFERENCE),
        clamped + BROWSE_REFERENCE
      )
    };
  }

  function moveTo(pose, { immediate = false, ms = RAIL_CONFIG.nearMoveMs } = {}) {
    const far = pose.position.distanceTo(position) > RAIL_CONFIG.cutDistance;
    if (immediate || far || reduceMotion.matches || ms === 0) {
      position.copy(pose.position);
      look.copy(pose.look);
      from = null;
      to = null;
      settled = true;
      apply();
      onSettle();
      return;
    }
    // New intent cancels whatever was in flight; nothing queues up.
    from = { position: position.clone(), look: look.clone() };
    to = { position: pose.position.clone(), look: pose.look.clone() };
    started = performance.now();
    duration = ms;
    settled = false;
    invalidate();
  }

  function frame(now) {
    if (!to) return false;
    const k = Math.min(1, (now - started) / duration);
    const e = easeOut(k);
    position.lerpVectors(from.position, to.position, e);
    look.lerpVectors(from.look, to.look, e);
    apply();
    if (k >= 1) { from = null; to = null; settled = true; onSettle(); return false; }
    return true;
  }

  function travelTo(z, opts) {
    moveTo(poseForZ(z), opts);
  }

  function travelBy(dz) {
    // Dragging is direct: the hall moves under the hand, with no easing tail.
    // It uses the same pose as every other move, so the pitch never jumps
    // between the end of a drag and the start of a button move.
    const pose = poseForZ((to ? to.position.z : position.z) + dz);
    position.copy(pose.position);
    look.copy(pose.look);
    from = null;
    to = null;
    settled = true;
    apply();
    onSettle();
  }

  function sectionAt(z) {
    for (const section of layout.sections) {
      if (z >= section.startZ && z < section.endZ) return section;
    }
    // Before the first section is still the first section, not the last one.
    return z < layout.sections[0].startZ
      ? layout.sections[0]
      : layout.sections[layout.sections.length - 1];
  }

  return {
    frame,
    moveTo,
    travelTo,
    travelBy,
    poseForSlot,
    poseForBook,
    poseForZ,
    focusSlot(slot, opts) { moveTo(poseForSlot(slot), { ms: RAIL_CONFIG.focusMs, ...opts }); },
    focusBook(book, opts) { moveTo(poseForBook(book), { ms: RAIL_CONFIG.focusMs, ...opts }); },
    toEntrance(opts) { moveTo(poseForZ(entranceZ()), opts); },
    goToSection(section, opts) { moveTo(poseForZ(section.entryAnchor.position.z), opts); },
    /** A resize changes the fit, so the current focus pose is recomputed. */
    refocus(pose) { if (pose) moveTo(pose, { immediate: true }); },
    get z() { return position.z; },
    get settled() { return settled; },
    get section() { return sectionAt(position.z); },
    sectionAt,
    apply,
    bounds: { minZ, maxZ }
  };
}

/**
 * Pointer, wheel, and key input for the rail. Kept apart from the camera maths
 * so the input contract can be read in one place.
 *
 * Horizontal drag moves along the hall. A vertical drag on touch is left alone
 * so the page still scrolls. The wheel scrolls the page unless the visitor turns
 * on "Use scroll to move", which ends on blur, on a view change, and when a
 * reader opens.
 */
export function attachRailInput(canvas, rail, options = {}) {
  const isEnabled = options.enabled || (() => true);
  const onActivate = options.onActivate || (() => {});
  const onHover = options.onHover || (() => {});
  const onScrollModeEnd = options.onScrollModeEnd || (() => {});
  const signal = options.signal;
  let scrollMode = false;
  let down = null;
  let dragging = false;

  const listen = (target, type, handler, opts = {}) =>
    target.addEventListener(type, handler, { ...opts, signal });

  listen(canvas, 'pointerdown', (event) => {
    if (!isEnabled()) return;
    down = { x: event.clientX, y: event.clientY, id: event.pointerId, touch: event.pointerType === 'touch' };
    dragging = false;
  });

  listen(canvas, 'pointermove', (event) => {
    if (!isEnabled()) return;
    if (!down || event.pointerId !== down.id) {
      if (event.pointerType !== 'touch') onHover(event);
      return;
    }
    const dx = event.clientX - down.x;
    const dy = event.clientY - down.y;
    // A vertical drag on a touch screen belongs to the page, not to the hall.
    if (down.touch && Math.abs(dy) > Math.abs(dx)) return;
    if (!dragging && Math.abs(dx) < RAIL_CONFIG.dragThreshold) return;
    dragging = true;
    rail.travelBy(-dx * RAIL_CONFIG.metresPerPixel);
    down.x = event.clientX;
    down.y = event.clientY;
  });

  const release = () => { down = null; };
  listen(canvas, 'pointerup', release);
  listen(canvas, 'pointercancel', () => { down = null; dragging = false; });
  listen(canvas, 'pointerleave', () => { down = null; });

  listen(canvas, 'click', (event) => {
    if (!isEnabled()) return;
    // A drag that ends on the canvas is not a selection.
    if (dragging) { dragging = false; return; }
    onActivate(event);
  });

  listen(canvas, 'wheel', (event) => {
    if (!scrollMode || !isEnabled()) return;   // The page scrolls by default.
    event.preventDefault();
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? 400 : 1;
    const raw = (event.deltaY * unit) * RAIL_CONFIG.wheelMetresPerUnit;
    const step = Math.max(-RAIL_CONFIG.maxWheelStep, Math.min(RAIL_CONFIG.maxWheelStep, raw));
    // At either end the page keeps its own scrolling rather than trapping it.
    rail.travelBy(step);
  }, { passive: false });

  listen(window, 'blur', () => { if (scrollMode) { scrollMode = false; onScrollModeEnd(); } });

  return {
    get scrollMode() { return scrollMode; },
    setScrollMode(value) {
      if (scrollMode === value) return;
      scrollMode = value;
      if (!value) onScrollModeEnd();
    },
    get dragging() { return dragging; }
  };
}
