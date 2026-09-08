// Woven — a timeline scaffold measured from the archive, with no fixed frame.
import * as THREE from 'three';
import { x, YEAR_MIN, YEAR_MAX } from './layout.js';

export function buildLoom(model) {
  const group = new THREE.Group();
  const points = [];
  const bottom = model.layout.bounds.minY - 0.5;
  for (let year = YEAR_MIN; year <= YEAR_MAX; year += 10) {
    points.push(x(year), 0.9, -0.12, x(year), bottom, -0.12);
  }
  for (const band of model.bands) {
    if (!band.count) continue;
    const y = band.top - band.height - 0.45;
    points.push(0, y, -0.12, x(YEAR_MAX), y, -0.12);
  }
  const grid = new THREE.BufferGeometry();
  grid.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
  const rules = new THREE.LineSegments(grid,
    new THREE.LineBasicMaterial({ color: 0x6b563c, transparent: true, opacity: 0.42 }));
  rules.name = 'timeline-rules';
  group.add(rules);

  // Each circular stitch marks a known founding year, including one-year titles.
  const dated = model.threads.filter((t) => !t.unknownFounding);
  const starts = new THREE.InstancedMesh(new THREE.SphereGeometry(0.10, 8, 6),
    new THREE.MeshBasicMaterial(), Math.max(1, dated.length));
  starts.count = dated.length;
  const matrix = new THREE.Matrix4();
  dated.forEach((t, i) => {
    matrix.makeTranslation(t.x0, t.y, 0.10);
    starts.setMatrixAt(i, matrix);
    starts.setColorAt(i, new THREE.Color(t.dye));
  });
  starts.name = 'founding-stitches';
  group.add(starts);
  return group;
}

export function buildLights() {
  const group = new THREE.Group();
  group.add(new THREE.HemisphereLight(0xf4f7ff, 0x142134, 1.2));
  const light = new THREE.DirectionalLight(0xffffff, 1.1);
  light.position.set(0.4, 0.8, 1);
  group.add(light);
  return group;
}
