// History hall — the room itself: floor, walls, decade markers, reading tables,
// and light.
//
// Art direction, in one place so it can be reviewed as one decision: a dark
// walnut floor with a low contrast figure, pale plaster walls that fade
// deliberately into the dark above the frames, restrained brass, and no ceiling
// mesh. No fog, no glow, no vignette, no particles. The printed matter on the
// walls is the brightest thing in the room, and it should stay that way.

import * as THREE from 'three';
import { paintFloor, paintWall, paintMarker, paintEndWall, paintRunner, textureFrom, textureBytes, MARKER_SIZE, END_WALL_SIZE, RUNNER_SIZE } from './paint.js';

// Every colour and light value the room uses, taken from the site's tokens.
export const SPACE_CONFIG = {
  background: '#0b0806',
  floorTint: '#ffffff',
  wallTint: '#ffffff',
  tableTop: '#6b563c',
  tablePlinth: '#3b3122',
  frameWood: '#2b2318',
  hemisphereSky: '#f3eee2',
  hemisphereGround: '#2b2318',
  hemisphereIntensity: 2.2,
  keyLight: '#fff3df',
  keyIntensity: 1.7,
  fillLight: '#e8ddc6',
  fillIntensity: 0.55
};

export function buildSpace(layout, { anisotropy = 4, onChange = () => {} } = {}) {
  const config = layout.config;
  const group = new THREE.Group();
  group.name = 'hall-space';
  const disposables = [];
  const track = (thing) => { disposables.push(thing); return thing; };

  const length = layout.length;
  const halfWidth = config.wallX;

  // ---- floor -------------------------------------------------------------
  const floorTexture = track(textureFrom(paintFloor(), anisotropy));
  floorTexture.wrapS = THREE.RepeatWrapping;
  floorTexture.wrapT = THREE.RepeatWrapping;
  floorTexture.repeat.set(2, Math.max(1, Math.round(length / 3)));
  const floor = new THREE.Mesh(
    track(new THREE.PlaneGeometry(halfWidth * 2, length)),
    track(new THREE.MeshLambertMaterial({ map: floorTexture, color: SPACE_CONFIG.floorTint }))
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, 0, length / 2);
  floor.name = 'hall-floor';
  group.add(floor);

  // ---- walls -------------------------------------------------------------
  const wallTexture = track(textureFrom(paintWall(), 1));
  wallTexture.wrapS = THREE.RepeatWrapping;
  wallTexture.repeat.set(1, 1);
  const wallMaterial = track(new THREE.MeshLambertMaterial({ map: wallTexture, color: SPACE_CONFIG.wallTint }));
  for (const side of [-1, 1]) {
    const wall = new THREE.Mesh(track(new THREE.PlaneGeometry(length, config.ceilingHeight)), wallMaterial);
    wall.position.set(side * halfWidth, config.ceilingHeight / 2, length / 2);
    wall.rotation.y = side < 0 ? Math.PI / 2 : -Math.PI / 2;
    wall.name = `hall-wall-${side < 0 ? 'left' : 'right'}`;
    group.add(wall);
  }
  // The two ends close the room. Without them the visitor looking back at the
  // entrance, or ahead past the 2020s, sees an unexplained black void.
  for (const [z, facing] of [[0, 1], [length, -1]]) {
    const end = new THREE.Mesh(
      track(new THREE.PlaneGeometry(halfWidth * 2, config.ceilingHeight)),
      wallMaterial
    );
    end.position.set(0, config.ceilingHeight / 2, z);
    if (facing < 0) end.rotation.y = Math.PI;
    group.add(end);
  }

  // ---- the far wall ------------------------------------------------------
  // The archive's icon and name close the hall, so the walk ends somewhere.
  // The panel is framed like the sheets and hangs at the same eye line.
  const span = `${config.chronology.firstYear}\u2013${config.chronology.lastYear}`;
  const endCanvas = paintEndWall(null, span);
  const endTexture = track(textureFrom(endCanvas, anisotropy));
  const panelHeight = 2.8;
  const panelWidth = panelHeight * END_WALL_SIZE.width / END_WALL_SIZE.height;
  const endPanel = new THREE.Group();
  endPanel.name = 'hall-end-wall';
  const endFrame = new THREE.Mesh(
    track(new THREE.BoxGeometry(panelWidth + 0.16, panelHeight + 0.16, 0.08)),
    track(new THREE.MeshLambertMaterial({ color: SPACE_CONFIG.frameWood }))
  );
  endFrame.userData.decorative = true;
  const endFace = new THREE.Mesh(
    track(new THREE.PlaneGeometry(panelWidth, panelHeight)),
    track(new THREE.MeshLambertMaterial({ map: endTexture }))
  );
  endFace.position.z = 0.041;
  endFace.userData.decorative = true;
  endPanel.add(endFrame, endFace);
  endPanel.position.set(0, config.frame.centreHeight + 0.55, length - 0.05);
  endPanel.rotation.y = Math.PI;
  group.add(endPanel);
  const icon = new Image();
  icon.addEventListener('load', () => {
    const painted = paintEndWall(icon, span);
    endCanvas.getContext('2d').drawImage(painted, 0, 0);
    endTexture.needsUpdate = true;
    // The hall draws on demand, so ask for a frame or the panel waits for the
    // visitor's next move.
    onChange();
  }, { once: true });
  icon.src = 'njblackpress-icon.png';

  // ---- the runner ----------------------------------------------------------
  // A carpet runner down the middle of the corridor, from the entrance to the
  // far wall. It repeats every 2.4 metres and sits a few millimetres above the
  // floor so the two never flicker.
  const runnerSpec = config.runner;
  const runnerLength = length - runnerSpec.inset * 2;
  const runnerTexture = track(textureFrom(paintRunner(), anisotropy));
  runnerTexture.wrapT = THREE.RepeatWrapping;
  runnerTexture.repeat.set(1, Math.max(1, Math.round(runnerLength / 2.4)));
  const runner = new THREE.Mesh(
    track(new THREE.PlaneGeometry(runnerSpec.width, runnerLength)),
    track(new THREE.MeshLambertMaterial({ map: runnerTexture }))
  );
  runner.rotation.x = -Math.PI / 2;
  runner.position.set(0, 0.004, length / 2);
  runner.name = 'hall-runner';
  runner.userData.decorative = true;
  group.add(runner);

  // ---- furnishings on the bare wall ---------------------------------------
  // Benches, plinths with a tied bundle of newspapers, and brass sconces, from
  // the layout's own tested bounds. Each part is one instanced mesh, so the
  // whole set costs a handful of draw calls.
  const parts = new Map();
  const part = (name, geometry, material) => {
    if (!parts.has(name)) parts.set(name, { geometry, material, matrices: [] });
    return parts.get(name);
  };
  const walnut = track(new THREE.MeshLambertMaterial({ color: SPACE_CONFIG.frameWood }));
  const oak = track(new THREE.MeshLambertMaterial({ color: SPACE_CONFIG.tableTop }));
  const brass = track(new THREE.MeshLambertMaterial({ color: '#a89179' }));
  const paper = track(new THREE.MeshLambertMaterial({ color: '#f3eee2' }));
  const twine = track(new THREE.MeshLambertMaterial({ color: '#8f3a14' }));
  const glow = track(new THREE.MeshBasicMaterial({ color: '#ffe6bd' }));
  const unit = track(new THREE.BoxGeometry(1, 1, 1));
  const shadeGeometry = track(new THREE.CylinderGeometry(0.07, 0.11, 0.16, 16, 1, true));
  const matrix = new THREE.Matrix4();
  const place = (name, geometry, material, x, y, z, sx = 1, sy = 1, sz = 1, turn = 0) => {
    matrix.compose(
      new THREE.Vector3(x, y, z),
      new THREE.Quaternion().setFromEuler(new THREE.Euler(0, turn, 0)),
      new THREE.Vector3(sx, sy, sz)
    );
    part(name, geometry, material).matrices.push(matrix.clone());
  };
  for (const ornament of layout.ornaments || []) {
    const b = ornament.bounds;
    const sign = ornament.wall === 'left' ? -1 : 1;
    const cx = (b.minX + b.maxX) / 2;
    const cz = (b.minZ + b.maxZ) / 2;
    const reach = b.maxX - b.minX;
    const len = b.maxZ - b.minZ;
    if (ornament.kind === 'bench') {
      place('bench-seat', unit, oak, cx, b.maxY - 0.03, cz, reach, 0.06, len);
      for (const end of [-1, 1]) place('bench-leg', unit, walnut, cx, (b.maxY - 0.06) / 2, cz + end * (len / 2 - 0.08), reach - 0.06, b.maxY - 0.06, 0.07);
    } else if (ornament.kind === 'plinth') {
      const bodyTop = b.maxY - 0.22;
      place('plinth-body', unit, walnut, cx, bodyTop / 2, cz, reach - 0.04, bodyTop, len - 0.04);
      place('plinth-cap', unit, oak, cx, bodyTop + 0.02, cz, reach, 0.04, len);
      // A tied bundle of folded newspapers, each sheet a little askew.
      for (let i = 0; i < 5; i += 1) {
        place('paper', unit, paper, cx + sign * 0.01 * ((i % 2) - 0.5), bodyTop + 0.05 + i * 0.03, cz, reach * 0.62, 0.026, len * 0.72, (i - 2) * 0.05);
      }
      place('twine', unit, twine, cx, bodyTop + 0.11, cz, reach * 0.64, 0.16, 0.025);
    } else if (ornament.kind === 'sconce') {
      const wallFace = sign * config.wallX;
      place('sconce-plate', unit, brass, wallFace - sign * 0.01, b.minY + 0.12, cz, 0.02, 0.24, 0.12);
      place('sconce-arm', unit, brass, (wallFace + cx) / 2, b.minY + 0.18, cz, reach * 0.8, 0.025, 0.025);
      place('sconce-shade', shadeGeometry, glow, b.minX + reach / 2 - sign * reach * 0.25, b.maxY - 0.14, cz);
    }
  }
  const furnishings = new THREE.Group();
  furnishings.name = 'hall-furnishings';
  for (const [name, { geometry, material, matrices }] of parts) {
    const mesh = new THREE.InstancedMesh(geometry, material, matrices.length);
    matrices.forEach((m, i) => mesh.setMatrixAt(i, m));
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
    mesh.name = `furnishing-${name}`;
    mesh.userData.decorative = true;
    track({ dispose: () => mesh.dispose() });
    furnishings.add(mesh);
  }
  group.add(furnishings);

  // ---- decade markers ----------------------------------------------------
  // One blade sign per wall at the head of each section, from the layout's own
  // marker bounds, so nothing here can drift out of the tested layout. The
  // blade stands at a right angle to the wall on a bracket, and carries the
  // decade on both faces: one read walking in, one read walking back.
  const markerMeshes = [];
  const bladeEdge = track(new THREE.MeshLambertMaterial({ color: SPACE_CONFIG.frameWood }));
  const bracketGeometry = track(new THREE.BoxGeometry(1, 0.035, 0.035));
  for (const section of layout.sections) {
    const texture = track(textureFrom(paintMarker(section.label), anisotropy));
    const material = track(new THREE.MeshLambertMaterial({ map: texture }));
    section.markerBounds.forEach((box, index) => {
      const width = box.maxX - box.minX;
      const height = box.maxY - box.minY;
      const depth = box.maxZ - box.minZ;
      const centre = new THREE.Vector3((box.minX + box.maxX) / 2, (box.minY + box.maxY) / 2, (box.minZ + box.maxZ) / 2);
      const blade = new THREE.Group();
      blade.name = `marker-${section.id}`;
      blade.position.copy(centre);
      const body = new THREE.Mesh(track(new THREE.BoxGeometry(width, height, depth * 0.6)), bladeEdge);
      body.userData.decorative = true;
      blade.add(body);
      for (const facing of [-1, 1]) {
        const face = new THREE.Mesh(track(new THREE.PlaneGeometry(width, height)), material);
        face.position.z = facing * depth / 2;
        if (facing < 0) face.rotation.y = Math.PI;
        face.userData.decorative = true;
        blade.add(face);
        markerMeshes.push(face);
      }
      // A slim bracket from the wall carries the blade along its top edge.
      const side = index === 0 ? -1 : 1;
      const bracket = new THREE.Mesh(bracketGeometry, bladeEdge);
      bracket.scale.x = width;
      bracket.position.set(0, height / 2 + 0.03, 0);
      bracket.userData.decorative = true;
      blade.add(bracket);
      blade.userData.wall = side < 0 ? 'left' : 'right';
      group.add(blade);
    });
  }

  // ---- reading tables ----------------------------------------------------
  const topMaterial = track(new THREE.MeshLambertMaterial({ color: SPACE_CONFIG.tableTop }));
  const plinthMaterial = track(new THREE.MeshLambertMaterial({ color: SPACE_CONFIG.tablePlinth }));
  const topThickness = 0.08;
  for (const bay of layout.bays) {
    const width = bay.bounds.maxX - bay.bounds.minX;
    const depth = bay.bounds.maxZ - bay.bounds.minZ;
    const top = new THREE.Mesh(
      track(new THREE.BoxGeometry(width, topThickness, depth)),
      topMaterial
    );
    top.position.set(bay.centre.x, config.table.height - topThickness / 2, bay.centre.z);
    top.name = `table-${bay.id}`;
    top.userData.decorative = true;
    group.add(top);

    const plinth = new THREE.Mesh(
      track(new THREE.BoxGeometry(width * 0.72, config.table.height - topThickness, depth * 0.82)),
      plinthMaterial
    );
    plinth.position.set(bay.centre.x, (config.table.height - topThickness) / 2, bay.centre.z);
    plinth.userData.decorative = true;
    group.add(plinth);
  }

  // ---- light -------------------------------------------------------------
  // A hemisphere for the room and one directional key down the hall. A sheet is
  // readable at either wall without a light of its own; the optional travelling
  // fill below only softens the far end and is never needed to read anything.
  const hemisphere = new THREE.HemisphereLight(
    SPACE_CONFIG.hemisphereSky, SPACE_CONFIG.hemisphereGround, SPACE_CONFIG.hemisphereIntensity
  );
  group.add(hemisphere);
  const key = new THREE.DirectionalLight(SPACE_CONFIG.keyLight, SPACE_CONFIG.keyIntensity);
  key.position.set(1.2, 6, -3);
  key.target.position.set(0, 1.4, 6);
  group.add(key, key.target);
  const fill = new THREE.DirectionalLight(SPACE_CONFIG.fillLight, SPACE_CONFIG.fillIntensity);
  fill.position.set(-1.4, 3.4, 8);
  group.add(fill);

  return {
    group,
    /** The fill follows the visitor so the walls near them do not go flat. */
    follow(z) {
      key.position.z = z - 3;
      key.target.position.z = z + 6;
      key.target.updateMatrixWorld();
      fill.position.z = z + 8;
    },
    /**
     * The fill is the one optional light in the room. The simplified tier drops
     * it; nothing is unreadable without it, because the hemisphere and the key
     * light every sheet on both walls on their own.
     */
    setFill(enabled) {
      if (fill.visible === enabled) return false;
      fill.visible = enabled;
      return true;
    },
    get fillEnabled() { return fill.visible; },
    /** An estimate of what the room's own textures hold: floor, walls, markers. */
    residentBytes() {
      return textureBytes(256, 256) + textureBytes(8, 256)
        + layout.sections.length * textureBytes(MARKER_SIZE.width, MARKER_SIZE.height)
        + textureBytes(END_WALL_SIZE.width, END_WALL_SIZE.height)
        + textureBytes(RUNNER_SIZE.width, RUNNER_SIZE.height);
    },
    markerMeshes,
    dispose() {
      for (const thing of disposables) thing.dispose?.();
      group.clear();
    }
  };
}
