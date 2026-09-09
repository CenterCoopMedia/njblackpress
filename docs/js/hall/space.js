// History hall — the room itself: floor, walls, decade markers, reading tables,
// and light.
//
// Art direction, in one place so it can be reviewed as one decision: a dark
// walnut floor with a low contrast figure, pale plaster walls that fade
// deliberately into the dark above the frames, restrained brass, and no ceiling
// mesh. No fog, no glow, no vignette, no particles. The printed matter on the
// walls is the brightest thing in the room, and it should stay that way.

import * as THREE from 'three';
import { paintFloor, paintWall, paintMarker, textureFrom } from './paint.js';

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

export function buildSpace(layout, { anisotropy = 4 } = {}) {
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

  // ---- decade markers ----------------------------------------------------
  // One painted plate per wall at the head of each section, from the layout's
  // own marker bounds, so nothing here can drift out of the tested layout.
  const markerMeshes = [];
  for (const section of layout.sections) {
    const texture = track(textureFrom(paintMarker(section.label), anisotropy));
    const material = track(new THREE.MeshLambertMaterial({ map: texture }));
    section.markerBounds.forEach((box, index) => {
      const side = index === 0 ? -1 : 1;
      const plate = new THREE.Mesh(
        track(new THREE.PlaneGeometry(box.maxZ - box.minZ, box.maxY - box.minY)),
        material
      );
      plate.position.set(
        side * (halfWidth - 0.02),
        (box.minY + box.maxY) / 2,
        (box.minZ + box.maxZ) / 2
      );
      plate.rotation.y = side < 0 ? Math.PI / 2 : -Math.PI / 2;
      plate.name = `marker-${section.id}`;
      plate.userData.decorative = true;
      group.add(plate);
      markerMeshes.push(plate);
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
    markerMeshes,
    dispose() {
      for (const thing of disposables) thing.dispose?.();
      group.clear();
    }
  };
}
