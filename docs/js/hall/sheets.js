// History hall — the framed sheets.
//
// Every publication has one frame at its own layout slot, all 136 of them, all
// the time. What changes is how much of a sheet is painted: the sheets near the
// visitor and the selected sheet carry a full painted face and a brass plate;
// the rest share one low detail paper material with an era accent and no type.
//

import * as THREE from 'three';
import { paintSheetFace, paintPlate, paintPlainPaper, textureFrom } from './paint.js';
import { SPACE_CONFIG } from './space.js';

// Pool size: 24 painted faces. A face is 512 by 704 RGBA8, about 1.83 MiB with
// its mip chain, so the faces hold about 44 MiB. With 24 plates (8 MiB), the 16
// decade markers (11 MiB), the 13 book covers (6 MiB), and the open volume's
// pages and clipping (about 11 MiB) the hall's own resident textures come to
// roughly 80 MiB, inside the 128 MiB standard budget. Painting all 136 faces
// would take about 249 MiB, which is why the pool exists.
export const FACE_POOL_SIZE = 24;

// A label plate, not a second slab: about the size of a gallery card under a
// frame. The required credit lives in the record panel either way.
const PLATE_WORLD = { width: 0.72, height: 0.14, drop: 0.07 };
// How many faces may be painted in one frame. A long jump repaints the whole
// pool, and doing that in one go would stall the visitor's input.
const PAINT_PER_FRAME = 2;

