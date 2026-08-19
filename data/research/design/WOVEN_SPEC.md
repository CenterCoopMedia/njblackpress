# Woven — technical and creative spec

Spec for issue #49. Implementation tickets are #50 (loom scene), #51 (story mode), #52 (ghost cloth), #53 (accessibility twin and fallback).

Author: woven-spec agent. Date: 2026-08-19.

Read `DESIGN_DIRECTION.md` before this file. Woven does not get its own palette, its own type, or its own rules about evidence. It uses the walnut/oak/linen/thread/stain tokens, the material split (wood is structure, fabric is surface, ink is content), and the rights rules from section 1 of that document. Where this spec and the design direction disagree, the design direction wins.

---

## 0. The piece, in one paragraph

One continuous woven cloth on a wooden loom. The warp is time — 147 threads, one per year from 1880 to 2026, strung top to bottom on the loom. The weft is the archive — 138 threads, one per publication, each starting at the year it was founded and ending at the year it stopped. Thread thickness is evidence weight: the more surviving material we hold for a title, the thicker its thread. The 19 titles still publishing run past the right-hand loom post and end in loose, unfinished strands. The 98 titles that survive only as a catalog line are woven in the same cloth as ghost threads — translucent, frayed, thinning to nothing. 81 event knots sit on the threads where something documented happened. 13 story tours move the camera through the cloth, dim everything not in the thread, and unfurl rights-cleared clipping panels in front of it.

The governing idea from the design direction holds here without exception: **this must not make the archive look more complete than it is.** A weave is a seductive form. Every design choice below is a check on that seduction.

---

## 1. File layout and loading

### 1.1 Files

```
docs/woven.html                          the page
docs/css/woven.css                       page chrome, twin, panels, tour bar
docs/js/woven/main.js                    entry, capability test, render loop, router
docs/js/woven/data.js                    fetch + derive the thread model and tours
docs/js/woven/layout.js                  year→x, slot→y, era bands, camera fitting
docs/js/woven/cloth.js                   weft + warp geometry, thread state texture
docs/js/woven/shaders.js                 GLSL source strings
docs/js/woven/loom.js                    frame, beams, lights, band rules, era labels
docs/js/woven/knots.js                   instanced event knots
docs/js/woven/picking.js                 plane-projection hover and pick
docs/js/woven/panel.js                   publication / event HTML side panel
docs/js/woven/tour.js                    story mode, keyframes, clipping panels
docs/js/woven/ghost.js                   the ghost cloth sequence
docs/js/woven/twin.js                    accessibility twin DOM, live region, keys
docs/js/woven/fallback.js                no-WebGL route
docs/vendor/three-0.171.0/three.module.min.js
docs/vendor/three-0.171.0/addons/controls/OrbitControls.js
docs/vendor/three-0.171.0/VENDOR.md      source URL, version, sha384 hashes
docs/images/evidence/                    clipping web assets (issue #54 output)
docs/data/clippings.json                 clipping index (issue #54 output)
```

No file may exceed 400 lines. If one does, split it.

### 1.2 three.js version and integrity

**Pinned version: three.js r171 (`three@0.171.0`).** It is the last release before the WebGPU renderer became the default export path, so `WebGLRenderer` and the `examples/jsm` addons stay where every reference expects them, and it ships `three.module.min.js` as a plain ES module with no bundler assumptions.

**CDN of record: jsDelivr.** Canonical URLs:

```
https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.module.min.js
https://cdn.jsdelivr.net/npm/three@0.171.0/examples/jsm/controls/OrbitControls.js
```

**Integrity approach: vendor the files, hash them, and never fetch them at runtime.** Download both files once from the URLs above, commit them under `docs/vendor/three-0.171.0/`, and record the version, the source URL, and the `sha384` of each file in `docs/vendor/three-0.171.0/VENDOR.md`. The page then loads them same-origin from GitHub Pages.

The reason is not preference. Subresource integrity does not apply to module specifiers resolved through an import map. The import-map `integrity` key exists but is not supported widely enough in 2026 to be the only guarantee. Self-hosting removes the third-party origin entirely, which also removes a runtime dependency, a privacy hop, and a whole class of CDN-outage failure. It costs ~170 KB gzipped in the repo and zero build steps.

Add the import-map `integrity` block anyway, for the browsers that honour it:

```html
<script type="importmap">
{
  "imports": {
    "three": "./vendor/three-0.171.0/three.module.min.js",
    "three/addons/": "./vendor/three-0.171.0/addons/"
  },
  "integrity": {
    "./vendor/three-0.171.0/three.module.min.js": "sha384-<recorded>"
  }
}
</script>
<script type="module" src="js/woven/main.js"></script>
```

Regenerate the hashes with `shasum -b -a 384 <file> | xxd -r -p | base64` and paste them into both `VENDOR.md` and the import map. If the two disagree, the page fails to load in Chrome — that is the intended behaviour.

**ES modules here, IIFE everywhere else.** Woven is the one page on this site that uses `type="module"` and real imports. It is self-contained, it never touches `window.njbp`, and the rest of the site is untouched. Woven exposes `window.njbpWoven = { open(pubId), playStory(storyId), showGhost(), exit() }` so the existing pages can deep-link into it. That is the entire cross-module surface.

### 1.3 The page shell and degradation

`woven.html` copies the head block from `index.html` verbatim — the same meta tags, the same Google Fonts request, the same Tailwind CDN script, and the same inline `tailwind.config` with the walnut/oak/linen/thread/stain tokens from the material language section. Then it adds `css/woven.css` and the import map.

The body ships, in source order:

1. Skip link — "skip the weave, read the archive as a list"
2. `<header>` — site nav, identical to the other pages
3. `<section id="woven-intro">` — the intro copy in section 7, in real HTML
4. `<div id="woven-stage">` — the sticky canvas wrapper containing `<canvas id="woven-canvas" role="application" tabindex="0" aria-describedby="woven-help">` and the HTML overlays
5. `<div id="woven-twin">` — the accessibility twin (section 6)
6. `<noscript>` block
7. `<footer>` — site footer

Three degradation routes, in order of severity:

**No JavaScript.** The `<noscript>` block renders. It says: "The weave is drawn with JavaScript. The same 138 publications, their dates, and their evidence are on the archive page." with links to `archive.html` and `index.html#timeline`. The canvas and the twin are both empty in source — the twin is data-driven and cannot exist without a fetch. Do not attempt to inline the data; `publications.json` is 316 KB.

**JavaScript but no WebGL.** `main.js` runs `hasWebGL()` before importing anything from `three`:

```js
function hasWebGL() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch { return false; }
}
```

On false, `main.js` dynamic-imports only `data.js`, `twin.js`, and `fallback.js`. three.js is never fetched. The stage is removed from the DOM, the twin is promoted to primary content, and a banner appears above it: "Your browser cannot draw the weave, so here it is as a list." with the same two links. Everything in the twin works.

**WebGL context lost mid-session.** Listen for `webglcontextlost` on the canvas. On fire: `preventDefault()` is *not* called, the stage is removed, the twin is promoted, and the banner reads "The drawing stopped. Here is the same archive as a list." Any running tour stops and its current stop stays open in the twin.

`?nogl=1` forces the fallback route for testing. `?twin=1` shows the twin alongside a working canvas.

---

## 2. Scene graph and geometry

### 2.1 Coordinate system

Right-handed, Y up, camera on +Z looking toward −Z. One world unit ≈ 0.9 metres if you need a mental scale; the loom is furniture-sized.

**X is time.**

```
x(year) = (year - 1880) * 0.50
```

