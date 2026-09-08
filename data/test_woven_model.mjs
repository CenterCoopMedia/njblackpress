// Behavioral checks against the real archive and the actual drawing geometry.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { registerHooks } from 'node:module';

const root = new URL('../', import.meta.url);
registerHooks({
  resolve(specifier, context, next) {
    if (specifier === 'three') return {
      url: new URL('docs/vendor/three-0.171.0/three.module.min.js', root).href,
      shortCircuit: true
    };
    return next(specifier, context);
  }
});
const documents = new Map();
for (const name of ['publications', 'events', 'stories', 'clippings']) {
  documents.set(`data/${name}.json`, JSON.parse(await readFile(new URL(`docs/data/${name}.json`, root))));
}
globalThis.fetch = async (url) => ({ ok: true, json: async () => documents.get(url) });
const { loadModel } = await import('../docs/js/woven/data.js');
const { buildWeft, buildWarp, createStateTexture, createClothMaterial, weaveUniform } = await import('../docs/js/woven/cloth.js');
const { buildLoom } = await import('../docs/js/woven/loom.js');
const { createFlatRenderer } = await import('../docs/js/woven/flat-renderer.js');
const THREE = await import('three');
const model = await loadModel();
const source = documents.get('data/publications.json').publications;
assert.equal(model.counts.total, source.length);
assert.equal(model.counts.stillPublishing, source.filter((p) => p.isActive).length);
assert.equal(new Set(model.layout.slots.map((t) => t.y)).size, source.length);
assert.equal(model.counts.ceased + model.counts.stillPublishing + model.counts.unknownEnd, source.length);
for (const t of model.threads) {
  const p = source.find((item) => item.id === t.id);
  assert.equal(t.yearFounded, p.yearFounded);
  assert.equal(t.yearCeased, p.yearCeased);
  assert.equal(t.endState === 'still', p.isActive);
  assert.deepEqual(t.evidence, p.evidence);
}
const geometry = buildWeft(model);
const represented = new Set();
const looseEnds = new Set();
for (const geo of Object.values(geometry)) {
  assert.ok([...geo.attributes.position.array].every(Number.isFinite));
  for (const [i, index] of geo.attributes.aThreadIndex.array.entries()) {
    represented.add(index);
    if (geo.attributes.position.array[i * 3] > 74.5) looseEnds.add(index);
  }
}
for (const t of model.threads) assert.ok(represented.has(t.threadIndex), `${t.name} must produce a visible ribbon`);
for (const t of model.threads) assert.equal(looseEnds.has(t.threadIndex), t.endState === 'still', `${t.name}: timeline loose ends must match active status`);
const warp = buildWarp(model, 4, 4);
assert.ok(Math.min(...warp.attributes.position.array.filter((_, i) => i % 3 === 1)) < model.layout.bounds.minY);
assert.equal(buildLoom(model).getObjectByName('founding-stitches').count, source.filter((p) => p.yearFounded != null).length);

// Render the real data through the flat renderer; fail on invalid coordinates.
let segments = 0;
let loadingFrames = 0;
let drawnXs = [];
const ctx = new Proxy({}, { get: (_, key) => (...args) => {
  if (key === 'lineTo') drawnXs.push(args[0]);
  if (key === 'strokeRect') { assert.ok(args.every(Number.isFinite)); loadingFrames++; }
  if (['moveTo', 'lineTo', 'arc', 'fillRect'].includes(key)) {
    assert.ok(args.every(Number.isFinite), `${key} has invalid coordinates`);
    segments++;
  }
}});
const canvas = { getContext: () => ctx };
const renderer = createFlatRenderer(canvas, model);
renderer.setPixelRatio(1.5);
renderer.setSize(1024, 700);
const camera = new THREE.PerspectiveCamera(45, 1024 / 700, 0.5, 400);
camera.position.set(36.5, -19, 100);
const scene = new THREE.Scene();
for (const [name, geo] of Object.entries(geometry)) {
  const mesh = new THREE.Mesh(geo, createClothMaterial(createStateTexture(source.length)));
  mesh.name = `weft-${name}`;
  scene.add(mesh);
}
weaveUniform.value = 1;
renderer.render(scene, camera);
assert.ok(segments > source.length, 'The flat timeline must draw the publication spans');
assert.equal(canvas.width, 1536);
const placeholder = new THREE.Mesh(new THREE.PlaneGeometry(10, 15),
  new THREE.MeshBasicMaterial({ color: 0x2b2318, opacity: 0.55 }));
placeholder.position.set(36.5, -19, 3);
scene.add(placeholder);
renderer.render(scene, camera);
assert.equal(loadingFrames, 1, 'A pending evidence image must show its loading frame');
placeholder.visible = false;
renderer.render(scene, camera);
assert.equal(loadingFrames, 1, 'Hidden loading frames must not draw');

// The flat fallback must retain the same active cue for undated records.
const flatScale = 700 / (2 * Math.tan(camera.fov * Math.PI / 360) * camera.position.z);
const timelineEdge = 512 + (73 - camera.position.x) * flatScale;
for (const t of model.threads.filter((thread) => thread.unknownFounding)) {
  const oneTitle = createFlatRenderer(canvas, { ...model, order: [t], knots: [] });
  oneTitle.setSize(1024, 700);
  camera.position.y = t.y;
  drawnXs = [];
  oneTitle.render(scene, camera);
  assert.equal(drawnXs.some((xx) => xx > timelineEdge), t.endState === 'still', `${t.name}: flat arrows must match active status`);
}

// Missing dates and rights are separate questions. Exercise cases absent today.
documents.set('data/publications.json', { publications: [
  { id: 1, name: 'Unknown ending', yearFounded: 1900, yearCeased: null, isActive: false, evidence: [{rightsStatus:'metadata_only'}] },
  { id: 2, name: 'Active', yearFounded: 2000, yearCeased: 2005, isActive: true, evidence: [] },
  { id: 3, name: 'Single year', yearFounded: 1940, yearCeased: 1940, isActive: false, evidence: [{rightsStatus:'publishable'}] },
  { id: 4, name: 'Undated', yearFounded: null, yearCeased: null, isActive: false, evidence: [] }
] });
for (const name of ['events', 'stories', 'clippings']) documents.set(`data/${name}.json`, { [name]: [] });
const cases = await loadModel();
assert.equal(cases.byId.get(1).endState, 'unrecorded');
assert.equal(cases.byId.get(1).ghost, true);
assert.equal(cases.byId.get(2).endYear, 2026);
assert.equal(cases.byId.get(3).ghost, false);
assert.equal(cases.byId.get(4).unknownFounding, true);
const single = buildWeft(cases).solid.attributes.position.array;
assert.ok(Math.max(...single.filter((_, i) => i % 3 === 0)) > Math.min(...single.filter((_, i) => i % 3 === 0)), 'One-year titles must have nonzero width');
console.log('PASS: Woven preserves source records, represents every title, handles uncertain dates, and renders finite geometry in both drawing paths');
