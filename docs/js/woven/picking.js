// Woven — analytic thread picking and instanced knot raycasting.
// The cloth is never raycast: 50k thin ribbon triangles give a bad hit rate.

import * as THREE from 'three';
import { YEAR_MIN, X_PER_YEAR } from './layout.js';

const CLOTH_PLANE = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
const raycaster = new THREE.Raycaster();
const ndc = new THREE.Vector2();
const hit = new THREE.Vector3();

export function createPicker(model, camera, knots) {
  return function pick(clientX, clientY, rect, touch) {
    ndc.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    ndc.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(ndc, camera);

    // Knots take priority when both hit.
    const knotHits = raycaster.intersectObjects(knots.meshes, false);
    if (knotHits.length) {
      const h = knotHits[0];
      const k = knots.lookup(h.object, h.instanceId);
      if (k) return { kind: 'knot', knot: k };
    }

    if (!raycaster.ray.intersectPlane(CLOTH_PLANE, hit)) return null;
    const year = YEAR_MIN + hit.x / X_PER_YEAR;
    const t = model.layout.slotAtY(hit.y);
    if (!t) return null;
    const tol = (touch ? 0.06 : 0.035) + t.width / 2;
    if (Math.abs(hit.y - t.y) > tol) return null;
    if (t.unknownFounding) {
      if (hit.x < 3.5 || hit.x > 62) return null;
      return { kind: 'thread', thread: t, year: null };
    }
    const endX = t.endState === 'still' ? 78.5 : t.x1;
    if (hit.x < t.x0 - 0.25 || hit.x > endX + 0.25) return null;
    return { kind: 'thread', thread: t, year };
  };
}