1880 → 0.0. 2026 → 73.0. One year is half a unit. Fractional years (from month/day precision on events) interpolate.

**Y is the publication slot, descending from the breast beam.**

Publications are grouped into eight era bands by `yearFounded`, then sorted inside a band by `yearFounded` ascending, then `name` ascending. Band order is chronological, top to bottom.

| Band | Range | Count | Height (count × 0.16) |
|---|---|---|---|
| A | 1880–1899 | 3 | 0.48 |
| B | 1900–1929 | 6 | 0.96 |
| C | 1930–1949 | 17 | 2.72 |
| D | 1950–1969 | 19 | 3.04 |
| E | 1970–1989 | 51 | 8.16 |
| F | 1990–2009 | 25 | 4.00 |
| G | 2010–2026 | 14 | 2.24 |
| U | founding year unrecorded | 3 | 0.48 |

Constants: `PITCH = 0.16`, `BAND_GAP = 0.70`, `bandTop[A] = -0.60`.

```
bandTop[n+1] = bandTop[n] - height[n] - BAND_GAP
slotY(band, j) = bandTop[band] - (j + 0.5) * PITCH
```

Cloth extent: x ∈ [0, 73], y ∈ [−0.60, −27.58]. Band U sits below G with the same gap and is labelled "founding year unrecorded"; its three threads (ids 14, 50, 128) are drawn as short stitched fragments, not full-span threads, because we do not know where they belong. Never guess a year to make the picture tidier.

**Why era bands and not city grouping.** Newark holds 40 of 138. A city grouping produces one 6.4-unit block and 44 slivers, which is the same distribution problem the design direction rejected a map for. Era bands are near-monotone with X, so threads read as a diagonal drift down and to the right — the archive's actual shape — and no thread ever has to cross another to reach its slot. City is carried instead by the hover tooltip, the panel, and the twin's text. Sorting inside a band by founding year means adjacent threads start near each other, which keeps the left edge of each band tidy without any curve routing.

**Occlusion is solved by construction, not by depth sorting.** Every weft thread is a horizontal band at a fixed Y with maximum width 0.10 against a 0.16 pitch. No two weft threads can overlap. The only depth interaction in the whole scene is weft-over-warp at the crossings, and that is 0.07 units of Z displacement, well inside the depth buffer's precision at these camera distances.

**Z.** The cloth plane is z = 0. Plain-weave undulation is z = ±0.035. Clipping panels sit at z = +3.0. The loom frame occupies z ∈ [−0.5, +0.5].

### 2.2 The weft — publication threads

**Geometry: one merged, static, non-indexed `BufferGeometry` of flat ribbons. Not instanced, not `TubeGeometry`.**

Instancing is wrong here because every thread has a different length, a different width, and a different end treatment; the instance transform cannot express that without a per-instance geometry, which defeats the point. `TubeGeometry` is wrong because a round tube at this scale costs 8–12× the triangles for a highlight that a two-triangle ribbon can fake exactly (see 2.6).

Build, per publication:

- Segment the thread at every integer year from `yearFounded` to `endYear`, inclusive. `endYear = yearCeased ?? 2026`.
- At each year column, emit two vertices offset ±`w/2` in Y, where `w` is the thread width from the evidence mapping.
- Z per column alternates: `z = WEAVE_AMP * (((threadIndex + yearIndex) % 2) ? 1 : -1)`, `WEAVE_AMP = 0.035`. That is a true plain weave against the warp, which takes the opposite parity.
- Consecutive column pairs form two triangles.

Per-vertex attributes:

| Attribute | Type | Meaning |
|---|---|---|
| `position` | vec3 | as above |
| `aThreadIndex` | float | 0–137, the row in the state texture |
| `aRibbonV` | float | −1 at the lower edge, +1 at the upper edge; drives the round-thread shading |
| `aYearNorm` | float | `(year - 1880) / 146`, drives the scroll-driven weave reveal |
| `aColor` | vec3 | era dye, linear sRGB |
| `aFlags` | float | bit 0 ghost, bit 1 unfinished, bit 2 unknown-end |
| `aFraySeed` | float | per-thread random in [0,1), stable across reloads via a seeded PRNG keyed on publication id |

**End treatments — three, and they must stay distinguishable.**

*Ceased* (42 titles, `yearCeased` is set). Clean selvedge: the ribbon terminates at `x(yearCeased)` with a 0.10-unit vertical tuck — two extra quads folding the end back on itself. Reads as a finished edge.

*Still publishing* (19 titles, see 2.7 for the rule). The ribbon continues past the right loom post to `x = 78.5`, splits into three strands at `x = 74.5` splaying ±0.06 in Y, and each strand tapers linearly to zero width over its last 2.0 units. `aFlags` bit 1 set. These threads are the only geometry that crosses the loom frame, and that crossing is the point.

*End unrecorded* (77 titles — `isActive` is true only because the source cell was blank). The ribbon runs to `x(2026)` but tapers to 40% width over its last 1.0 unit and gets no selvedge. `aFlags` bit 2 set, and the fragment shader multiplies alpha by `smoothstep` down to 0.55 over the same run. It has to look unresolved, because it is. Do not draw these the same as a still-publishing thread; 77 of 138 titles hang on this distinction and getting it wrong would be the single largest overstatement the piece could make.

**Triangle count.** Roughly 6,900 quads for the spans plus ~1,500 for tucks, splits, and frays. **≈ 15,000 triangles, one draw call.**

### 2.3 The warp — year threads

147 threads, one per year 1880–2026, running the full loom height from the breast beam (y = 0) to the cloth beam (y = −28.6). They exist whether or not any publication crosses them. That is the loom: the warp is strung for the whole span, and the cloth only exists where somebody wove.

Same ribbon construction, width fixed at 0.022, colour `oak-500 #6b563c`, alpha 0.55. A warp thread gets a vertex ring at every weft slot Y so the over/under parity is real, plus one at each band gap.

Two prebuilt meshes, one visible at a time:

- `warpFull` — all 147, ring per slot. 147 × 138 × 2 ≈ 40,600 vertices, **≈ 40,600 triangles**.
- `warpCoarse` — every 4th year (37 threads), ring every 4th slot. **≈ 2,600 triangles**.

Swap on camera distance: `warpFull` when `camera.position.distanceTo(target) < 45`, else `warpCoarse`. The default full-cloth framing is around distance 70, so the expensive warp only exists when the reader has zoomed in far enough to see individual crossings. Decade years (1880, 1890, …) render at width 0.030 and `oak-400`, and carry a small mono year label in the HTML overlay along the top rail — never in-canvas text.

### 2.4 The loom frame

Wood is structure. Nothing else in the scene may be wood-coloured furniture.

| Part | Geometry | Position | Material |
|---|---|---|---|
| Left post | `BoxGeometry(1.2, 31, 1.0)` | x = −2.5 | oak-500 |
| Right post | `BoxGeometry(1.2, 31, 1.0)` | x = 75.5 | oak-500 |
| Breast beam | `CylinderGeometry(0.55, 0.55, 79, 12)` rotated Z 90° | y = 0.9 | oak-400 |
| Cloth beam | `CylinderGeometry(0.70, 0.70, 79, 12)` rotated Z 90° | y = −28.6 | oak-400 |
| Heddle bar | `BoxGeometry(79, 0.28, 0.28)` | y = −29.9, z = 0.9 | oak-500 |
| Band rules | 7 × `BoxGeometry(76, 0.05, 0.06)` | one per band gap | oak-500, alpha 0.5 |

≈ 2,900 triangles across 13 meshes. Merge the seven band rules into one geometry; merge the four beams and posts into one. **Two draw calls.**

