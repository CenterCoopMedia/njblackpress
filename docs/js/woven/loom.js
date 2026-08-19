// Woven — the loom frame and the lights. Wood is structure, nothing else.

import * as THREE from 'three';

const OAK_500 = 0x6b563c;
const OAK_400 = 0x8a7252;

// Local merge, so the only vendored addon is OrbitControls.
// All parts carry position and normal after toNonIndexed().
function mergeParts(parts) {
  const flat = parts.map((g) => (g.index ? g.toNonIndexed() : g));
  let n = 0;
  for (const g of flat) n += g.attributes.position.count;
  const pos = new Float32Array(n * 3);
  const nor = new Float32Array(n * 3);
  let o = 0;
  for (const g of flat) {
    pos.set(g.attributes.position.array, o * 3);
    nor.set(g.attributes.normal.array, o * 3);
    o += g.attributes.position.count;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  out.computeBoundingSphere();
  return out;
}

function placed(geo, x, y, z, rotZ) {
  const g = geo.clone();
  if (rotZ) g.rotateZ(rotZ);
  g.translate(x, y, z);
  return g;
}

export function buildLoom(model) {
  const group = new THREE.Group();
  const frameParts = [
    placed(new THREE.BoxGeometry(1.2, 31, 1.0), -2.5, -14.3, 0),
    placed(new THREE.BoxGeometry(1.2, 31, 1.0), 75.5, -14.3, 0),
    placed(new THREE.CylinderGeometry(0.55, 0.55, 79, 12), 36.5, 0.9, 0, Math.PI / 2),
    placed(new THREE.CylinderGeometry(0.70, 0.70, 79, 12), 36.5, -28.6, 0, Math.PI / 2),
    placed(new THREE.BoxGeometry(79, 0.28, 0.28), 36.5, -29.9, 0.9)
  ];
  const frame = new THREE.Mesh(
    mergeParts(frameParts),
    new THREE.MeshLambertMaterial({ color: OAK_400 })
  );
  frame.name = 'loom-frame';
  group.add(frame);

  const ruleParts = [];
  for (const band of model.bands) {
    if (!band.count) continue;
    ruleParts.push(placed(new THREE.BoxGeometry(76, 0.05, 0.06), 36.5, band.top - band.height - 0.35, 0));
  }
  if (ruleParts.length) {
    const rules = new THREE.Mesh(
      mergeParts(ruleParts),
      new THREE.MeshLambertMaterial({ color: OAK_500, transparent: true, opacity: 0.5 })
    );
    rules.name = 'band-rules';
    group.add(rules);
  }
  return group;
}

export function buildLights() {
  const g = new THREE.Group();
  g.add(new THREE.HemisphereLight(0xa89179, 0x0b0806, 0.55));
  const dir = new THREE.DirectionalLight(0xf3eee2, 0.75);
  dir.position.set(0.4, 0.8, 1.0).normalize();
  g.add(dir);
  return g;
}
