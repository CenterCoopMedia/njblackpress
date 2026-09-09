// History hall — the framed sheets.
//
// Every publication has one frame at its own layout slot, all 136 of them, all
// the time. What changes is how much of a sheet is painted: the sheets near the
// visitor and the selected sheet carry a full painted face and a brass plate;
// the rest share one low detail paper material with an era accent and no type.
//
// Filtering never moves a sheet. A filter changes two things and nothing else:
// which sheets can be picked, and how brightly their paper is lit. The gallery
// the visitor learned stays where it was.

import * as THREE from 'three';
import {
  paintSheetFace, paintPlate, paintPlainPaper, textureFrom, textureBytes,
  FACE_SIZE, PLATE_SIZE
} from './paint.js';
import { SPACE_CONFIG } from './space.js';

// Painted faces per tier. A face is 512 by 704 RGBA8, about 1.83 MiB with its
// mip chain, so 24 faces hold about 44 MiB and 12 hold about 22 MiB. With the
// matching plates, the 16 decade markers, the 13 book covers, and the open
// volume's pages, the standard tier comes to roughly 80 MiB and the simplified
// tier to roughly 50 MiB, inside the 128 MiB and 64 MiB budgets. Painting all
// 136 faces would take about 249 MiB, which is why the pool exists.
export const FACE_POOL_SIZES = { standard: 24, simplified: 12 };
export const FACE_POOL_SIZE = FACE_POOL_SIZES.standard;

// A label plate, not a second slab: about the size of a gallery card under a
// frame. The required credit lives in the record panel either way.
const PLATE_WORLD = { width: 0.72, height: 0.14, drop: 0.07 };
// How many faces may be painted in one frame. A long jump repaints the whole
// pool, and doing that in one go would stall the visitor's input.
const PAINT_PER_FRAME = 2;

// How brightly a sheet's paper is lit. A sheet the filter excludes is pushed
// back, not put out: the hall has to stay readable as a room, and a visitor who
// filters must still see where the rest of the collection is.
const TONE = { match: 1, related: 1.16, dimmed: 0.55 };
// How much further away a sheet counts when the paint pool is handed out. A
// match is worth its real distance, a sheet the story names a little less, and a
// sheet the filter excludes two and a half times more — so a filtered-out sheet
// the visitor is standing in front of still carries its name, while paint goes
// to the matches first.
const PAINT_WEIGHT = { match: 1, related: 0.6, dimmed: 2.5 };
// How many referenced sheets can carry the story cue at once. No stop in the
// archive names more than a handful of publications.
const RELATED_MARKS = 8;

/** Instance colour is only read when the material has vertex colours, and the
 * attribute has to exist or the shader reads black. One white colour per vertex
 * makes the instance colour the only thing that tints the sheet. */