Material: `MeshLambertMaterial`, no map, no shadows. Lights: one `HemisphereLight(0xa89179, 0x0b0806, 0.55)` and one `DirectionalLight(0xf3eee2, 0.75)` at `(0.4, 0.8, 1.0)` normalized. `renderer.shadowMap.enabled = false` — shadows on a flat cloth buy nothing and cost a whole extra pass.

No wood texture map. No bevels. No fake hardware. The design direction's "what not to do" list applies to geometry exactly as it applies to CSS.

### 2.5 Event knots

81 events, two `InstancedMesh` objects split by confidence — shape carries confidence, not colour, so the encoding survives a colourblind reader and matches the timeline convention already set in the design direction.

| Confidence | Count | Geometry | Colour |
|---|---|---|---|
| high | 70 | `TorusGeometry(0.085, 0.038, 6, 12)` — closed | `stain #e2662b` |
| medium | 11 | `TorusGeometry(0.085, 0.030, 6, 12, 4.6)` — open arc | `linen-300 #cdc4b1` |

144 triangles each → **≈ 11,700 triangles, two draw calls.**

Placement: `x = x(fractionalYear(event.date))`, `y = slotY(primary thread)`, `z = 0`. Rotation: torus axis along X so the knot reads as a bead threaded onto the ribbon; add a per-instance random Z-roll from the seeded PRNG so 81 knots do not look stamped.

An event with several `publicationIds` gets one instance per publication id, capped at 3 per event, and the instances share a `sourceEventId`. An event with no `publicationIds` (8 of 81) is placed on a **context tick** above the top band rule at y = +0.35, joined to nothing, and it is announced in the twin as "context — not tied to a specific publication". It is never drawn on a thread, because that would be a claim we cannot support.

Idle knots do not animate. During a tour, the active stop's knot scales 1.0 → 1.35 → 1.0 over 1200 ms; under `prefers-reduced-motion` it holds at 1.35 with no animation.

### 2.6 Cloth shading

**Custom `ShaderMaterial`, not a material trick, and it is 40 lines.**

Vertex shader:

- Standard `projectionMatrix * modelViewMatrix * vec4(position,1.0)`.
- Sample the thread state texture at `u = (aThreadIndex + 0.5) / 256.0`, pass state to the fragment shader as a varying.
- Pass `aRibbonV`, `aColor`, `aFlags`, `aFraySeed`, `aYearNorm`.
- Weave reveal: nothing here; the reveal is a fragment discard so the edge can be soft.

Fragment shader:

```glsl
// round-thread fake: a flat ribbon shaded like a cylinder
float r = clamp(abs(vRibbonV), 0.0, 1.0);
float ny = sqrt(max(0.0, 1.0 - r * r));          // cylinder normal, Y component
float lambert = clamp(dot(normalize(vec3(0.32, 0.64, 0.70)),
                          normalize(vec3(0.0, vRibbonV, ny))), 0.0, 1.0);
float shade = 0.42 + 0.58 * lambert;             // wrap term, never fully black
vec3 col = vColor * shade;
```

That single `sqrt` turns a two-triangle flat strip into something that reads as a round, lit thread from any angle the camera is allowed to reach. It is the whole reason instancing and tube geometry are unnecessary.

Then, in order:

1. **Weave reveal** — `if (vYearNorm > uWeaveProgress + 0.004) discard;` and fade alpha over the leading 0.004 so the growing edge is soft, not stepped.
2. **Ghost** — when bit 0 is set, `alpha *= 0.28` and apply the fray: `float fray = noise(vec2(vYearNorm * 34.0, vFraySeed * 91.0)); if (fray < uFrayCut * frayRamp) discard;` where `frayRamp` rises from 0 at the thread's start to 1 at its end, so a ghost thread is solid where the catalog actually pins it and eaten away where it does not. Use a 12-line hash-based value noise; do not load a noise texture.
3. **Unknown end** — when bit 2 is set, `alpha *= mix(1.0, 0.55, endRamp)`.
4. **Dim and highlight** — `col = mix(col, uDimColor, state.g); alpha *= mix(1.0, 0.15, state.g); col = mix(col, uHighlightColor, state.r);`
5. Output `vec4(col, alpha)`.

Material settings: `transparent: true`, `depthWrite: true`, `depthTest: true`, `side: THREE.DoubleSide`, `alphaTest: 0.02`. Depth write stays on because the alpha here is either near-1 or discarded; the ghost threads at 0.28 are the exception and they are drawn in a second pass with `depthWrite: false` and `renderOrder: 2`. That means the weft is technically two draw calls, solid and ghost, sharing one geometry via `drawRange` — sort the merged geometry so all solid threads precede all ghost threads and the split is a single index.

**Thread state texture.** One `DataTexture`, 256 × 1, `RGBAFormat`, `UnsignedByteType`, `NearestFilter` on both min and mag, `generateMipmaps: false`. Row *i* is publication *i*.

| Channel | Meaning |
|---|---|
| R | highlight, 0–255 |
| G | dim, 0–255 |
| B | ghost alpha boost, 0–255 (used only by the ghost sequence) |
| A | flags: bit 0 selected, bit 1 hovered, bit 2 in current tour |

Dimming 119 threads for a tour is 138 byte writes and one `needsUpdate = true`. No geometry rebuild, no material swap, no change in draw calls, ever. This is the single most important performance decision in the spec — every state change in the piece goes through this texture.

### 2.7 The data → visual mapping table

Field by field. Every visual property in the scene traces to exactly one row here.

| Source | Field | Visual property | Rule |
|---|---|---|---|
| publications.json | `id` | thread identity, deep link | `?pub=<id>`; also the twin's `id="thread-<id>"` |
| | `yearFounded` | thread start X, era band | `x(yearFounded)`. Null (3 titles) → band U, drawn as a fragment |
| | `yearCeased` | thread end X, selvedge | `x(yearCeased)` + tuck. Null → see `isActive` |
| | `isActive` + `yearFounded` + `websiteUrl` | end treatment | **still publishing** if `isActive && (yearFounded >= 1995 \|\| websiteUrl is a live host)`; live host = `websiteUrl` present and not matching `/loc\.gov\|worldcat\.org\|archive\.org\|libraries\.rutgers\.edu\|marxists\.org/i`. Current data: 19 titles. Otherwise if `isActive` → **end unrecorded** (77). Otherwise → **ceased** (42) |
| | `evidence.length` | thread width | `w = clamp(0.030 + 0.026 * ln(1 + n), 0.030, 0.100)`. n=0 → 0.030, 1 → 0.048, 2 → 0.059, 3 → 0.066, 10 → 0.092 |
| | `evidence[].rightsStatus` | ghost flag | ghost when **no** entry has status `publishable`, `publishable_with_credit`, or `crop_first`. Current data: 98 titles |
| | `decade` / `yearFounded` | era band, era dye | band from the table in 2.1; dye interpolated across 7 steps from `oak-300 #a89179` (band A) to `linen-100 #f3eee2` (band G), band U → `thread-400 #a89c85` |
| | `city` | nothing in the canvas | tooltip, panel, twin text only |
| | `name`, `alternateName` | tooltip, panel, twin | never rendered in the canvas |
| | `medium`, `format`, `frequency`, `publishers`, `languages`, `primaryFocus`, `missionStatement`, `historicalNotes`, `targetAudience`, `keyStaff`, `archiveUrl`, `websiteUrl` | panel and twin only | no geometry |
| events.json | `date` | knot X | `fractionalYear()` — see 5.1 |
| | `publicationIds` | knot Y | one instance per id, max 3; empty → context tick at y = +0.35 |
| | `confidence` | knot shape and colour | `high` → closed torus, stain. `medium` → open arc torus, linen-300 |
| | `title`, `description`, `people`, `sourceFiles` | overlay and twin text | never in-canvas |
| stories.json | `eventIds` | tour keyframes | one stop per event, date-sorted |
| | `publicationIds` | tour thread set | these threads highlight; every other thread dims |
| | `era` | tour opening framing, band label | parsed to a band range for the transit rule (5.3) |
| | `strength` | tour warning | `weak` → "thinly sourced" label on the tour card and the opening stop; never autoplays |
| | `thread`, `title`, `people` | overlay text | never in-canvas |
| clippings.json | `webPath` | clipping panel texture | absent → no panel, citation-only card instead |
| | `rightsStatus` | panel frame | `crop_first` → 1px stain frame + "clip" label. Others → no frame |
| | `altText` | panel `alt`, live region | **missing `altText` means no panel renders.** Same rule as the evidence card |
| | `citation`, `caption` | overlay `<figcaption>` and `<cite>` | never in-canvas |

