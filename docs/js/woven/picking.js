// Woven — analytic thread picking and instanced knot raycasting.
// The cloth is never raycast: 50k thin ribbon triangles give a bad hit rate.

import * as THREE from 'three';
import { YEAR_MIN, X_PER_YEAR } from './layout.js';

const CLOTH_PLANE = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
const raycaster = new THREE.Raycaster();
const ndc = new THREE.Vector2();
const hit = new THREE.Vector3();

// A thread is a fraction of a world unit thick, which on a phone is a target one
// or two pixels tall. The hit slab is therefore sized in screen pixels and
// converted to world units at the camera's current distance: a fingertip inside
// this many pixels of a thread picks it. A mouse gets a smaller, sharper slab.
const COARSE_PX = 24;
const FINE_PX = 9;

export function createPicker(model, camera, knots, controls) {
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
    const nearest = model.layout.slotAtY(hit.y);
    if (!nearest) return null;

    const dist = controls
      ? camera.position.distanceTo(controls.target)
      : Math.abs(camera.position.z);
    const worldPerPx = (2 * Math.tan((camera.fov * Math.PI) / 360) * dist) / Math.max(1, rect.height);
    const slabPx = touch ? COARSE_PX : FINE_PX;
    const tol = Math.max((touch ? 0.06 : 0.035) + nearest.width / 2, slabPx * worldPerPx);
    // The same slab is given to the ends of a thread, so a tap just past the last
    // year still lands on the title it was aimed at.
    const padX = Math.max(0.25, slabPx * worldPerPx);

    // The nearest row is often one that stopped publishing before the year under
    // the finger, and there is no thread drawn there to hit. Rather than return
    // nothing, walk outward through the rows inside the slab and take the closest
    // one that is actually drawn at this year. This is what turns four taps into
    // one on a phone, where the rows can be four pixels apart.
    const slots = model.layout.slots;
    let best = null;
    let bestD = Infinity;

    const consider = (t) => {
      const dy = Math.abs(hit.y - t.y);
      if (dy >= bestD) return;
      if (t.unknownFounding) {
        if (hit.x < 3.5 - padX || hit.x > 62 + padX) return;
      } else {
        const endX = t.endState === 'still' ? 78.5 : t.x1;
        if (hit.x < t.x0 - padX || hit.x > endX + padX) return;
      }
      best = t;
      bestD = dy;
    };

    // The slot table runs top to bottom, so each direction can stop as soon as it
    // leaves the slab.
    consider(nearest);
    for (let i = nearest.globalIndex - 1; i >= 0; i--) {
      if (Math.abs(hit.y - slots[i].y) > tol) break;
      consider(slots[i]);
    }
    for (let i = nearest.globalIndex + 1; i < slots.length; i++) {
      if (Math.abs(hit.y - slots[i].y) > tol) break;
      consider(slots[i]);
    }
    if (!best) return null;
    return { kind: 'thread', thread: best, year: best.unknownFounding ? null : year };
  };
}
