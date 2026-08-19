// Woven — event knots. Shape carries confidence, not colour.

import * as THREE from 'three';

const STAIN = new THREE.Color('#e2662b');
const LINEN_300 = new THREE.Color('#cdc4b1');
const WALNUT_700 = new THREE.Color('#2b2318');

export function buildKnots(model) {
  const high = model.knots.filter((k) => k.confidence !== 'medium');
  const medium = model.knots.filter((k) => k.confidence === 'medium');

  const meshHigh = make(new THREE.TorusGeometry(0.085, 0.038, 6, 12), high, STAIN, 'knots-high');
  const meshMedium = make(new THREE.TorusGeometry(0.085, 0.030, 6, 12, 4.6), medium, LINEN_300, 'knots-medium');

  return {
    meshes: [meshHigh, meshMedium],
    high, medium,
    lookup(mesh, instanceId) {
      return mesh.name === 'knots-high' ? high[instanceId] : medium[instanceId];
    },
    reset() {
      applyAll(meshHigh, high, STAIN, 1);
      applyAll(meshMedium, medium, LINEN_300, 1);
    },
    setTour(activeIds, activeEventId) {
      applyTour(meshHigh, high, STAIN, activeIds, activeEventId);
      applyTour(meshMedium, medium, LINEN_300, activeIds, activeEventId);
    }
  };
}

function make(geo, list, colour, name) {
  const mat = new THREE.MeshLambertMaterial({ color: 0xffffff });
  const mesh = new THREE.InstancedMesh(geo, mat, Math.max(1, list.length));
  mesh.name = name;
  mesh.count = list.length;
  mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(Math.max(1, list.length) * 3), 3);
  applyAll(mesh, list, colour, 1);
  mesh.frustumCulled = false;
  return mesh;
}

const m4 = new THREE.Matrix4();
const q = new THREE.Quaternion();
const e = new THREE.Euler();
const v = new THREE.Vector3();
const s = new THREE.Vector3();

function place(mesh, i, k, scale) {
  // Torus axis along X so the knot reads as a bead threaded onto the ribbon.
  e.set(0, Math.PI / 2, k.roll);
  q.setFromEuler(e);
  v.set(k.x, k.y, 0);
  s.set(scale, scale, scale);
  m4.compose(v, q, s);
  mesh.setMatrixAt(i, m4);
}

function applyAll(mesh, list, colour, scale) {
  list.forEach((k, i) => {
    place(mesh, i, k, scale);
    mesh.instanceColor.setXYZ(i, colour.r, colour.g, colour.b);
  });
  mesh.instanceMatrix.needsUpdate = true;
  mesh.instanceColor.needsUpdate = true;
}

function applyTour(mesh, list, colour, activeIds, activeEventId) {
  list.forEach((k, i) => {
    const inTour = activeIds.has(k.eventId);
    const scale = k.eventId === activeEventId ? 1.35 : inTour ? 1.0 : 0.6;
    place(mesh, i, k, scale);
    const c = inTour ? colour : WALNUT_700;
    mesh.instanceColor.setXYZ(i, c.r, c.g, c.b);
  });
  mesh.instanceMatrix.needsUpdate = true;
  mesh.instanceColor.needsUpdate = true;
}