**Three counts to verify at build time, not to hardcode.** The still-publishing count (19), the ghost count (98), and the total (138) are all computed from the data at load and interpolated into the copy strings. Issue #52 says 93 ghosts; this spec's rule yields 98 against the current `publications.json`. Do not paper over that — ticket T5 must reconcile the two numbers against `source-catalog.json` and either fix the rule or fix the issue. Ship whichever number the rule actually produces.

---

## 3. Performance budget

**Target: a locked 60 fps on a 2021-class laptop with integrated graphics (Iris Xe / Apple M1) at 1440 × 900 CSS pixels, DPR 2.**

### 3.1 Ceilings

| Budget | Ceiling | Expected |
|---|---|---|
| Triangles, full-cloth view | 90,000 | ≈ 32,000 |
| Triangles, zoomed in | 90,000 | ≈ 70,000 |
| Draw calls | 14 | 8 idle, 11 during a tour |
| Geometry memory | 8 MB | ≈ 2.6 MB |
| Texture memory | 24 MB | ≤ 22 MB with 4 panels resident |
| JS heap after load | 60 MB | ≈ 34 MB |
| Time to first frame | 1200 ms | ≈ 700 ms on cable |
| Total page transfer | 900 KB | ≈ 690 KB (three 170 KB gz + data 130 KB gz + fonts) |

Draw-call inventory: weft-solid, weft-ghost, warp (one of two), knots-high, knots-medium, loom frame, band rules, clipping panel (0–2 during tours), panel frame (0–1). That is 7 idle, 8 with a warp swap, 11 at a tour's busiest stop.

### 3.2 Render on change, not continuously

The render loop is gated:

```js
let needsRender = true;
function frame() {
  requestAnimationFrame(frame);
  const active = controls.update() || tour.isPlaying || ghost.isPlaying
                 || intro.isAnimating || tween.count > 0;
  if (!needsRender && !active) return;
  renderer.render(scene, camera);
  needsRender = false;
}
```

`needsRender = true` is set by: pointer move that changes the hover target, any state-texture write, a warp LOD swap, a resize, a panel load, and a deep-link navigation. An idle reader looking at a static weave costs zero GPU work. This is worth more than every other optimization in this section combined.

### 3.3 Renderer settings

```js
new THREE.WebGLRenderer({
  canvas,
  antialias: window.devicePixelRatio < 2,
  powerPreference: 'high-performance',
  alpha: false,
  stencil: false,
  depth: true
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setClearColor(0x0b0806, 1);   // walnut-950
```

If the canvas would exceed 2.2 megapixels after DPR, drop the pixel ratio to 1.5 and re-check. No post-processing, no MSAA render targets, no tone mapping.

### 3.4 Adaptive degrade

Sample frame time over a rolling 60-frame window. If the median exceeds 22 ms for two consecutive windows, degrade one step and re-measure. Steps, in order:

1. Force `warpCoarse` regardless of distance.
2. Drop pixel ratio to 1.25.
3. Stop the knot pulse and the panel sag animation.
4. Show a one-line notice — "Simplified the drawing to keep it smooth." — and a link to the twin.

Never degrade the thread widths, the ghost fray, or the end treatments. Those carry meaning. Degrade the decoration.

### 3.5 Clipping panel textures

Panels load lazily, per tour stop, and only for stops that have a cleared `webPath`.

