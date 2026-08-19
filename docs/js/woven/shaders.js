// Woven — GLSL sources. The cloth shader is the only custom material.

export const CLOTH_VERT = /* glsl */`
attribute float aThreadIndex;
attribute float aRibbonV;
attribute float aYearNorm;
attribute float aFlags;
attribute float aFraySeed;
attribute float aRamp;
attribute vec3 aColor;

uniform sampler2D uState;

varying float vRibbonV;
varying float vYearNorm;
varying float vFlags;
varying float vFraySeed;
varying float vRamp;
varying vec3 vColor;
varying vec4 vState;

void main() {
  vRibbonV = aRibbonV;
  vYearNorm = aYearNorm;
  vFlags = aFlags;
  vFraySeed = aFraySeed;
  vRamp = aRamp;
  vColor = aColor;
  vState = texture2D(uState, vec2((aThreadIndex + 0.5) / 256.0, 0.5));
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
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

  col = mix(col, uDimColor, vState.g);
  alpha *= mix(1.0, 0.15, vState.g);
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
