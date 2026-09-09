// History hall — the bound volumes on the reading tables.
//
// One closed volume per guided story, resting where the layout put it. Opening
// one shows a spread: the cleared clipping on the left page, the stop's title
// and date on the right. A stop with no cleared clipping gets a deliberate text
// page, never invented historical paper.
//
// The volumes are contemporary containers for the guided stories. They are not
// evidence that a matching physical book exists, and the reader says so.

import * as THREE from 'three';
import { paintCover, paintPage, textureFrom } from './paint.js';

const TURN_MS = 520;
const OPEN_MS = 340;
// A page turn that skips several stops is not worth simulating page by page.
const MAX_SIMULATED_SKIP = 1;

export function buildVolumes(layout, storyViews, assets, options = {}) {
  const config = layout.config;
  const anisotropy = options.anisotropy || 4;
  const invalidate = options.invalidate || (() => {});
  const reduceMotion = options.reduceMotion || { matches: false };
  const group = new THREE.Group();
  group.name = 'hall-volumes';
  const disposables = [];
  const track = (thing) => { disposables.push(thing); return thing; };

  const pageWidth = config.book.width - 0.04;
  const pageHeight = config.book.height - 0.06;
  // A page lying on a table, read from the near side of the hall: its top edge
  // is the far edge, so the type runs the way a reader standing here expects.
  const flat = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, Math.PI));
  const flipped = new THREE.Quaternion()
    .setFromEuler(new THREE.Euler(0, 0, Math.PI))
    .multiply(flat);

  // ---- closed volumes -----------------------------------------------------
  const bookMeshes = [];
  const blockMaterial = track(new THREE.MeshLambertMaterial({ color: '#3b3122' }));
  const blockGeometry = track(new THREE.BoxGeometry(config.book.width, config.book.thickness, config.book.height));
  const coverGeometry = track(new THREE.PlaneGeometry(config.book.width - 0.06, config.book.height - 0.06));
  for (const slot of layout.bookSlots) {
    const view = storyViews.get(slot.storyId);
    const block = new THREE.Mesh(blockGeometry, blockMaterial);
    block.position.set(slot.position.x, slot.position.y, slot.position.z);
    block.name = `volume-${slot.storyId}`;
    block.userData.storyId = slot.storyId;
    block.userData.bayId = slot.bayId;
    block.userData.homeZ = slot.position.z;
    const cover = new THREE.Mesh(
      coverGeometry,
      track(new THREE.MeshBasicMaterial({ map: track(textureFrom(paintCover(view, view.eraColor), anisotropy)) }))
    );
    cover.quaternion.copy(flat);
    cover.position.set(0, config.book.thickness / 2 + 0.002, 0);
    cover.userData.decorative = true;
    block.add(cover);
    group.add(block);
    bookMeshes.push(block);
  }

  // ---- the open volume ----------------------------------------------------
  // Two groups: the outer one turns the volume to face the corridor, so the
  // spread runs along the table rather than hanging over its edge, and the
  // inner one gives it a small lectern tilt.
  const facing = new THREE.Group();
  facing.visible = false;
  const open = new THREE.Group();
  facing.add(open);
  group.add(facing);

  const leftPivot = new THREE.Group();
  const rightPivot = new THREE.Group();
  const leaf = new THREE.Group();
  open.add(leftPivot, rightPivot, leaf);

  // Cover boards a little larger than the pages on every side, a spine ridge at
  // the gutter, and a block of page edges under each half. Without them a spread
  // reads as a loose sheet lying on the table rather than as a bound volume.
  const coverMaterial = track(new THREE.MeshLambertMaterial({ color: '#3b3122' }));
  const spineMaterial = track(new THREE.MeshLambertMaterial({ color: '#2b2318' }));
  const edgeMaterial = track(new THREE.MeshLambertMaterial({ color: '#e6ddc7' }));
  const coverBoard = new THREE.Mesh(
    track(new THREE.BoxGeometry(pageWidth * 2 + 0.08, 0.022, pageHeight + 0.07)),
    coverMaterial
  );
  const spine = new THREE.Mesh(
    track(new THREE.BoxGeometry(0.07, 0.05, pageHeight + 0.07)),
    spineMaterial
  );
  // One unit tall, scaled per stop: the two stacks trade height as the visitor
  // reads, so how far through the story they are is visible on the table.
  const stackGeometry = track(new THREE.BoxGeometry(pageWidth, 1, pageHeight));
  const leftStack = new THREE.Mesh(stackGeometry, edgeMaterial);
  const rightStack = new THREE.Mesh(stackGeometry, edgeMaterial);
  open.add(coverBoard, spine, leftStack, rightStack);

  function makePage(sign, segments = 1) {
    const geometry = new THREE.PlaneGeometry(pageWidth, pageHeight, segments, 1);
    const material = new THREE.MeshBasicMaterial({ side: THREE.FrontSide });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(sign * pageWidth / 2, 0, 0);
    mesh.quaternion.copy(flat);
    return mesh;
  }
  // The visitor stands at the near end of the hall looking along it, so their
  // right hand points along negative x. The left page therefore sits at
  // positive x and the right page at negative x, or the spread reads backwards.
  const leftPage = makePage(1);
  const rightPage = makePage(-1);
  leftPivot.add(leftPage);
  rightPivot.add(rightPage);

  // The turning leaf: its front carries the page that is leaving, its back the
  // page arriving underneath. Both are segmented so the leaf can bend a little
  // around the spine instead of turning as a board.
  const leafFront = makePage(-1, 6);
  const leafBack = makePage(-1, 6);
  leafBack.quaternion.copy(flipped);
  leafBack.position.set(-pageWidth / 2, -0.004, 0);
  leafFront.position.set(-pageWidth / 2, 0.004, 0);
  leaf.add(leafFront, leafBack);
  leaf.visible = false;

  const baseFront = leafFront.geometry.attributes.position.array.slice();
  const baseBack = leafBack.geometry.attributes.position.array.slice();

  const BLOCK_MIN = 0.016;
  const BLOCK_SPAN = 0.072;

  function setBlock(index, count) {
    const through = count > 1 ? index / (count - 1) : 0.5;
    const leftHeight = BLOCK_MIN + BLOCK_SPAN * through;
    const rightHeight = BLOCK_MIN + BLOCK_SPAN * (1 - through);
    // The left page is at positive x: the visitor's right hand points along
    // negative x when they look down the hall.
    leftStack.scale.y = leftHeight;
    leftStack.position.set(pageWidth / 2, leftHeight / 2, pageHeight / 2);
    rightStack.scale.y = rightHeight;
    rightStack.position.set(-pageWidth / 2, rightHeight / 2, pageHeight / 2);
    leftPivot.position.set(0, leftHeight + 0.002, pageHeight / 2);
    rightPivot.position.set(0, rightHeight + 0.002, pageHeight / 2);
    leaf.position.set(0, Math.max(leftHeight, rightHeight) + 0.006, pageHeight / 2);
    coverBoard.position.set(0, -0.011, pageHeight / 2);
    spine.position.set(0, 0.014, pageHeight / 2);
  }

  function setPageTexture(mesh, key, canvas) {
    const previous = mesh.material.map;
    if (previous && previous.userData.key === key) return;
    const texture = textureFrom(canvas, anisotropy);
    texture.userData.key = key;
    mesh.material.map = texture;
    mesh.material.needsUpdate = true;
    if (previous) previous.dispose();
  }

  let current = null;      // the story view being read
  let currentStop = null;  // the stop view on the spread
  let turning = null;      // { started, from, to, forward }
  let opening = 0;
  let openStarted = 0;
  let requestToken = 0;

  function place(slot) {
    const sign = slot.wall === 'left' ? -1 : 1;
    facing.position.set(slot.position.x, config.table.height + 0.015, slot.position.z);
    // Turned a quarter turn toward the corridor: the visitor reads it from the
    // walking side, and the spread lies along the length of the table.
    facing.rotation.set(0, sign * Math.PI / 2, 0);
    open.position.set(0, 0, -pageHeight / 2);
    // A small lectern tilt, so the spread faces the visitor rather than the
    // ceiling. The near edge stays on the table; nothing floats.
    open.rotation.set(-0.30, 0, 0);
    leftPivot.position.set(0, 0.004, pageHeight / 2);
    rightPivot.position.set(0, 0.004, pageHeight / 2);
    leaf.position.set(0, 0.008, pageHeight / 2);
  }

  const sided = (page, gutter) => ({ ...page, gutter });

  function paintSpread(stop, image) {
    setPageTexture(leftPage, `left:${stop.key}`, paintPage(sided(stop.left, 'right'), image));
    setPageTexture(rightPage, `right:${stop.key}`, paintPage(sided(stop.right, 'left'), null));
  }

  /**
   * Show a stop. The reader already has the text; this is the picture catching
   * up with it. The latest request wins, and a skip of more than one stop is an
   * immediate change rather than a queue of turns.
   */
  function showStop(stop, { previous = null, immediate = false } = {}) {
    const token = ++requestToken;
    currentStop = stop;
    if (current) setBlock(stop.index, current.stopCount);
    const forward = previous ? stop.index > previous.index : true;
    const distance = previous ? Math.abs(stop.index - previous.index) : 0;
    const animate = !immediate && !reduceMotion.matches && previous &&
      distance > 0 && distance <= MAX_SIMULATED_SKIP;

    const image = stop.left.path ? assets.peek(stop.left.path) : null;
    if (stop.left.path && !image) {
      assets.loadImage(stop.left.path, { priority: 'high', token: null }).then((loaded) => {
        // A late image only lands if the visitor is still on the stop that
        // asked for it.
        if (loaded && token === requestToken && currentStop === stop) {
          paintSpread(stop, loaded);
          invalidate();
        }
      });
    }

    if (!animate) {
      paintSpread(stop, image);
      leaf.visible = false;
      turning = null;
      invalidate();
      return;
    }

    const previousImage = previous.left.path ? assets.peek(previous.left.path) : null;
    if (forward) {
      setPageTexture(leftPage, `left:${previous.key}`, paintPage(sided(previous.left, 'right'), previousImage));
      setPageTexture(rightPage, `right:${stop.key}`, paintPage(sided(stop.right, 'left'), null));
      setPageTexture(leafFront, `front:${previous.key}`, paintPage(sided(previous.right, 'left'), null));
      setPageTexture(leafBack, `back:${stop.key}`, paintPage(sided(stop.left, 'right'), image));
      turning = { started: performance.now(), from: 0, to: -Math.PI, stop };
    } else {
      setPageTexture(leftPage, `left:${stop.key}`, paintPage(sided(stop.left, 'right'), image));
      setPageTexture(rightPage, `right:${previous.key}`, paintPage(sided(previous.right, 'left'), null));
      setPageTexture(leafFront, `front:${stop.key}`, paintPage(sided(stop.right, 'left'), null));
      setPageTexture(leafBack, `back:${previous.key}`, paintPage(sided(previous.left, 'right'), previousImage));
      turning = { started: performance.now(), from: -Math.PI, to: 0, stop };
    }
    leaf.visible = true;
    leaf.rotation.z = turning.from;
    invalidate();
  }

  function bend(amount) {
    for (const [mesh, base] of [[leafFront, baseFront], [leafBack, baseBack]]) {
      const attribute = mesh.geometry.attributes.position;
      const array = attribute.array;
      for (let i = 0; i < array.length; i += 3) {
        const t = (base[i] + pageWidth / 2) / pageWidth;
        array[i + 2] = base[i + 2] + Math.sin(Math.PI * t) * amount;
      }
      attribute.needsUpdate = true;
    }
  }

  function openVolume(storyId, stop) {
    const slot = layout.bookSlotByStoryId.get(storyId);
    if (!slot) return;
    current = storyViews.get(storyId);
    place(slot);
    coverMaterial.color.set(current.eraColor);
    coverMaterial.color.multiplyScalar(0.55);
    // The other volumes on this table are pushed clear of the open spread
    // rather than taken away: they are still there to be chosen.
    for (const mesh of bookMeshes) {
      mesh.visible = mesh.userData.storyId !== storyId;
      if (mesh.userData.bayId !== slot.bayId) { mesh.position.z = mesh.userData.homeZ; continue; }
      const away = mesh.userData.homeZ >= slot.position.z ? 1 : -1;
      mesh.position.z = mesh.userData.homeZ + away * 0.24;
    }
    setBlock(stop.index, current.stopCount);
    facing.visible = true;
    leaf.visible = false;
    showStop(stop, { immediate: true });
    if (reduceMotion.matches) {
      opening = 0;
      leftPivot.rotation.z = 0;
      rightPivot.rotation.z = 0;
    } else {
      opening = 1;
      openStarted = performance.now();
      leftPivot.rotation.z = 0.45;
      rightPivot.rotation.z = -0.45;
    }
    invalidate();
  }

  function closeVolume() {
    current = null;
    currentStop = null;
    turning = null;
    opening = 0;
    facing.visible = false;
    leaf.visible = false;
    for (const mesh of bookMeshes) {
      mesh.visible = true;
      mesh.position.z = mesh.userData.homeZ;
    }
    invalidate();
  }

  function frame(now) {
    let busy = false;
    if (opening) {
      const k = Math.min(1, (now - openStarted) / OPEN_MS);
      const e = 1 - Math.pow(1 - k, 3);
      leftPivot.rotation.z = 0.45 * (1 - e);
      rightPivot.rotation.z = -0.45 * (1 - e);
      if (k >= 1) opening = 0; else busy = true;
      invalidate();
    }
    if (turning) {
      const k = Math.min(1, (now - turning.started) / TURN_MS);
      const e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      leaf.rotation.z = turning.from + (turning.to - turning.from) * e;
      bend(Math.sin(Math.PI * k) * 0.045);
      if (k >= 1) {
        // The spread settles to the stop the visitor actually asked for.
        const settled = turning.stop;
        turning = null;
        leaf.visible = false;
        bend(0);
        if (settled === currentStop) {
          paintSpread(settled, settled.left.path ? assets.peek(settled.left.path) : null);
        }
      } else busy = true;
      invalidate();
    }
    return busy;
  }

  /** Books are pickable; the tables and the room around them are not. */
  function pickables() {
    return bookMeshes.filter((mesh) => mesh.visible);
  }

  return {
    group,
    frame,
    openVolume,
    closeVolume,
    showStop,
    pickables,
    get openStoryId() { return current ? current.id : null; },
    get animating() { return !!turning || !!opening; },
    dispose() {
      for (const mesh of [leftPage, rightPage, leafFront, leafBack]) {
        mesh.material.map?.dispose();
        mesh.material.dispose();
        mesh.geometry.dispose();
      }
      for (const thing of disposables) thing.dispose?.();
      group.clear();
    }
  };
}