- Max long edge 1024 px, JPEG, quality 82 (issue #54 produces these).
- Max 4 resident `THREE.Texture` objects, LRU. On eviction call `texture.dispose()` and null the material map.
- `generateMipmaps: true`, `minFilter: LinearMipmapLinearFilter`, `anisotropy: Math.min(4, renderer.capabilities.getMaxAnisotropy())`, `colorSpace: SRGBColorSpace`.
- 1024² RGBA + mips ≈ 5.6 MB → four resident ≈ 22 MB. Hard cap 24 MB; if a decoded image would breach it, evict before upload.
- Prefetch exactly one stop ahead during a tour, never more. `img.decode()` before creating the texture so the upload never lands mid-frame.
- On a failed fetch or a missing `altText`, silently fall back to the citation-only card. A broken image in an archive about evidence is worse than no image.

---

## 4. Interaction model

### 4.1 Camera and controls

`OrbitControls` with `enableDamping: true`, `dampingFactor: 0.08`, and hard bounds. The reader must never see the cloth edge-on or from behind.

| Bound | Value |
|---|---|
| `minPolarAngle` | 0.96 rad (55°) |
| `maxPolarAngle` | 1.75 rad (100°) |
| `minAzimuthAngle` | −0.61 rad (−35°) |
| `maxAzimuthAngle` | +0.61 rad (+35°) |
| `minDistance` | 8 |
| `maxDistance` | 130 |
| `enablePan` | true, clamped to the cloth bbox + 10% each side |
| `screenSpacePanning` | true |
| `rotateSpeed` | 0.45 |
| `zoomSpeed` | 0.7 |

Clamp panning in the `change` handler by writing `controls.target` back inside the box. Do not rely on `maxTargetRadius` alone — it is a sphere and the cloth is 2.7:1.

Initial framing: `fitToBox(clothBox, 0.06)` — solve for the distance that contains the box width and height at the current aspect with 6% margin, then place the camera at that distance along `(0.0, 0.12, 1.0)` normalized from the box centre. On a 16:9 viewport that lands near distance 70. Recompute on resize; never hardcode a distance.

`0` resets to the initial framing. `+` / `−` dolly by a factor of 1.3 per press.

### 4.2 Picking

**Do not raycast the cloth.** 55,000 thin ribbon triangles give a miserable hit rate and a bad worst case.

Threads are picked analytically:

```js
raycaster.setFromCamera(ndc, camera);
const hit = raycaster.ray.intersectPlane(CLOTH_PLANE /* z = 0 */, tmpVec3);
if (!hit) return null;
const year = 1880 + hit.x / 0.50;
const slot = slotAtY(hit.y);          // binary search over a sorted band table, O(log n)
if (!slot) return null;
const t = threads[slot.index];
if (Math.abs(hit.y - t.y) > t.width / 2 + 0.035) return null;   // 0.035 forgiveness
if (year < t.startYear - 0.5 || year > t.endXYear + 0.5) return null;
return { thread: t, year };
```

Constant time, no allocation in the hot path, and the 0.035 tolerance makes a 0.030-wide thread comfortably clickable on a touchscreen. Touch gets 0.06.

Knots are picked with a real raycast against the two `InstancedMesh` objects only — 81 instances, `intersectObjects([knotsHigh, knotsMedium], false)`, returns `instanceId`. Knots take priority over threads when both hit.

Pointer move is throttled to one test per `requestAnimationFrame`. Hover writes the state texture (flags bit 1), sets `needsRender`, and positions the HTML tooltip.

### 4.3 Hover

An absolutely positioned `<div id="woven-tip" role="presentation">`, `.surface-cloth` on walnut-700 with a walnut-600 hairline, offset 14 px from the pointer and flipped when it would leave the viewport. Content, three lines:

```
The New Jersey Herald News
Newark · 1938–1948
10 items of evidence
```

For a ghost thread the third line reads `catalog entry only`. For a knot: event title, then the date, then `medium confidence` when applicable. The tooltip is decorative — everything in it is already in the twin — so it is `role="presentation"` and never announced.

### 4.4 Selection and the publication panel

Click a thread, or press Enter on a focused thread in the twin, or land on `?pub=N`:

1. Write the state texture: selected thread highlight 255, flags bit 0; all others unchanged. Selection does **not** dim the rest of the cloth — dimming is reserved for tours, so the two reads never get confused.
2. Ease the camera to frame the thread's full span over 700 ms (instant under reduced motion).
3. Open `<aside id="woven-panel" role="dialog" aria-modal="false" aria-labelledby="woven-panel-title">` — 420 px, full height, sliding from the right, `.surface-cloth` on walnut-700.
4. Move focus to the panel's `<h2>`.
5. `history.replaceState(null, '', '?pub=' + id)`.

The panel is not modal. The reader can keep orbiting with the panel open; that is the whole point of putting the record next to the cloth. Escape closes it and returns focus to the canvas, or to the twin item if that is where focus came from.

Panel content, in this order: name; alternate name; city and years; end-state line ("still publishing" / "ceased 1993" / "end date unrecorded"); publisher; format, frequency, medium, languages; mission; historical notes; **"evidence we hold"** rendered with the exact `.evidence-card` component and the three rights variants from the design direction, including the `metadata_only` shelf-label treatment between two `.rail-wood` bars; "part of these threads" story links; and a link out to `publication.html?id=N` labelled "open the full record".

Clicking a knot opens the same panel in event mode: title, date, description, confidence, people, source files, and a link to each related publication.

### 4.5 Tour controls

A fixed bar at the bottom of the stage, `.surface-cloth` on walnut-800 under a `.rail-wood` top edge. Real buttons, all of them:

```
[⏸ pause]  [← previous]  [next →]   stop 3 of 9 · 1938   [exit tour]
```

Plus a non-interactive progress rail — 9 stitch marks, the current one filled `stain` — and the tour title in mono. The rail is `aria-hidden`; the counter text is the accessible version.

Autoplay: 3200 ms dwell at each stop, 1600 ms transit. Pause stops the clock, not the camera damping. Previous/next jump immediately and cancel autoplay (a reader who steers has taken control; do not snatch it back).

**Reduced motion** (`prefers-reduced-motion: reduce`, checked live via `matchMedia().addEventListener('change')`):

- The scroll intro does not run; the cloth starts fully woven at `uWeaveProgress = 1`.
- Camera transitions are cuts, not eases.
- Tours never autoplay. The play button is replaced by "next stop"; the reader advances every stop by hand.
- Knots do not pulse; panels do not sag or unfurl, they appear.
- The ghost sequence becomes a single state change plus the full name list, with no camera move and no timed reveal.

### 4.6 The ghost cloth moment

**Trigger.** Three routes, all explicit. A labelled button in the top bar, "show what did not survive". The key `G` with the canvas focused. The deep link `?ghost=1`. It is also *offered* at the end of any tour as a link in the closing card, never started automatically. Nobody gets ambushed by a memorial.

**Sequence** (total ≈ 42 s, skippable at every moment):

| t | Action |
|---|---|
| 0 | The intro card fades in over the cloth: the ghost copy from section 7. Live region announces the same text. |
| 0–900 ms | All non-ghost threads dim to 12% alpha via the state texture G channel. |
| 400–1800 ms | Camera eases to `fitToBox(clothBox, 0.02)` — the widest view in the piece. |
| 1800–2400 ms | Ghost threads raise from 0.28 to 0.62 alpha (B channel), and `uFrayCut` animates 0.0 → 0.35 so the fraying visibly eats in rather than being pre-baked. |
| 2400 → end | Names appear in a left-hand DOM list, six at a time, 2400 ms per group. Each group's six threads flare highlight to 180 for the group's duration. 98 names / 6 ≈ 17 groups ≈ 41 s. |
| end | The closing card: "That is what the record lost." and two buttons — "return to the weave" and "read the list again". |

**Exit.** Escape, the "return to the weave" button, or any orbit/zoom input. All threads restore over 700 ms; the camera returns to wherever the reader was before the sequence, not to the default. The name list stays in the DOM, collapsed, under a disclosure labelled "the 98 catalog-only titles".

**Every name must match `source-catalog.json` exactly** — issue #52's done-condition. Render `publication.name` verbatim, no title-casing, no truncation, no ellipsis. If a name overflows its line, it wraps.

---

## 5. Story mode

### 5.1 Deriving the tour data

No new data file. `data.js` builds the 13 tours at load from `stories.json`, `events.json`, and the thread model.

**Date parsing.** `events.json` dates come in three shapes: `"1843"`, `"1881-05"`, `"1888-12-11"`.

```js
function fractionalYear(d) {
  const m = /^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/.exec(d);
  if (!m) return { year: null, precision: 'none' };
  const y = +m[1], mo = m[2] ? +m[2] : null, da = m[3] ? +m[3] : null;
  const frac = y + ((mo ?? 6.5) - 1) / 12 + ((da ?? 15) - 1) / 365;
  return { year: y, value: frac,
           precision: da ? 'day' : mo ? 'month' : 'year' };
}
```

A year-only date resolves to mid-year, which is a placement convenience and nothing more. It must never be displayed as a month. The overlay prints the raw `date` string, always.

**Tour shape:**

```js
{
  id: 'story-005',
  title: 'Two Newark weeklies become one',
  era: '1930s-1940s',
  strength: null,                 // 'weak' on story-013
  threadIds: [9, 16, 24],
  bandRange: ['C', 'C'],
  stops: [ /* Stop */ ],
  thread: '…full narrative text…'
}
```

```js
// Stop
{
  kind: 'open' | 'event' | 'transit' | 'close',
  eventId: 'evt-031' | null,
  dateLabel: '1938-06-11',
  target: Vector3,               // look-at point
  distance: 14,
  threadId: 16 | null,
  clipping: { webPath, altText, citation, caption, rightsStatus } | null,
  caption: '…',
  confidence: 'high' | 'medium'
}
```

**Building the stops:**

1. **Open.** Target = centre of the union bbox of the tour's threads across the story's full date span. Distance = `fitToBox(bbox, 0.15)`.
2. **One event stop per `eventId`**, sorted by `fractionalYear().value` ascending, ties broken by event id.
   - Target x = `x(fractionalYear.value)`.
   - Target y = `slotY` of the primary thread. Primary thread = the first id in `event.publicationIds` that is also in `story.publicationIds`; if none intersect, the first id in `event.publicationIds`; if the event has no ids at all, the mean y of the tour's threads, and the knot renders on the context tick with a dashed stitch down to that y.
   - Distance = 14, or 22 when the stop touches more than one of the tour's threads.
3. **Transit stops** — see 5.3.
4. **Close.** Target = the open stop's target. Distance = the open stop's distance × 1.1. Carries the closing card.

Verification, and it is ticket T4's done-condition: every string the overlay shows during a tour comes from `stories.json` (`title`, `thread`), `events.json` (`title`, `description`, `date`, `people`), `publications.json` (`name`, `city`, years), or `clippings.json` (`caption`, `citation`, `altText`). Nothing is composed, paraphrased, or invented in JavaScript. The only generated strings in the whole tour are the stop counter and the era label.

### 5.2 Playback and dimming

On tour start:

1. Write the state texture in one pass — tour threads: highlight 200, dim 0, flags bit 2. Every other thread: dim 217 (0.85), highlight 0. Knots: tour event knots scale 1.35 and take `stain`; all others drop instance colour toward walnut-700 and scale to 0.6.
2. `history.replaceState(null, '', '?story=' + id)`.
3. Announce in the live region, then move to the open stop.

Camera motion between stops uses two `CatmullRomCurve3` curves — one through the stop targets, one through the derived camera positions — sampled with `easeInOutCubic` over the leg duration. Curves, not lerps, because a straight cut between two stops eight world units apart looks like a jump-cut and a curve looks like a hand moving across cloth. Curve tension 0.4, `curveType: 'centripetal'` to stop overshoot on tightly clustered stops (story-006 has 9 events inside band C).

On exit: restore the state texture over 500 ms, drop the URL parameter, return the camera to the pre-tour framing.

### 5.3 Stories that span eras

Two of the thirteen span wide ranges — story-010 (1870s–1970s, threads in bands A and E) and story-012 (1930s–1990s, threads in bands C, E, and F). At tour-stop distance 14 the reader cannot see both bands, so a direct move between them destroys the reader's sense of place.

**The transit rule.** If consecutive stops sit in different era bands, insert a transit stop between them:

- Target = the midpoint of the two stops' targets.
- Distance = `fitToBox(union of the two bands' boxes, 0.10)`, so both bands are on screen at once.
- Duration 900 ms in, 600 ms hold, 900 ms out.
- The era label in the overlay changes at the hold, and the live region announces "moving from 1880 to 1899, down to 1970 to 1989."
- Under reduced motion the transit is a cut and the announcement still fires.

Also: the overlay always shows the current band label in mono along the top rail ("1930–1949"), and it updates on every stop, not just on transits. A reader should never have to guess where in the century they are.

### 5.4 Clipping panels

A panel appears at a stop only when **all** of these hold: the stop's event resolves to a `clippings.json` entry; the entry has a non-empty `webPath`; the entry has a non-empty `altText`; and `rightsStatus` is `publishable`, `publishable_with_credit`, or `crop_first`. Otherwise the stop shows a citation-only card in the overlay and no canvas panel. Given the data — 107 of 182 evidence entries are `metadata_only` — the citation-only stop is the normal case. Build it first and make it look deliberate, exactly as the design direction requires of the `metadata_only` card.

**`clippings.json` — the shape Woven expects** (issue #54 owns the file):

```json
{
  "clippings": [
    {
      "publicationId": 16,
      "eventId": "evt-031",
      "sourceFile": "NewarkHerald19380611a.json",
      "webPath": "images/evidence/newark-herald-1938-06-11-p1.jpg",
      "width": 1024, "height": 1420,
      "rightsStatus": "crop_first",
      "citation": "Newark Herald, 1938-06-11, p. 1.",
      "caption": "…",
      "altText": "…"
    }
  ],
  "metadata": { "totalCount": 0, "generated": "" }
}
```

Woven must load this file with `.catch(() => ({ clippings: [] }))`. If it does not exist yet, every tour still plays; every stop is simply citation-only. Do not block the page on it.

**Panel geometry.** `PlaneGeometry(w, h, 8, 6)` sized to the clipping's aspect at a 4.5-unit height, positioned at `z = +3.0` and offset 5 units to the camera's right of the stop target so it never covers the knot it is about. Billboarded on the Y axis only — it rotates to face the camera in plan but keeps its top edge horizontal, because a panel that tilts with the camera reads as a UI element and a panel that stays level reads as hanging cloth.

Vertex shader sag: a shallow catenary in Y plus a 0.02-amplitude ripple, `z += 0.06 * (1.0 - pow(2.0 * uv.x - 1.0, 2.0)) + 0.02 * sin(uv.x * 9.0 + uTime * 0.6)`. That is the only continuously animating thing in the scene, and the adaptive degrade turns it off first.

Material: `MeshBasicMaterial({ map, transparent: true })`. **Unlit, untinted, unfiltered.** No lambert term, no vertex colour, no tone curve, no vignette. The design direction's rule is absolute — we style the furniture, never the document. If the panel looks flat against a lit scene, that is correct; the evidence is not part of the furniture.

`crop_first` gets a 1px `stain` frame as a separate `LineSegments` box inset 0.04 units, plus the mono label "clip" in the HTML overlay and the line "Cropped detail. Full page not reproduced." Every other status gets no frame at all.

Unfurl: `scale.y` 0 → 1 over 500 ms with a slight overshoot settle. Only one panel visible at a time; the previous fades over 300 ms while the next unfurls.

### 5.5 Caption and citation rendering

**All text lives in the DOM. Nothing is drawn into the canvas — not a caption, not a year, not a name.** No `CSS2DRenderer`, no sprite text, no canvas textures of type. This is not a stylistic preference: in-canvas text cannot be selected, cannot be found by browser search, cannot be read by a screen reader, cannot be zoomed by the OS, and cannot be copied by a researcher who needs the citation.

The stop overlay is a `<figure>` in `#woven-overlay`, positioned by projecting the panel's world position to screen space each frame the camera moves, then clamped to a 24 px viewport inset. It carries:

- `<figcaption>` — the caption, DM Sans 15px linen-100
- `<cite>` — the citation, mono 11px linen-300, selectable, never truncated
- The provenance line — source, date, and "view at source" with `target="_blank" rel="noopener noreferrer"` when a URL exists
- The rights label — mono 11px `stain`, paired with the frame so colour is never the only cue

These use the exact `.evidence-card` classes from the design direction so the rights rules cannot drift between the detail page and Woven.

Below the overlay, a fixed narrative card carries the event title (Fraunces 24px) and description (DM Sans 16px/1.6), plus a "medium confidence" mono label and the conflict note where one applies. The story's full `thread` text is shown at the open stop and again in the closing card, and it is always present in the twin.

### 5.6 story-013

`strength: "weak"`. Its tour is available and complete, but: the tour card in the menu carries a mono "thinly sourced" label; the opening stop's card repeats it in a sentence — "This thread rests on two cover artifacts and one dated clipping. Read it as a lead, not a finding."; and it is excluded from the "start a tour" default suggestion. This mirrors the design direction's requirement for `stories.html` exactly.

---

## 6. The accessibility twin

### 6.1 Structure

The twin is not a summary and not a caption. It is the same archive in a form that does not need a GPU or a pointer. It exists in the DOM at all times, whether or not WebGL works, and it is one `syncTwin(state)` call behind the canvas at all times.

```html
<div id="woven-twin" role="region" aria-labelledby="woven-twin-h">
  <h2 id="woven-twin-h">The weave, as a list</h2>
  <p id="woven-help">138 publications, 1880 to 2026, grouped by the decade each one began…</p>

  <ol class="era-bands">
    <li class="era-band" id="band-C" aria-labelledby="band-C-h">
      <h3 id="band-C-h">1930 to 1949 — 17 publications</h3>
      <ol class="threads">
        <li id="thread-16" data-pub="16" data-state="ceased">
          <button type="button" aria-expanded="false" aria-controls="thread-16-detail">
            <span class="t-name">The New Jersey Herald News</span>
            <span class="t-place">Newark</span>
            <span class="t-years">1938 to 1948</span>
            <span class="t-evidence">10 items of evidence</span>
            <span class="t-state">ceased 1948</span>
          </button>
          <div id="thread-16-detail" hidden>
            <ol class="events"> … one <li> per knot, date + title + confidence … </ol>
            <ul class="stories"> … links to each story containing this title … </ul>
            <a href="publication.html?id=16">Open the full record</a>
          </div>
        </li>
      </ol>
    </li>
  </ol>

  <section id="woven-twin-tours" aria-labelledby="tours-h">
    <h3 id="tours-h">Guided threads</h3>
    <ol> … 13 <li> each with a "play" button and a "read as text" disclosure … </ol>
  </section>

  <section id="woven-twin-ghost" aria-labelledby="ghost-h">
    <h3 id="ghost-h">Titles that survive only as a catalog entry</h3>
    <p>…the ghost copy…</p>
    <ol> … 98 <li>, each name, city, years, and the catalog citation … </ol>
  </section>
</div>
```

`.t-state` carries one of three exact strings and they are the twin's version of the three end treatments: `still publishing`, `ceased 1948`, `end date unrecorded`.

Ghost threads get `data-ghost="true"` on the `<li>` and the evidence line reads `catalog entry only`.

### 6.2 Syncing

One direction of truth: the state object. Both the canvas and the twin are renderers of it.

- Selection → `aria-current="true"` on the selected `<li>`, removed from all others, and `scrollIntoView({ block: 'nearest' })` if the twin is visible.
- Hover → `data-hover="true"` only. Hover **never** moves DOM focus and never announces. Pointer hover stealing focus is the classic way to break a screen-reader user's place.
- Tour start → the tour's `<li>` gets `aria-current="step"`; the threads in the tour get `data-in-tour="true"`.
- Tour stop change → the matching event `<li>` inside the thread detail gets `aria-current="step"`, and the detail is expanded if collapsed.
- Ghost sequence → the ghost section is expanded and the current group's six items get `aria-current="true"`.

Never disable, hide, or `aria-hidden` twin content because the canvas is doing something. The twin is always complete.

### 6.3 Focus order and live region

Tab order: skip link → header nav → top bar controls (about, guided threads, show what did not survive, reset view) → canvas → tour bar (when a tour runs) → panel (when open) → twin → footer.

The canvas is `tabindex="0"`, `role="application"`, `aria-describedby="woven-help"`, and it gets a 2px `stain` focus ring at 2px offset drawn in CSS on the canvas element. `role="application"` is used deliberately and narrowly: it is what lets the arrow keys drive the weave rather than the reader's virtual cursor, and it is safe here only because the twin below provides a full document-mode equivalent. Do not put `role="application"` on anything else.

```html
<div id="woven-live" aria-live="polite" aria-atomic="true" class="sr-only"></div>
<div id="woven-live-assertive" aria-live="assertive" class="sr-only"></div>
```

Polite announces: selection changes; tour start ("Guided thread: two Newark weeklies become one. Five stops, 1930 to 1949."); each stop ("Stop 2 of 5. 1938. The Newark Herald folds. The New Jersey Herald News. Medium confidence."); era transits; ghost groups (the six names). Assertive is used for exactly two things: the WebGL failure banner and the adaptive-degrade notice.

Throttle announcements to one per 800 ms and drop, not queue, anything faster. A tour on autoplay must not flood the buffer.

### 6.4 Keyboard map

With the canvas focused. Every one of these also has a visible control; the keys are shortcuts, never the only route.

| Key | Action |
|---|---|
| ↑ / ↓ | previous / next thread in the band; wraps into the adjacent band at the edges |
| ← / → | previous / next event knot on the current thread; with no knots, moves ±5 years along it and announces the year |
| Page Up / Page Down | previous / next era band, landing on its first thread |
| Home / End | first / last thread in the archive |
| Enter or Space | open the panel for the focused thread or knot |
| Escape | close the panel, then exit the tour, then leave the ghost sequence — in that order, one per press |
| T | open the guided-threads menu |
| G | run the ghost cloth sequence |
| + / − | zoom one step |
| 0 | reset the view |
| ? | show the keyboard help card |

With the tour bar focused: Space toggles play/pause, ← / → step stops, Escape exits.

Arrow keys inside the twin are the browser's, untouched. The twin is a document, not an application.

Keyboard navigation moves the camera. Every ↑/↓/←/→ eases the camera to keep the focused thread or knot centred, over 250 ms, instant under reduced motion. A sighted keyboard user must see what a screen-reader user hears.

### 6.5 The no-GPU route

Covered in 1.3. The done-condition for #53 is stronger than "it renders": complete an entire tour, open five publication panels, and run the ghost sequence to the end, using only the keyboard, with the canvas removed from the DOM. If any step needs the canvas, the twin is incomplete.

---

## 7. Copy

Every string below is final. Sentence case throughout. Counts in braces are interpolated from the data at load — never hardcoded.

### 7.1 Page intro

> **A hundred and forty-six years, woven once**
>
> Every cross thread here is one publication, starting the year it was founded and ending the year it stopped. The thicker the thread, the more of that paper we have actually found and can show you. The threads that run past the edge of the loom belong to the {19} papers still publishing today. The thin, fraying ones belong to the {98} we know only from a line in a librarian's catalog.

### 7.2 Ghost cloth introduction

Shown as the opening card of the sequence and as the standing text above the twin's ghost section.

> **What did not survive**
>
> {98} of these papers exist now as a single line in a catalog — a title, a city, a range of years, recorded by a librarian who held the issue we cannot find. No page, no masthead, no photograph. They are woven into the same cloth as everything else, thin and unfinished, because an absence in the record is not an absence in the history. Their names follow.

Closing card:

> That is what the record lost. It is not the same as what happened.

### 7.3 UI labels

**Top bar**

- About this weave
- Guided threads
- Show what did not survive
- Reset the view
- Read the archive as a list

**Hover tooltip**

- `{name}` / `{city} · {yearFounded}–{end}` / `{n} items of evidence`
- catalog entry only
- still publishing
- end date unrecorded

**Publication panel**

- Open the full record
- Evidence we hold
- Part of these threads
- Nothing survives but the catalog entry
- Close

**Tour bar**

- Play the thread
- Pause
- Previous stop
- Next stop
- Stop {n} of {total}
- Exit this thread
- Thinly sourced
- Medium confidence
- Unsettled

**Tour cards**

- Read this thread as text
- Publications in this thread
- Where this thread goes next
- Cropped detail. Full page not reproduced.
- The source is a printed bibliography. We quote it; we do not reproduce the page.
- This thread rests on two cover artifacts and one dated clipping. Read it as a lead, not a finding.

**Ghost sequence**

- Return to the weave
- Read the list again
- The {98} catalog-only titles

**System messages**

- Your browser cannot draw the weave, so here it is as a list.
- The drawing stopped. Here is the same archive as a list.
- The weave is drawn with JavaScript. The same 138 publications, their dates, and their evidence are on the archive page.
- Simplified the drawing to keep it smooth.

**Twin**

- The weave, as a list
- 138 publications, 1880 to 2026, grouped by the decade each one began. Open any title for its evidence and its events.
- Guided threads
- Titles that survive only as a catalog entry
- Skip the weave, read the archive as a list

**Keyboard help card**

- Moving through the weave
- Up and down — move between publications
- Left and right — move between events on this publication
- Page up and page down — move between decades
- Enter — open this publication
- Escape — go back
- T — guided threads · G — what did not survive · 0 — reset the view

---

## 8. Build order

Six tickets. Each is one agent-session. Each ships on its own and leaves the page working. Do not start a ticket before the previous one merges, except T4 and T5, which may run in parallel once T3 is in.

### T1 — Page shell, vendored three.js, data adapter, twin skeleton

Maps to the setup half of #50 and #53.

Create `woven.html` with the copied head block, the import map, the intro copy, the stage, and the `<noscript>` block. Vendor `three@0.171.0` and `OrbitControls` with recorded sha384 hashes and `VENDOR.md`. Write `data.js`: fetch the four JSON files in parallel, tolerate a missing `clippings.json`, and derive the thread model — era band, slot, x-range, width, end state, ghost flag, era dye, plus the event index and the 13 tour objects. Write `layout.js` with the constants and the `slotAtY` binary search. Write `twin.js` far enough to render the eight era bands and 138 thread items with their five spans, plus the skip link and the live-region elements. Write `fallback.js` and the `hasWebGL` gate. Render nothing in the canvas yet.

**Done when:** `woven.html` loads with no console errors; the twin lists all 138 titles in eight bands with correct years, evidence counts, and end states; `?nogl=1` shows the fallback banner and a fully usable twin; the derived counts printed to the console are 138 threads / 19 still publishing / 42 ceased / 77 end unrecorded / 98 ghost / 81 events / 13 tours; and `VENDOR.md` hashes match the committed files.

### T2 — The loom scene

Maps to #50.

`cloth.js`, `shaders.js`, `loom.js`, `knots.js`, `main.js` render loop. Build the merged weft geometry with all six vertex attributes and the three end treatments, both warp meshes with the distance swap, the loom frame and lights, and the two knot instanced meshes. Implement the cloth shader including the round-thread fake, the era dye, the ghost fray, the unknown-end fade, and `uWeaveProgress`. Implement the thread state texture and its write API. Implement the gated render loop, the DPR cap, and the resize handler. Implement the scroll-driven intro: sticky stage, four scroll steps, scroll progress → `uWeaveProgress`, skipped entirely under reduced motion.

**Done when:** all 138 threads, 147 warp threads, 81 knots, and the frame render; the three end treatments are visually distinct at default framing; ghost threads read as frayed and translucent; a 60-frame median frame time under 12 ms at default framing and under 16 ms at `minDistance` on the reference laptop; draw calls ≤ 9 idle (log `renderer.info.render.calls`); the idle render loop issues zero draws; and the scroll intro assembles the cloth left to right and lands at 1.0.

### T3 — Interaction, panel, deep links

Maps to the rest of #50.

`picking.js`, `panel.js`, plus the OrbitControls bounds and pan clamp. Analytic thread picking, instanced knot raycast, rAF-throttled hover, the tooltip, selection through the state texture, the camera ease, the publication and event panel with the three `.evidence-card` rights variants, the `?pub=N` deep link both ways, and the `+`/`−`/`0` keys. Wire twin selection to canvas selection in both directions.

**Done when:** hovering any thread, including a 0.030-wide one, shows the correct tooltip; clicking opens the correct panel; `?pub=16` deep-links, frames, selects, and focuses; Escape closes and restores focus; the camera cannot be rotated past the bounds or panned off the cloth; a `metadata_only` publication's panel shows the shelf-label card between two wood rails and no image; and every panel image with a missing `altText` is skipped rather than rendered with an empty alt.

### T4 — Story mode

Maps to #51.

`tour.js`. Keyframe derivation from `stories.json` and `events.json`, the two Catmull-Rom curves, the transit rule for era-spanning stories, tour dimming through the state texture, the tour bar with real buttons, clipping panel geometry with the sag shader and the LRU texture cache, the projected HTML overlay with `<figure>`/`<figcaption>`/`<cite>`, the citation-only stop, the `crop_first` frame and label, `?story=N` both ways, the story-013 treatment, and reduced-motion behaviour.

**Done when:** all 13 tours play start to finish with no console errors; every stop's overlay text traces to a field in `stories.json`, `events.json`, `publications.json`, or `clippings.json` (list the field for each stop in the PR); story-010 and story-012 insert transit stops at every band change; a stop with no cleared image shows the citation-only card and never a placeholder; resident panel textures never exceed four; story-013 carries "thinly sourced" in two places and does not autoplay; and with `prefers-reduced-motion` on, no tour autoplays and every camera move is a cut.

### T5 — The ghost cloth

Maps to #52.

`ghost.js`. The three triggers, the five-phase sequence, the group-of-six name reveal synchronised to thread flares, the DOM name list, the exit and restore, and the reduced-motion path. **First job of this ticket: reconcile the ghost count.** The rule in this spec yields 98 against the current data; issue #52 says 93. Check both against `source-catalog.json` and `rights-manifest.json`, decide which is right, and fix the rule or the issue. Do not ship a number nobody has checked.

**Done when:** the sequence runs from all three triggers; every name in the list matches `publications.json` and `source-catalog.json` character for character; the sequence is interruptible at any moment and restores the reader's previous camera, not the default; the count in the copy is computed at load; under reduced motion the whole thing is one state change plus the full list; and the count discrepancy is resolved in writing in the PR.

### T6 — Accessibility twin, fallback, and the performance gate

Maps to the rest of #53.

Complete `twin.js`: thread detail disclosures with events and story links, the tours section with play buttons and text disclosures, the ghost section, full `syncTwin` coverage of selection / hover / tour / ghost, the live regions with the 800 ms throttle, the full keyboard map with camera-follow, and the keyboard help card. Complete the fallback: context-loss handling, the two banners, and the `?nogl=1` and `?twin=1` routes. Implement the adaptive degrade ladder and its notice. Run the performance gate and record the numbers.

**Done when:** a full tour, five publication panels, and the complete ghost sequence are all reachable using only the keyboard with the canvas removed from the DOM; every announcement fires once and only once during an autoplaying tour; no interactive element anywhere sets `outline: none` without a replacement; every text and label pair in the overlay, panel, tour bar, and twin measures at least 4.5:1 against its ground; hover never moves focus; and the reference-laptop numbers for frame time, draw calls, triangle count, and texture memory are recorded in the PR against the ceilings in section 3.

---

## 9. What not to do

Six failure modes specific to this piece. Each is a way Woven stops being a finding aid.

Do not draw text into the canvas. Not a year, not a name, not a caption. Every string in this piece lives in the DOM where it can be selected, searched, zoomed, copied, and read aloud.

Do not smooth the distribution. 51 of 138 publications began in the 1970s and 1980s, 26 of 81 events sit in the 1930s, and 118 of 137 evidence-bearing titles carry exactly one item. The cloth will be lumpy and thin in places. That is the archive. Any layout that evens it out is lying.

Do not treat "we do not know when it ended" as "it is still going". 77 titles are in that state against 19 that are genuinely still publishing. If those two ever render alike, the piece overstates the survival of the Black press in New Jersey by a factor of four.

Do not tint, warm, filter, or light the clipping panels. The furniture is warm; the evidence stays neutral and unlit. This is the same line the design direction draws, and it is the line between a finding aid and a nostalgia object.

Do not let the weave become the only route. The twin is not a compliance artifact bolted on at T6 — it is built in T1, before a single triangle renders, and every ticket after it keeps it complete.

Do not add a second visual language. No particle systems, no bloom, no depth of field, no lens flare, no vignette, no ambient dust motes, no soundtrack. The scene has two materials and one accent, and that is the whole vocabulary.
