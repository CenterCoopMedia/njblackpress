// Woven — GLSL sources. The cloth shader is the only custom material.

export const CLOTH_VERT = /* glsl */`
attribute float aThreadIndex;
attribute float aRibbonV;
attribute float aYearNorm;
attribute float aFlags;
attribute float aFraySeed;
attribute float aRamp;
attribute vec3 aColor;
// Half the ribbon's own width, in world units. Zero on the warp, which is
// background rule work and is left alone.
attribute float aHalfW;

uniform sampler2D uState;

// The floor on how thin a thread may be drawn, as a half-width in world units at
// the current zoom. Zoomed right out a real thread is a fifth of a pixel wide
// and simply misses the raster, so a band holding three papers drew as empty
// black. Sparse must read as sparse, never as nothing.
uniform float uMinHalfW;

// One pluck at a time. x is the picked thread, y and z are the two threads
// beside it, all as state-texture indices. A negative index matches nothing.
uniform vec3 uPluckIdx;
uniform float uPluckAge;   // seconds since the pluck
uniform float uPluckAmp;   // 0 under reduced motion
// World units per screen pixel at the current camera distance. The ripple is
// sized in pixels, so it stays as visible far out as it is close in.
uniform float uPluckScale;

varying float vRibbonV;
varying float vYearNorm;
varying float vFlags;
varying float vFraySeed;
varying float vRamp;
varying vec3 vColor;
varying vec4 vState;

// Amplitude for this vertex: full on the picked thread, a fifth on each
// neighbour, nothing anywhere else.
float pluckWeight(float idx) {
  float w = 0.0;
  w += step(abs(idx - uPluckIdx.x), 0.25) * 1.0;
  w += step(abs(idx - uPluckIdx.y), 0.25) * 0.2;
  w += step(abs(idx - uPluckIdx.z), 0.25) * 0.2;
  return w;
}

void main() {
  vRibbonV = aRibbonV;
  vYearNorm = aYearNorm;
  vFlags = aFlags;
  vFraySeed = aFraySeed;
  vRamp = aRamp;
  vColor = aColor;
  vState = texture2D(uState, vec2((aThreadIndex + 0.5) / 256.0, 0.5));

  vec3 p = position;
  // Widen outward from the thread's own centre line, never move the centre.
  p.y += aRibbonV * max(0.0, uMinHalfW - aHalfW);

  float w = uPluckAmp * pluckWeight(aThreadIndex);
  if (w > 0.0 && uPluckAge < 1.25) {
    // A struck string: a travelling wave, pinned at both ends, decaying to
    // nothing in about 1.2 seconds. No CPU physics, one uniform set per pluck.
    float envelope = exp(-uPluckAge * 2.6) * (1.0 - smoothstep(1.05, 1.25, uPluckAge));
    float shape = sin(vRamp * 3.14159265);
    float wave = sin(vRamp * 18.85 - uPluckAge * 27.0);
    float d = w * envelope * shape * wave;
    p.y += d * 0.20 * uPluckScale;
    p.z += d * 0.10 * uPluckScale;
  }

  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
}
`;

export const CLOTH_FRAG = /* glsl */`
precision highp float;

uniform float uWeaveProgress;
uniform float uFrayCut;
uniform float uGhostAlpha;
uniform vec3 uDimColor;
uniform vec3 uHighlightColor;

varying float vRibbonV;
varying float vYearNorm;
varying float vFlags;
varying float vFraySeed;
varying float vRamp;
varying vec3 vColor;
varying vec4 vState;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float valueNoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

void main() {
  // Weave reveal, soft at the growing edge.
  if (vYearNorm > uWeaveProgress + 0.004) discard;
  float revealFade = clamp((uWeaveProgress + 0.004 - vYearNorm) / 0.004, 0.0, 1.0);

  // Round-thread fake: a flat ribbon shaded like a cylinder.
  float r = clamp(abs(vRibbonV), 0.0, 1.0);
  float ny = sqrt(max(0.0, 1.0 - r * r));
  float lambert = clamp(dot(normalize(vec3(0.32, 0.64, 0.70)),
                           normalize(vec3(0.0, vRibbonV, ny))), 0.0, 1.0);
  float shade = 0.42 + 0.58 * lambert;
  vec3 col = vColor * shade;
  float alpha = revealFade;

  // Raking light: the cloth catches the lamp just behind the growing edge, so
  // the reader can see how far it has been drawn in. One exp, no branches.
  float rake = exp(-max(0.0, uWeaveProgress - vYearNorm) * 42.0);
  col += col * rake * 0.85;

  float ghost = mod(vFlags, 2.0);
  float unknownEnd = mod(floor(vFlags / 4.0), 2.0);

  if (ghost > 0.5) {
    alpha *= uGhostAlpha + vState.b * (0.62 - 0.28);
    float fray = valueNoise(vec2(vYearNorm * 34.0, vFraySeed * 91.0));
    if (fray < uFrayCut * vRamp) discard;
  }

  if (unknownEnd > 0.5) {
    alpha *= mix(1.0, 0.55, smoothstep(0.75, 1.0, vRamp));
  }

  // Dimming is capped. A dimmed thread must stay a visible thread, so it never
  // reaches the dim colour outright and never falls below a sixth of its alpha.
  col = mix(col, uDimColor, vState.g * 0.85);
  alpha *= mix(1.0, 0.18, vState.g);
  col = mix(col, uHighlightColor, vState.r);

  gl_FragColor = vec4(col, alpha);
}
`;

export const PANEL_VERT = /* glsl */`
uniform float uTime;
varying vec2 vUv;
void main() {
  vUv = uv;
  vec3 p = position;
  p.z += 0.06 * (1.0 - pow(2.0 * uv.x - 1.0, 2.0)) + 0.02 * sin(uv.x * 9.0 + uTime * 0.6);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
}
`;

export const PANEL_FRAG = /* glsl */`
precision highp float;
uniform sampler2D uMap;
uniform float uOpacity;
varying vec2 vUv;
void main() {
  // Unlit, untinted, unfiltered. We style the furniture, never the document.
  vec4 c = texture2D(uMap, vUv);
  gl_FragColor = vec4(c.rgb, c.a * uOpacity);
}
`;