export function buildSheets(layout, views, assets, options = {}) {
  const config = layout.config;
  const anisotropy = options.anisotropy || 4;
  const invalidate = options.invalidate || (() => {});
  const group = new THREE.Group();
  group.name = 'hall-sheets';
  const disposables = [];
  const track = (thing) => { disposables.push(thing); return thing; };
  const slots = layout.slots;
  const dummy = new THREE.Object3D();
  const colour = new THREE.Color();

  const quaternionFor = (wall) => {
    const euler = new THREE.Euler(0, wall === 'left' ? Math.PI / 2 : -Math.PI / 2, 0);
    return new THREE.Quaternion().setFromEuler(euler);
  };

  // ---- the parts every sheet has -----------------------------------------
  const frameGeometry = track(new THREE.BoxGeometry(config.frame.depth * 0.5, config.frame.height + 0.10, config.frame.width + 0.10));
  const frames = new THREE.InstancedMesh(
    frameGeometry,
    track(new THREE.MeshLambertMaterial({ color: SPACE_CONFIG.frameWood })),
    slots.length
  );
  frames.name = 'sheet-frames';
  frames.userData.decorative = true;

  const paperWidth = config.frame.width - 0.08;
  const paperHeight = config.frame.height - 0.08;
  const paperTexture = track(textureFrom(paintPlainPaper(), 2));
  const paperGeometry = track(new THREE.PlaneGeometry(paperWidth, paperHeight));
  const papers = new THREE.InstancedMesh(
    paperGeometry,
    track(new THREE.MeshLambertMaterial({ map: paperTexture })),
    slots.length
  );
  papers.name = 'sheet-papers';

  const accents = new THREE.InstancedMesh(
    track(new THREE.PlaneGeometry(paperWidth, 0.06)),
    track(new THREE.MeshBasicMaterial({})),
    slots.length
  );
  accents.name = 'sheet-accents';
  accents.userData.decorative = true;

  const blanks = new THREE.InstancedMesh(
    track(new THREE.PlaneGeometry(PLATE_WORLD.width, PLATE_WORLD.height)),
    track(new THREE.MeshLambertMaterial({ color: '#8a7252' })),
    slots.length
  );
  blanks.name = 'sheet-plates';
  blanks.userData.decorative = true;

  slots.forEach((slot, index) => {
    const sign = slot.wall === 'left' ? -1 : 1;
    const wallFace = sign * config.wallX;
    const quaternion = quaternionFor(slot.wall);
    const scale = new THREE.Vector3(1, 1, 1);

    dummy.position.set(wallFace - sign * config.frame.depth * 0.25, slot.y, slot.z);
    dummy.quaternion.identity();
    dummy.scale.copy(scale);
    dummy.updateMatrix();
    frames.setMatrixAt(index, dummy.matrix);

    dummy.position.set(slot.x, slot.y, slot.z);
    dummy.quaternion.copy(quaternion);
    dummy.updateMatrix();
    papers.setMatrixAt(index, dummy.matrix);

    dummy.position.set(
      slot.x - sign * 0.004, slot.y - paperHeight / 2 + 0.05, slot.z
    );
    dummy.updateMatrix();
    accents.setMatrixAt(index, dummy.matrix);
    accents.setColorAt(index, colour.set(views.get(slot.publicationId).eraColor));

    dummy.position.set(
      slot.x, slot.y - config.frame.height / 2 - PLATE_WORLD.drop, slot.z
    );
    dummy.updateMatrix();
    blanks.setMatrixAt(index, dummy.matrix);
  });
  frames.instanceMatrix.needsUpdate = true;
  papers.instanceMatrix.needsUpdate = true;
  accents.instanceMatrix.needsUpdate = true;
  if (accents.instanceColor) accents.instanceColor.needsUpdate = true;
  blanks.instanceMatrix.needsUpdate = true;
  group.add(frames, papers, accents, blanks);

  // ---- the painted pool ---------------------------------------------------
  const faceGeometry = track(new THREE.PlaneGeometry(paperWidth, paperHeight));
  const plateGeometry = track(new THREE.PlaneGeometry(PLATE_WORLD.width, PLATE_WORLD.height));
  const pool = [];
  for (let i = 0; i < Math.min(FACE_POOL_SIZE, slots.length); i++) {
    const faceMaterial = new THREE.MeshBasicMaterial({ transparent: false });
    const plateMaterial = new THREE.MeshBasicMaterial({ transparent: false });
    const face = new THREE.Mesh(faceGeometry, faceMaterial);
    const plate = new THREE.Mesh(plateGeometry, plateMaterial);
    face.visible = false;
    plate.visible = false;
    face.userData.decorative = true;
    plate.userData.decorative = true;
    group.add(face, plate);
    pool.push({ face, plate, faceMaterial, plateMaterial, slotIndex: -1, painted: false });
  }
  const paintQueue = [];
  let assigned = new Map(); // slot index -> pool entry

  function place(entry, slot) {
    const sign = slot.wall === 'left' ? -1 : 1;
    const quaternion = quaternionFor(slot.wall);
    entry.face.position.set(slot.x - sign * 0.008, slot.y, slot.z);
    entry.face.quaternion.copy(quaternion);
    entry.plate.position.set(
      slot.x - sign * 0.008, slot.y - config.frame.height / 2 - PLATE_WORLD.drop, slot.z
    );
    entry.plate.quaternion.copy(quaternion);
  }

  function clearTextures(entry) {
    if (entry.faceMaterial.map) { entry.faceMaterial.map.dispose(); entry.faceMaterial.map = null; }
    if (entry.plateMaterial.map) { entry.plateMaterial.map.dispose(); entry.plateMaterial.map = null; }
    entry.face.visible = false;
    entry.plate.visible = false;
    entry.painted = false;
  }

  function paintEntry(entry) {
    const slot = slots[entry.slotIndex];
    if (!slot) return;
    const view = views.get(slot.publicationId);
    const image = view.wallPath ? assets.peek(view.wallPath) : null;
    if (view.wallPath && !image) {
      // The record design is drawn now and the copy is fetched alongside it, so
      // the sheet is never an empty image-shaped hole while an image loads.
      assets.loadImage(view.wallPath, { priority: 'high', token: null }).then((loaded) => {
        if (loaded && entry.slotIndex >= 0 && slots[entry.slotIndex] === slot) {
          entry.painted = false;
          queue(entry);
        }
      });
    }
    entry.faceMaterial.map = textureFrom(paintSheetFace(view, image), anisotropy);
    entry.plateMaterial.map = textureFrom(paintPlate(view), anisotropy);
    entry.faceMaterial.needsUpdate = true;
    entry.plateMaterial.needsUpdate = true;
    entry.face.visible = true;
    entry.plate.visible = true;
    entry.painted = true;
    invalidate();
  }

  function queue(entry) {
    if (!paintQueue.includes(entry)) paintQueue.push(entry);
  }

  /** Paint a little of the backlog. Called once per drawn frame. */
  function work() {
    let painted = 0;
    while (paintQueue.length && painted < PAINT_PER_FRAME) {
      const entry = paintQueue.shift();
      if (entry.slotIndex < 0 || entry.painted) continue;
      paintEntry(entry);
      painted++;
    }
    return paintQueue.length > 0;
  }

  /**
   * Decide which sheets carry a painted face: the selected one first, then the
   * nearest along the hall. Slots keep their places; only the paint moves.
   */
  function updatePool(cameraZ, selectedId) {
    const wanted = [];
    const seen = new Set();
    const selectedSlot = selectedId == null ? null : layout.slotByPublicationId.get(selectedId);
    if (selectedSlot) { wanted.push(selectedSlot.index); seen.add(selectedSlot.index); }
    const ordered = slots
      .map((slot) => ({ index: slot.index, distance: Math.abs(slot.z - cameraZ) }))
      .sort((a, b) => a.distance - b.distance);
    for (const item of ordered) {
      if (wanted.length >= pool.length) break;
      if (seen.has(item.index)) continue;
      wanted.push(item.index);
      seen.add(item.index);
    }
    const keep = new Map();
    const free = [];
    for (const entry of pool) {
      if (entry.slotIndex >= 0 && seen.has(entry.slotIndex)) keep.set(entry.slotIndex, entry);
      else { clearTextures(entry); entry.slotIndex = -1; free.push(entry); }
    }
    assigned = keep;
    for (const index of wanted) {
      if (keep.has(index)) continue;
      const entry = free.pop();
      if (!entry) break;
      entry.slotIndex = index;
      place(entry, slots[index]);
      keep.set(index, entry);
      queue(entry);
    }
  }

  // ---- highlights ---------------------------------------------------------
  function marker(colourValue) {
    const line = new THREE.LineSegments(
      track(new THREE.EdgesGeometry(new THREE.PlaneGeometry(config.frame.width + 0.14, config.frame.height + 0.14))),
      track(new THREE.LineBasicMaterial({ color: colourValue }))
    );
    line.visible = false;
    line.userData.decorative = true;
    group.add(line);
    return line;
  }
  const hoverLine = marker('#f0854a');
  const selectedLine = marker('#e2662b');

  function markLine(line, publicationId) {
    const slot = publicationId == null ? null : layout.slotByPublicationId.get(publicationId);
    if (!slot) { line.visible = false; return; }
    const sign = slot.wall === 'left' ? -1 : 1;
    line.position.set(slot.x - sign * 0.02, slot.y, slot.z);
    line.quaternion.copy(quaternionFor(slot.wall));
    line.visible = true;
  }

  // ---- picking ------------------------------------------------------------
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let matches = null;

  /**
   * Only the sheets themselves are pickable. Walls, tables, frames, plates, and
   * decade markers are decorative and never take a click.
   */
  function pick(x, y, rect, camera) {
    pointer.set((x / rect.width) * 2 - 1, -(y / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObject(papers, false);
    for (const hit of hits) {
      const slot = slots[hit.instanceId];
      if (!slot) continue;
      if (matches && !matches.has(slot.publicationId)) continue;
      // The distance goes back with the hit so the caller can tell a sheet from
      // a volume that happens to lie along the same ray.
      return { publicationId: slot.publicationId, distance: hit.distance };
    }
    return null;
  }

  return {
    group,
    pick,
    work,
    updatePool,
    setMatches(ids) { matches = ids; },
    /** Repaint every face in the pool, for instance once the fonts arrive. */
    repaint() {
      for (const entry of pool) {
        if (entry.slotIndex < 0) continue;
        entry.painted = false;
        queue(entry);
      }
    },
    setHover(id) { markLine(hoverLine, id); },
    setSelected(id) { markLine(selectedLine, id); },
    get pending() { return paintQueue.length; },
    get paintedCount() { return assigned.size; },
    dispose() {
      for (const entry of pool) clearTextures(entry);
      for (const thing of disposables) thing.dispose?.();
      frames.dispose();
      papers.dispose();
      accents.dispose();
      blanks.dispose();
      group.clear();
    }
  };
}
