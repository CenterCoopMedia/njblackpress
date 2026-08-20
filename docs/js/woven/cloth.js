// Woven — weft and warp geometry, plus the thread state texture.

import * as THREE from 'three';
import { CLOTH_VERT, CLOTH_FRAG } from './shaders.js';
import { WEAVE_AMP, X_PER_YEAR, YEAR_MIN, YEAR_SPAN, x } from './layout.js';

const SPLIT_X = 74.5;
const OFF_LOOM_X = 78.5;
const OAK_500 = new THREE.Color('#6b563c');

class RibbonBuilder {
  constructor() {
    this.pos = []; this.idx = []; this.rv = []; this.yn = [];
    this.flags = []; this.seed = []; this.ramp = []; this.col = []; this.hw = [];
    this.count = 0;
  }

  // cols: [{ x, y, w, z, yearNorm, ramp }]
  strip(cols, meta) {
    for (let i = 0; i < cols.length - 1; i++) {
      const a = cols[i];
      const b = cols[i + 1];
      const quad = [
        [a, -1], [b, -1], [b, 1],
        [a, -1], [b, 1], [a, 1]
      ];
      for (const [c, v] of quad) {
        this.pos.push(c.x, c.y + (v * c.w) / 2, c.z);
        this.rv.push(v);
        this.hw.push(c.w / 2);
        this.yn.push(c.yearNorm);
        this.ramp.push(c.ramp);
        this.idx.push(meta.threadIndex);
        this.flags.push(meta.flags);
        this.seed.push(meta.fraySeed);
        this.col.push(meta.color[0], meta.color[1], meta.color[2]);
        this.count++;
      }
    }
  }

  toGeometry() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('aRibbonV', new THREE.Float32BufferAttribute(this.rv, 1));
    g.setAttribute('aHalfW', new THREE.Float32BufferAttribute(this.hw, 1));
    g.setAttribute('aYearNorm', new THREE.Float32BufferAttribute(this.yn, 1));
    g.setAttribute('aRamp', new THREE.Float32BufferAttribute(this.ramp, 1));
    g.setAttribute('aThreadIndex', new THREE.Float32BufferAttribute(this.idx, 1));
    g.setAttribute('aFlags', new THREE.Float32BufferAttribute(this.flags, 1));
    g.setAttribute('aFraySeed', new THREE.Float32BufferAttribute(this.seed, 1));
    g.setAttribute('aColor', new THREE.Float32BufferAttribute(this.col, 3));
    g.computeBoundingSphere();
    return g;
  }
}

const yearNorm = (xx) => Math.max(0, Math.min(1, xx / (YEAR_SPAN * X_PER_YEAR)));

function threadColumns(t) {
  const cols = [];
  const flags = (t.ghost ? 1 : 0) | (t.endState === 'still' ? 2 : 0) | (t.endState === 'unrecorded' ? 4 : 0);
  const meta = { threadIndex: t.threadIndex, flags, fraySeed: t.fraySeed, color: t.dyeRgb };

  if (t.unknownFounding) {
    // Founding year unrecorded: five short stitched fragments across the loom.
    // We do not know where these belong; we never guess a year to tidy the picture.
    const pieces = [];
    for (let i = 0; i < 5; i++) {
      const x0 = 4 + i * 14;
      pieces.push([
        colAt(x0, t, 0.03, 0, 0),
        colAt(x0 + 3.5, t, 0.03, 1, 1)
      ]);
    }
    return { pieces, meta };
  }

  const startX = t.x0;
  const endX = t.x1;
  const span = Math.max(0.5, endX - startX);
  const first = Math.floor(t.startYear);
  const last = Math.ceil(t.endYear);
  let k = 0;
  for (let y = first; y <= last; y++, k++) {
    const xx = Math.min(endX, Math.max(startX, x(y)));
    let w = t.width;
    if (t.endState === 'unrecorded') {
      const d = endX - xx;
      if (d < 1.0) w *= 0.4 + 0.6 * d;
    }
    const z = WEAVE_AMP * (((t.threadIndex + k) % 2) ? 1 : -1);
    cols.push({ x: xx, y: t.y, w, z, yearNorm: yearNorm(xx), ramp: (xx - startX) / span });
  }

  const pieces = [cols];

  if (t.endState === 'ceased') {
    // Clean selvedge: a 0.10-unit tuck folding the end back on itself.
    const e = cols[cols.length - 1];
    pieces.push([
      { ...e, w: t.width, z: e.z },
      { ...e, x: e.x - 0.10, w: t.width * 0.55, z: e.z - 0.05, ramp: 1 }
    ]);
  }

  if (t.endState === 'still') {
    // Past the right post, into three loose strands that taper to nothing.
    const last2 = cols[cols.length - 1];
    for (const dy of [-0.06, 0, 0.06]) {
      const strand = [];
      for (let s = 0; s <= 8; s++) {
        const xx = SPLIT_X + ((OFF_LOOM_X - SPLIT_X) * s) / 8;
        const taper = 1 - s / 8;
        strand.push({
          x: xx, y: t.y + dy * (s / 8), w: t.width * taper, z: last2.z,
          yearNorm: 1, ramp: 1
        });
      }
      pieces.push(strand);
    }
    // Bridge from the cloth edge to the split point.
    pieces.push([
      { ...last2, x: x(2026), yearNorm: 1, ramp: 1 },
      { ...last2, x: SPLIT_X, yearNorm: 1, ramp: 1 }
    ]);
  }

  return { pieces, meta };
}