function withVertexColors(geometry) {
  const count = geometry.attributes.position.count;
  geometry.setAttribute('color', new THREE.BufferAttribute(new Float32Array(count * 3).fill(1), 3));
  return geometry;
}

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
  const paperGeometry = track(withVertexColors(new THREE.PlaneGeometry(paperWidth, paperHeight)));
  const papers = new THREE.InstancedMesh(
    paperGeometry,
    track(new THREE.MeshLambertMaterial({ map: paperTexture, vertexColors: true })),
    slots.length
  );
  papers.name = 'sheet-papers';

  const accents = new THREE.InstancedMesh(
    track(withVertexColors(new THREE.PlaneGeometry(paperWidth, 0.06))),
    track(new THREE.MeshBasicMaterial({ vertexColors: true })),
    slots.length
  );
  accents.name = 'sheet-accents';
  accents.userData.decorative = true;

  const blanks = new THREE.InstancedMesh(
    track(withVertexColors(new THREE.PlaneGeometry(PLATE_WORLD.width, PLATE_WORLD.height))),
    track(new THREE.MeshLambertMaterial({ color: '#8a7252', vertexColors: true })),
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
    papers.setColorAt(index, colour.setScalar(TONE.match));

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
    blanks.setColorAt(index, colour.setScalar(TONE.match));
  });
  frames.instanceMatrix.needsUpdate = true;
  papers.instanceMatrix.needsUpdate = true;
  accents.instanceMatrix.needsUpdate = true;
  if (accents.instanceColor) accents.instanceColor.needsUpdate = true;
  blanks.instanceMatrix.needsUpdate = true;
  group.add(frames, papers, accents, blanks);

  // The era colour each accent strip starts from, so a dimmed sheet can be
  // returned to its own colour rather than to white.
  const accentColours = slots.map((slot) => new THREE.Color(views.get(slot.publicationId).eraColor));

  // ---- the painted pool ---------------------------------------------------
  const faceGeometry = track(new THREE.PlaneGeometry(paperWidth, paperHeight));
  const plateGeometry = track(new THREE.PlaneGeometry(PLATE_WORLD.width, PLATE_WORLD.height));
  const pool = [];
  for (let i = 0; i < Math.min(FACE_POOL_SIZES.standard, slots.length); i++) {
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
  let poolLimit = Math.min(FACE_POOL_SIZES.standard, pool.length);
  let matches = null;       // null means no filter is applied
  let related = new Set();  // publications the open story stop names

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

  /** How brightly one slot's paper is lit, from the filter and the open story. */
  function toneFor(slot) {
    if (matches && !matches.has(slot.publicationId)) return TONE.dimmed;
    if (related.has(slot.publicationId)) return TONE.related;
    return TONE.match;
  }

  function paintEntry(entry) {
    const slot = slots[entry.slotIndex];
    if (!slot) return;
    const view = views.get(slot.publicationId);
    const image = view.wallPath ? assets.peek(view.wallPath) : null;
    if (view.wallPath && !image && !assets.hasFailed(view.wallPath)) {
      // The record design is drawn now and the copy is fetched alongside it, so
      // the sheet is never an empty image-shaped hole while an image loads.
      const token = options.generation ? options.generation() : null;
      assets.loadImage(view.wallPath, { priority: 'high', token }).then((loaded) => {
        // A late arrival only lands if this pool entry still holds this slot.
        if (entry.slotIndex >= 0 && slots[entry.slotIndex] === slot) {
          entry.painted = false;
          queue(entry);
          invalidate();
        }
      });
    }
    const unavailable = !!view.wallPath && !image && assets.hasFailed(view.wallPath);
    // A face is repainted when the fonts arrive and when a wall copy finishes
    // decoding, so the texture it replaces is released rather than left on the
    // GPU with nothing pointing at it.
    entry.faceMaterial.map?.dispose();
    entry.plateMaterial.map?.dispose();
    entry.faceMaterial.map = textureFrom(paintSheetFace(view, image, { unavailable }), anisotropy);
    entry.plateMaterial.map = textureFrom(paintPlate(view), anisotropy);
    entry.faceMaterial.color.setScalar(toneFor(slot));
    entry.plateMaterial.color.setScalar(toneFor(slot));
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
   * publications the open story names, then the nearest along the hall. A sheet
   * the filter excludes comes last, because paint is the scarce resource and a
   * match deserves it before a non-match does. Slots keep their places; only
   * the paint moves.
   */
  function updatePool(cameraZ, selectedId) {
    const wanted = [];
    const seen = new Set();
    const selectedSlot = selectedId == null ? null : layout.slotByPublicationId.get(selectedId);
    if (selectedSlot) { wanted.push(selectedSlot.index); seen.add(selectedSlot.index); }
    const ordered = slots
      .map((slot) => ({
        index: slot.index,
        score: Math.abs(slot.z - cameraZ) * (
          matches && !matches.has(slot.publicationId) ? PAINT_WEIGHT.dimmed
            : related.has(slot.publicationId) ? PAINT_WEIGHT.related : PAINT_WEIGHT.match)
      }))
      .sort((a, b) => a.score - b.score);
    for (const item of ordered) {
      if (wanted.length >= poolLimit) break;
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

  /** Write every sheet's tone from the current filter and story cue. */
  function applyTones() {
    for (const slot of slots) {
      const tone = toneFor(slot);
      papers.setColorAt(slot.index, colour.setScalar(tone));
      blanks.setColorAt(slot.index, colour.setScalar(tone));
      accents.setColorAt(slot.index, colour.copy(accentColours[slot.index]).multiplyScalar(tone));
    }
    if (papers.instanceColor) papers.instanceColor.needsUpdate = true;
    if (blanks.instanceColor) blanks.instanceColor.needsUpdate = true;
    if (accents.instanceColor) accents.instanceColor.needsUpdate = true;
    for (const [index, entry] of assigned) {
      const tone = toneFor(slots[index]);
      entry.faceMaterial.color.setScalar(tone);
      entry.plateMaterial.color.setScalar(tone);
    }
    invalidate();
  }

  // ---- highlights ---------------------------------------------------------
  // One outline geometry, shared by every marker: the source plane is disposed
  // as soon as its edges have been taken from it.
  const markerPlane = new THREE.PlaneGeometry(config.frame.width + 0.14, config.frame.height + 0.14);
  const markerGeometry = track(new THREE.EdgesGeometry(markerPlane));
  markerPlane.dispose();

  function marker(colourValue) {
    const line = new THREE.LineSegments(
      markerGeometry,
      track(new THREE.LineBasicMaterial({ color: colourValue }))
    );
    line.visible = false;
    line.userData.decorative = true;
    group.add(line);
    return line;
  }
  const hoverLine = marker('#f0854a');
  const selectedLine = marker('#e2662b');
  // The story cue: quiet brass edges on the sheets the current stop names. No
  // camera move, no lines through the room.
  const relatedLines = [];
  for (let i = 0; i < RELATED_MARKS; i += 1) relatedLines.push(marker('#a89179'));

  function markLine(line, publicationId) {
    const slot = publicationId == null ? null : layout.slotByPublicationId.get(publicationId);
    if (!slot) { line.visible = false; return; }
    const sign = slot.wall === 'left' ? -1 : 1;
    line.position.set(slot.x - sign * 0.02, slot.y, slot.z);
    line.quaternion.copy(quaternionFor(slot.wall));
    line.visible = true;
  }

  function setRelated(ids) {
    related = new Set(ids || []);
    const list = [...related].slice(0, RELATED_MARKS);
    relatedLines.forEach((line, i) => markLine(line, list[i] ?? null));
    applyTones();
  }

  // ---- picking ------------------------------------------------------------
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  /**
   * Only the sheets themselves are pickable. Walls, tables, frames, plates, and
   * decade markers are decorative and never take a click, and a sheet the
   * filter excludes is not an accidental target either.
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
    setRelated,
    /** @param {Set<number>|null} ids the publications the filters match, or null for all. */
    setMatches(ids) {
      matches = ids;
      applyTones();
    },
    /** The tier decides how many faces may be painted at once. */
    setPoolLimit(limit) {
      const next = Math.max(1, Math.min(pool.length, limit));
      if (next === poolLimit) return false;
      poolLimit = next;
      return true;
    },
    /** The wall copies the painted pool is using, for the working set. */
    workingPaths() {
      const paths = [];
      for (const [index] of assigned) {
        const view = views.get(slots[index].publicationId);
        if (view && view.wallPath) paths.push(view.wallPath);
      }
      return paths;
    },
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
    get poolLimit() { return poolLimit; },
    get relatedCount() { return related.size; },
    /** An estimate of what the painted pool holds, faces plus plates. */
    residentBytes() {
      const face = textureBytes(FACE_SIZE.width, FACE_SIZE.height);
      const plate = textureBytes(PLATE_SIZE.width, PLATE_SIZE.height);
      return assigned.size * (face + plate) + textureBytes(128, 176);
    },
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