function colAt(xx, t, w, ramp, k) {
  return { x: xx, y: t.y, w, z: WEAVE_AMP * ((k % 2) ? 1 : -1), yearNorm: yearNorm(xx), ramp };
}

export function buildWeft(model) {
  const solid = new RibbonBuilder();
  const ghost = new RibbonBuilder();
  for (const t of model.order) {
    const b = t.ghost ? ghost : solid;
    const { pieces, meta } = threadColumns(t);
    for (const p of pieces) b.strip(p, meta);
  }
  return { solid: solid.toGeometry(), ghost: ghost.toGeometry() };
}

export function buildWarp(model, every, slotEvery) {
  const b = new RibbonBuilder();
  const meta = { threadIndex: 255, flags: 0, fraySeed: 0.5, color: [OAK_500.r, OAK_500.g, OAK_500.b] };
  const ys = [];
  ys.push(0.9);
  model.layout.slots.forEach((t, i) => { if (i % slotEvery === 0) ys.push(t.y); });
  for (const band of model.bands) if (band.count) ys.push(band.top - band.height - 0.35);
  ys.push(-28.6);
  ys.sort((a, c) => c - a);

  for (let year = YEAR_MIN; year <= YEAR_MIN + YEAR_SPAN; year += every) {
    const xx = x(year);
    const decade = year % 10 === 0;
    const w = decade ? 0.030 : 0.022;
    const cols = ys.map((yy, i) => ({
      x: xx, y: yy, w, z: -WEAVE_AMP * (((year + i) % 2) ? 1 : -1),
      yearNorm: 0, ramp: 1
    }));
    // Warp ribbons run vertically, so swap the offset axis by building columns
    // along Y with the width applied in X.
    for (let i = 0; i < cols.length - 1; i++) {
      const a = cols[i];
      const c = cols[i + 1];
      const quad = [[a, -1], [c, -1], [c, 1], [a, -1], [c, 1], [a, 1]];
      for (const [p, v] of quad) {
        b.pos.push(p.x + (v * p.w) / 2, p.y, p.z);
        // Zero half-width: the minimum-thickness floor is for publications, not
        // for the warp rules behind them.
        b.rv.push(v); b.hw.push(0); b.yn.push(0); b.ramp.push(1);
        b.idx.push(255); b.flags.push(0); b.seed.push(0.5);
        b.col.push(meta.color[0], meta.color[1], meta.color[2]);
        b.count++;
      }
    }
  }
  return b.toGeometry();
}

export function createStateTexture(count) {
  const data = new Uint8Array(256 * 4);
  const tex = new THREE.DataTexture(data, 256, 1, THREE.RGBAFormat, THREE.UnsignedByteType);
  tex.minFilter = THREE.NearestFilter;
  tex.magFilter = THREE.NearestFilter;
  tex.generateMipmaps = false;
  tex.needsUpdate = true;
  return {
    texture: tex,
    data,
    count,
    set(i, ch, v) { data[i * 4 + ch] = v; },
    get(i, ch) { return data[i * 4 + ch]; },
    clear(ch, v = 0) { for (let i = 0; i < 256; i++) data[i * 4 + ch] = v; },
    commit() { tex.needsUpdate = true; }
  };
}

// One pluck runs at a time across every cloth material, so all of them share
// these three uniform objects. Writing the value once updates every mesh and
// costs no extra draw call.
export const pluckUniforms = {
  uPluckIdx: { value: new THREE.Vector3(-1, -1, -1) },
  uPluckAge: { value: 99 },
  uPluckAmp: { value: 1 },
  // World units per screen pixel when the pluck was struck, so the ripple is the
  // same size on screen at every zoom. Written once per pluck.
  uPluckScale: { value: 1 }
};

// The reveal edge is shared for the same reason: one edge crosses the whole
// cloth, so one uniform object drives every mesh.
export const weaveUniform = { value: 0 };

// The on-screen floor for thread thickness, written once per frame from the
// camera distance. One object, so every cloth mesh reads the same number.
export const minHalfWidth = { value: 0 };

export function createClothMaterial(state, opts = {}) {
  return new THREE.ShaderMaterial({
    vertexShader: CLOTH_VERT,
    fragmentShader: CLOTH_FRAG,
    uniforms: {
      uState: { value: state.texture },
      uWeaveProgress: weaveUniform,
      uMinHalfW: minHalfWidth,
      uPluckIdx: pluckUniforms.uPluckIdx,
      uPluckAge: pluckUniforms.uPluckAge,
      uPluckAmp: pluckUniforms.uPluckAmp,
      uPluckScale: pluckUniforms.uPluckScale,
      uFrayCut: { value: opts.frayCut ?? 0.22 },
      uGhostAlpha: { value: opts.ghostAlpha ?? 0.28 },
      uDimColor: { value: new THREE.Color('#2b2318') },
      uHighlightColor: { value: new THREE.Color('#f0854a') }
    },
    transparent: true,
    depthWrite: opts.depthWrite !== false,
    depthTest: true,
    side: THREE.DoubleSide,
    alphaTest: 0.02
  });
}
