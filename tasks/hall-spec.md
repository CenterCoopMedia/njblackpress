# Specification: the hall

Status: proposed revision for Joe's review, not an implementation report.  
Date: September 9, 2026.  
Basis: Claude's `hallspec.md`, dated September 9, 2026. This revision keeps its 14-section structure and its hall, sheet, volume, rail, and reader terminology.

## How to read this revision

The source draft supplies the project intent and compatibility requirements. The requirements below are proposed changes or retained requirements, not claims that the repository already implements them. The repository, dataset, rights records, installed Three.js version, and issues 58 and 72 were not inspected for this review. Their current details must be checked before implementation. External implementation references are listed at the end.

The main changes are deliberate: chronological galleries replace a fixed distance-per-year rule; an explicit state model replaces implicit camera behavior; the DOM reader remains usable independently of the scene; and layout, memory, interaction, and fallback behavior become acceptance requirements. Numerical performance budgets below are starting targets for measurement, not measured results or universal device limits.

## 1. Purpose

Replace the 3D timeline on `historical-notes.html` with a walk through a hall of New Jersey's Black press. Each publication is a framed sheet. Each guided story is a bound volume that opens at a reading table. The hall is an editorial exhibition, not a reconstruction of a documented historical building.

The visitor must be able to understand where they are, find a publication, inspect its available evidence, read a guided story, and return to their previous position without learning game controls.

The flat timeline, Canvas 2D fallback, text archive, existing record content, search, filters, and supported deep links remain available. Preserving them means preserving their content and behavior, not merely retaining their buttons.

### Experience contract

The first settled view shows a readable decade marker, identifiable publications, and a clear route to a guided story. It does not require a camera tour, hover discovery, or an instruction modal. Provide a short instruction in ordinary page text: “Choose a publication, open a guided story, or move to another decade.”

Keep Hall, Timeline, and Text archive controls visible outside the canvas. Include search, the publication index, the guided stories picker, and decade navigation in the normal interface. A visitor may bypass the spatial experience at any point without losing the selected publication or story.

The hall is the default visual view for a first visit on a supported device. An explicit URL mode or the visitor's current view choice takes precedence. Never force a return to the hall after the visitor has selected another view.

The first delivery must include the hall's material character, spatial depth, distinct reading positions, and volume/page interaction. It must not be delivered as a flat list with a decorative camera effect. Equally, no publication or story may depend on a camera animation completing before its text is available.

## 2. Names

Public name: **The hall**. Entry button: **Walk the hall**. Internal name: `hall`. New modules live in `docs/js/hall/`.

Use publication, sheet, frame, volume, page, section, reading table, and rail in new interface copy and code. Do not introduce textile metaphors.

Preserve old URL aliases, required imports, existing DOM IDs such as `#woven-publications`, and the legacy color-token names where compatibility requires them. Keep the exceptions in a small, documented allowlist. Do not rename the old modules or tokens as a side effect of this work.

The language rule applies to newly authored interface language and identifiers. It must not change publication names, historical quotations, citations, source documents, or legacy compatibility strings.

Use sentence case for interface headings and controls. Preserve the proper capitalization of publication and story titles.

## 3. The space

### Chronology and scale

Time progresses along the z axis from the entrance to the far end. Use the same chronology bounds as the flat timeline. The source draft specifies 1880–2026; read that range from the shared configuration rather than creating a second constant or changing it according to the visitor's clock.

Keep one labeled section per decade, followed by a distinct area for publications whose dates are unrecorded. Its count comes from the data; do not hardcode three titles.

**Replace the fixed rule of 1 year = 1.2 units.** The hall is ordered chronologically but is not a quantitative time scale. Display a brief explanation beside the decade navigator: “Arranged by founding date. Gallery spacing varies.” The flat timeline remains the precise temporal comparison view.

Each decade section receives enough physical length for its publications and reading-table positions. Sparse sections stay compact. Dense sections extend into additional bays within the same labeled decade. Empty decades retain a marker and navigation destination without imposing a long empty walk.

The rail displays the current decade or “Date unrecorded.” It must not derive an apparently exact founding year from an arbitrary camera coordinate. Exact dates belong to the selected record and to any explicitly labeled year controls.

### Deterministic layout

Create the layout from the complete, unfiltered public dataset. Sort dated publications by the existing normalized founding-date value and then stable publication ID. Preserve any uncertainty or date interval in the displayed date; sorting is not permission to invent precision.

Fill paired left and right wall slots at a primary reading height. Same-year titles receive separate physical slots, with their shared date still shown. Determine each section's length from its occupied slots, boundary clearance, and table-bay clearance. Do not cap capacity at three rows or allow overlap as an overflow behavior.

The first implementation uses one primary reading row. A secondary row may be added only after a prototype proves that each frame has a comfortable focus pose and remains discoverable by pointer, keyboard, and index. Do not use high rows to avoid implementing density handling.

Publication frame rectangles, plates, decade markers, and table footprints must have non-overlapping layout bounds. The layout output includes publication slots, section boundaries, book slots, camera anchors, and collision bounds. It must be testable without WebGL.

Date ranges, ambiguous founding dates, dates outside the configured range, and missing values require explicit handling in the data adapter. Preserve the source wording and uncertainty. Do not silently clamp or replace a source date. Report unsupported cases for a data/placement decision while keeping the record available in the DOM.

### Architecture and art direction

Retain the dark walnut floor, pale plaster walls, restrained brass details, existing era colors, Libre Franklin, and DM Sans from the draft. Use the existing token values through a hall-specific configuration layer.

The visual character should come from publication typography, real clippings, the proportion of frames and tables, and light on paper—not invented historical insignia or an all-purpose sepia treatment. Printed matter should be the most visually distinct content in the scene.

Use thin, visibly constructed frames, a small paper inset, subtle contact shading, and low-contrast floor grain. Avoid heavy varnish, dramatic vignettes, particles, fog that conceals nearby labels, glowing frames, or large decorative gradients. These are art-direction requirements, not a request to remove depth or texture.

Create a legible rhythm through decade thresholds, wall breaks, and reading bays. Use existing approved story summaries where contextual text is useful. Do not generate new historical claims to fill an empty wall.

No ceiling mesh is required. The upper walls must terminate or fade deliberately; the opening must not expose unexplained geometry or a distracting black void.

### Lighting

Start with a hemisphere light and a directional light. A subtle traveling fill is optional and must not be necessary to read a selected sheet. Do not create a real point light for every active publication.

Separate architectural shading from reading contrast. A selected sheet and the DOM reader remain readable in every quality tier and at either wall. Color-managed clipping textures must not receive a sepia filter or a warm wash that materially alters the source image. Three.js requires appropriate color-space annotation for color textures [T1].

Dynamic shadows are not a baseline requirement. Establish contact shading through inexpensive materials or geometry first. Add real-time shadows only after a measured visual/performance comparison. Do not list shadows in an adaptive ladder unless the implementation actually has them.

### Tables and camera clearance

Place reading tables in shallow side bays, outside the center travel corridor. A table's decade placement comes from its story metadata. Several volumes in one decade require separate, reachable book slots.

Define the rail corridor, table bounds, frame bounds, and valid camera poses before building decorative geometry. No normal movement or focus transition may pass through a wall, frame, or tabletop. There is no head bob, camera roll, collision bounce, or free-flight navigation.

## 4. Sheets

Each public publication record has one logical sheet and one stable layout slot. “Every publication is a sheet” does not require every sheet's high-resolution texture to be resident in GPU memory at the same time.

Use the draft's 1.4 by 1.9 units as a prototype frame size, not a permanent fit guarantee. The relationship among frame size, gallery width, camera height, and available screen space must be established together.

### Content hierarchy

A sheet shows the publication name first, followed by city and the existing date/status wording. Use the existing era color as a restrained frame accent. Do not encode era or active status by color alone.

Use a real, cleared clipping when available. A typeset publication name is a contemporary exhibit label, not a recreated historical masthead. Do not invent a logo or distress a modern label to make it look like an archival original.

Preserve the date cases in the draft: a known date range; active publication ending in “present”; an unrecorded ending; and “date unrecorded.” Add fixtures for any approximate or interval dates that the actual dataset supports. The normalized display formatter must be shared across scene labels and DOM text.

When no public clipping is available, use a deliberate publication-record design rather than an empty image-shaped hole. Retain the source's careful distinction between unavailable display material and lost newspapers. Suggested copy: “No copies cleared for display here. Copies may survive elsewhere.”

Show the exact required attribution in the DOM whenever a clipping is presented. A brass plate can supplement that attribution, not be its only readable location. “Cropped detail” is a separate explanatory label and never replaces a required credit.

An active publication may have a small, non-flickering lamp-like mark made with a material, plus a textual “Still publishing” label. It must not create a separate scene light.

If evidence counts are shown, count the appropriate public records through the shared data policy, not an unchecked raw array. Use “1 record” and “3 records” correctly. Do not treat record count, clipping availability, or confidence as a score of a publication's historical importance.

### Interaction and selection

Hover and keyboard focus provide a visible frame highlight and a readable DOM label. They do not move the camera, open a panel, or start loading a full clipping. Activation selects the sheet.

Selection opens the existing record content immediately and requests a comfortable camera focus pose. Keep the record panel's content, rights logic, links, and actions. Allow the small integration changes needed for focus, close events, responsive positioning, and shared selection state; “unchanged” must not prevent these contracts from being implemented.

Fit the selected frame into the remaining visible scene rectangle after accounting for the record panel and controls. The draft's fixed distance of 2.6 units is not a universal reading position. Compute the fit from the frame bounds, aspect ratio, projection, and safe margins. Use APIs available in the repository's pinned Three.js version; current documentation describes view-size helpers [T2].

Provide a DOM **View clipping** action that opens a large, flat, credited image with zoom controls. The visitor must not need to read archival body text from a perspective texture.

### Picking and filters

Pick only visible, eligible objects. Decorative walls, empty frame backs, hidden rows, filtered-out sheets, and books behind other objects are not accidental targets.

For touch, provide an approximately 44 by 44 CSS-pixel target where space permits. This is a product target, not a claim about a world-space mesh size. Use visible DOM controls or bounded, occlusion-aware hit regions. When targets would overlap, provide a small disambiguation list rather than assigning the tap unpredictably. W3C's minimum target-size criterion has its own sizes and exceptions [A4].

Filtering does not rebuild or reorder the gallery. Preserve slots; suppress picking of non-matches and distinguish matches without making the whole hall unreadably dark. Show the matching count and a clear-filter action in the DOM. A zero-result state must be explicit.

A deep-linked record outside the current filters remains accessible. Temporarily reveal the selected record and explain the mismatch, or provide an explicit action to clear the filters. Do not silently change the visitor's filters.

## 5. Movement

The hall uses constrained travel with authored focus positions, not unrestricted walking.

### Interaction states

Use one authoritative application state for the active view, filters, rail anchor, selected publication, active story and stop, overlay, return context, motion preference, and quality tier.

| State | Meaning |
|---|---|
| Browse | Travel along the center rail; select publications or volumes. |
| Publication focus | A selected sheet is framed and its record content is open. |
| Story reading | One volume and one story stop are active. Rail movement is suspended. |
| Clipping inspection | A large, flat image is open with its attribution and controls. |

Animation is a transition between states, not the owner of the selected record or story stop. Loading and renderer failure are separate conditions. All controls, search results, deep links, and browser-history events dispatch the same commands.

Before entering focus, reading, or inspection, save the return context: logical position, camera pose, selected item, filters, scroll position where relevant, and DOM focus target. Closing restores it. Return context must handle a story opened from a publication panel and a clipping opened from a story.

### Input contract

| Input | Result |
|---|---|
| Select a sheet or publication button | Open the record and focus its sheet. |
| Select a volume or story button | Open that story and its first or restored stop. |
| Horizontal drag in browse mode | Move along the rail. A movement threshold distinguishes drag from activation. |
| Vertical drag on touch | Preserve page scrolling; do not use it to tilt the camera. |
| Wheel/trackpad | Scroll the page by default. Rail movement is available through an explicit “Use scroll to move” mode, not automatic interception. |
| Previous/Next publication controls | Move to and select the adjacent matching publication in stable order. |
| Previous/Next decade controls | Move to that decade's entry anchor. |
| Decade navigator | Jump directly to a named decade or the undated section. |
| Back to entrance | Close the current reading/focus state and return to the entrance. |
| Escape | Close the topmost inspection/reading/focus state and restore its return context. |
| Tab and Shift+Tab | Follow the normal DOM focus order. |

Keep a visible way to exit wheel-navigation mode. Blur, view switching, and opening a reader end wheel capture. At rail boundaries, do not trap page scrolling. Normalize input deltas and clamp travel speed; a large trackpad gesture must not traverse the entire hall.

Optional Left/Right shortcuts move between publications in the dedicated scene-navigation controls; Shift+Left/Right moves between decades. They apply only in that explicit context and must not intercept inputs, native sliders, text selection, or the reader. All actions remain available through ordinary buttons even when a screen reader reserves arrow keys.

Inside a story, Previous and Next buttons turn pages. Optional Left/Right shortcuts apply only in the reader's page-navigation context, not to arbitrary focused content. Swipe turning is restricted to the book/image area so that text scrolling remains normal. Every drag or swipe action has a non-drag pointer alternative [A2].

Remove the separate “Whole hall” control if it only duplicates “Back to entrance.” A future control named “Hall overview” must actually provide an overview.

### Camera motion

Keep browsing motion level and restrained. Do not turn the camera on hover. A selected object may use a short lateral move and yaw into a validated reading pose; it need not remain on the center rail.

Use short, interruptible transitions for nearby moves. Long jumps and initial deep links go directly to the target rather than flying through many decades. New navigation intent cancels an old camera transition. No command requires the visitor to wait for camera settling before text or controls respond.

The document does not mandate one duration for all movement. Prototype durations with real content, then record the chosen constants in the motion configuration. Prefer a fast start and settled endpoint over elastic or overshooting motion.

Reduced motion means immediate position changes and instant page changes. Do not require the draft's 200 ms fade on every action. A non-spatial opacity transition may be separately optional, but “No animation” must mean no animation. No traveling flicker or autonomous movement is allowed. These requirements implement this product's motion choice; W3C also documents disabling interaction-triggered motion [A3].

## 6. Volumes and the reading table

Every public guided story remains a distinct bound volume. The volumes are contemporary editorial containers for guided stories, not evidence that matching physical historical books exist. Make that distinction in the reader introduction or help text.

Derive placement from the approved story metadata. The source draft's section map—1880s: 001, 002, 003, 010; 1900s: 004; 1930s: 005–009 and 012; 1970s: 011; 1980s: 013—is a migration fixture to verify, not a second runtime source of truth.

A story beginning before 1880 may sit in an entrance reading bay associated with the first section, but its cover and reader keep the actual era wording. Add “Begins before 1880” where needed; do not change the story's date to fit the hall.

Use 0.9 by 1.2 by 0.12 units as initial closed-volume proportions. The cover shows the approved title and era, with a muted era color. The title must remain available as DOM text when the physical cover is too small to read. A spine title is detail, not the only identifying label.

### Opening and reading

Selecting a volume opens the story's DOM reader immediately. The book may lift and open into its reading pose while the text is already usable. Selecting from a deep link bypasses a long table-travel sequence.

Each stop is one spread. The left page displays the approved public clipping, fitted without an additional decorative crop. The right page shows the approved stop title and date. A stop without a clipping uses the date and an intentional text-only treatment, not fabricated historical paper.

The DOM reader contains the full stop text, citation, confidence wording, rights note, required credit, and “Stop 3 of 9” status. It also provides Previous, Next, Close, View clipping, and Copy link controls. Include a simple contents selector so a visitor can go directly to a stop.

Use one source of story state and one source of stop content. The renderer, reader text, source attribution, stop counter, and URL must agree. Full-size public images load only when needed. Preload adjacent public stop images within the asset budget; a failed image must not block the story text or page controls.

### Page turn contract

Retain a tactile page turn. A segmented page surface may bend lightly around the spine. Full paper physics is unnecessary.

For a forward turn from stop i to stop i+1, keep the old left page visible underneath, show the old right page on the turning leaf's front, show the new left page on its back, and reveal the new right page underneath. Reverse this mapping for Previous. Test texture orientation, especially back-face text, plus page thickness/contact and clipping through the cover.

Treat 650 ms from the source draft as an upper prototype value, not a compulsory pause. Page turning must remain responsive under repeated input. Accept the latest requested stop, clamp it to the valid range, cancel stale image loads, and settle to that stop without accumulating a long animation queue. When the target skips several stops, use an immediate update or a short transition rather than simulating every page.

Close works during opening, loading, and page turning. The first and final stops have correct disabled navigation states. The final stop offers a clear return to the hall; it does not wrap unexpectedly.

### Relationship to the hall

While a story is open, the hall may quietly highlight publications explicitly referenced by the current stop. Derive this only from existing record links; do not infer relationships from similar names or proximity. Provide a DOM “Publications in this stop” control when useful.

This relationship cue must not move the camera, add unsupported connections, or require animated lines through the room. It is a way to connect the book to the exhibit, not a separate graph feature.

## 7. Wall copies of clippings

Retain `data/make_wall_copies.py` and `docs/images/evidence/wall/`. The builder reads `docs/data/clippings.json` plus the existing public-rights/asset policy. It uses approved files at `webPath`, never the research corpus or an uncropped original.

The source draft explicitly states that public files are already cropped and cleared. Verify and enforce that assumption in the existing metadata contract. The hall must not make new rights judgments. In particular, a `crop_first` status requires a verified public cropped derivative; an outline or “Cropped detail” label is not a crop operation or a permission grant.

### Derivative contract

Use a 400-pixel target width without upscaling. Also cap the long edge—initial target 1200 pixels—so an extremely tall clipping does not produce an unexpectedly large wall asset. Preserve the complete approved public image and its aspect ratio. Wider/taller details remain available in the reader and image inspector.

JPEG quality 78 is the initial encoding setting, subject to inspection of actual newsprint. Standardize orientation, color conversion, alpha compositing where needed, and encoder settings in a pinned tool environment. Do not impose a blanket higher quality or new format without measuring the result.

Use stable, collision-safe output names derived from clipping ID, with a `.jpg` extension matching the encoded content. Preserve a public basename only when it is already unique and appropriate. “Same file name” must not create a JPEG with a PNG extension or overwrite a different clipping with the same basename.

Write a generated manifest linking clipping ID, public source path, wall path, source hash, output hash, dimensions, encoding configuration, and the public display/credit metadata needed by the application. Do not expose research-only paths or private metadata in the manifest.

The manifest is the application's derivative lookup. Avoid independently guessing wall URLs in several modules.

### Stability and failure

Within the pinned environment, unchanged source bytes and settings produce identical output bytes. A repeat run does not rewrite unchanged files. A changed source, crop, credit requirement, eligibility state, or encoder configuration invalidates the relevant result. Build timestamps must not make deterministic outputs change.

Generate only eligible public clippings. Detect missing files, path collisions, unknown statuses, and unresolved crop requirements. A referenced clipping with an ambiguous public-display state fails validation; do not silently fall back to another source file.

Remove obsolete outputs only within the generated directory and only through the generated manifest. Rights withdrawal must remove the asset from published output and update references/cache policy. Document that rebuilding cannot retract copies already downloaded by visitors; do not claim guaranteed deletion from client caches.

Add the builder and manifest to the generated-files documentation in `CLAUDE.md`.

## 8. Small screens

Support the source draft's 375 by 812 viewport, but do not optimize only for that screenshot. Include 320-pixel-wide layouts, short landscape screens, tablet layouts, dynamic browser chrome, text zoom, and large system font settings.

The browse-stage height is responsive rather than fixed at 62 percent of the viewport. Navigation and an escape to the text archive must remain visible without requiring the visitor to finish a gesture. Touch exploration uses horizontal gestures while preserving vertical page scroll and browser zoom.

A narrower field of view is not the complete mobile solution. Compute camera fit from both dimensions and the space occupied by controls. A selected frame must not be cropped just to make it larger.

### Mobile reading

When a story opens on a small screen, present a full-height DOM reading sheet with a normal vertical content flow: title and stop controls, clipping/book presentation, text, and attribution. Keep Close reachable. Use the dynamic visible height and safe-area space, with an appropriate fallback for browsers that need it.

A compact view of the open book may introduce the stop. It can scroll away or collapse. Do not permanently divide a roughly 503-pixel stage into two roughly 252-pixel regions for book and text. Do not require both regions to remain visible at all times.

Provide explicit “Read text” and “View clipping” actions. The full clipping can open an image inspector; the reader must also work without the 3D book. Zooming the clipping must not require a precise pinch gesture: include ordinary zoom and reset controls.

Keep the controls at comfortable touch sizes and reflow text rather than reducing its font to preserve a fixed composition. W3C's reflow criterion distinguishes two-dimensional content from the surrounding text and interface [A5].

The repository's issue 58 closes only after its actual acceptance criteria are inspected and satisfied. This spec alone does not establish that the issue is resolved.

## 9. Accessibility and fallbacks

### Semantic interface

Preserve the publication index, search, filters, and text archive. Every publication retains a native button in `#woven-publications`. Guided stories and story stops have equivalent DOM navigation, not only canvas hit targets.

Do not retain `role="application"` automatically. Prefer a named section with ordinary HTML controls and a canvas that does not duplicate accessible content. With a complete DOM equivalent, keep the canvas non-focusable and hidden from the accessibility tree; keyboard actions belong to the visible controls.

A narrowly scoped application-role interaction is an alternative only if testing demonstrates a real need and every required content/focus behavior is provided. It must not wrap the reader, publication index, or unrelated page content. WAI-ARIA describes the role's effect on assistive-technology input and its obligations for static content [A1].

A desktop reader may be a labeled non-modal section. An overlay image inspector or modal mobile reading sheet must implement an actual dialog focus model: an accessible name, suitable initial focus, inert background while modal, a visible close action, Escape, and focus restoration. Do not trap focus inside a panel declared non-modal [A6].

Use polite, concise live announcements after a selection, page change, or settled decade transition. Do not announce every animation frame or wheel increment. Announce the actual label and state; “No publications match these filters” must not be reported as an empty archive.

Credit, date uncertainty, and active status must be readable without depending on color, scene lighting, hover, or a very small plate texture. Respect reduced motion at startup and when its setting changes. Test contrast, visible focus, high-contrast/forced-colors behavior of the DOM interface, zoom, and touch targets.

### Fallback policy

| Condition | Behavior |
|---|---|
| `?nogl=1` or `?twin=1` | Open the text archive and requested content without fetching or evaluating Three.js. |
| No usable WebGL at initial load | Open the existing Canvas 2D timeline, with the selected record/story in the DOM. Promote text if Canvas 2D is also unavailable. Explain the hall's unavailability. |
| Hall renderer initialization fails | Keep the DOM interface and requested content usable; offer the supported fallback view. |
| WebGL context is lost during use | Stop rendering, preserve selection/story/stop/filter state, and promote the text archive with that content. |
| One image fails | Show its metadata and an explicit image-unavailable message; retain reader navigation. |
| Font loading fails | Use the approved fallback font and repaint labels as needed; do not block entry. |
| Scene is offscreen or document hidden | Stop the animation loop; retain logical state. |

Do not automatically restore WebGL after a context-loss fallback while the visitor is reading. A user-triggered retry may reconstruct the scene from logical state. Avoid a loop of failed restoration attempts.

Decide forced-text mode before importing any module that imports Three.js, including indirect imports. Test network requests as well as the visible result. A renderer hidden by CSS is not a no-WebGL fallback.

The DOM story reader, its controls, and its URL parsing must work independently of `volumes.js` and renderer initialization.

### Rendering and resource ownership

Use invalidation-driven rendering. Request a frame on input, camera transition, page animation, texture/font completion, resize, selection/filter change, or quality change. Continue requesting frames only while a finite animation is active. Do not maintain an idle frame loop that merely decides to skip drawing.

Load nearby texture detail within a bounded working set. Prioritize selected objects, visible objects, and a small amount of upcoming content. Distant sheets keep lightweight geometry or lower-detail representations. Visibility culling alone is not the asset-lifetime policy.

Reuse geometry and materials where appropriate. Repeated frame geometry is a candidate for section-level instancing; unique clipping faces need a separate texture strategy. Do not assume one `InstancedMesh` removes the cost of different materials or textures. The documented class is intended for shared geometry/material combinations [T3].

Manage wall copies, label canvases, book covers, page textures, decoded images, render targets, event handlers, observers, and requests through explicit ownership. On eviction or disposal, release the resources no longer shared. Three.js provides explicit GPU texture disposal [T1]. An object removed from the scene is not an ownership policy.

Use generation tokens or cancellation for asynchronous work. An image that finishes loading after the visitor changes story or exits the hall must not update the new view, restart an idle loop, or recreate disposed resources.

### Initial budgets and measurement

These are proposed starting budgets for the hall's own working set. Record the actual reference devices, browsers, viewport, device pixel ratio, and baseline before accepting or adjusting them.

| Metric | Initial target |
|---|---|
| Moving-frame performance, standard tier | Aim for 60 fps; investigate p95 frame intervals above 20 ms on the recorded reference desktop. |
| Moving-frame performance, simplified tier | Aim for 30 fps; investigate p95 frame intervals above 33.3 ms on the recorded reference mobile device. |
| Visible input feedback | Under 100 ms for controls when the required data is already loaded. |
| Hall-owned resident texture estimate | At most 128 MiB standard; 64 MiB simplified, including active page textures. |
| Incremental first-scene image transfer | At most 1.5 MiB before optional prefetch and full-image inspection. Measure shared library/font bytes separately and also report the total. |
| Fully settled, visible scene | No continuing animation-frame requests until invalidated. |
| Hidden/offscreen scene | No ongoing rendering or unnecessary prefetch. |
| Repeated view/story cycles | No monotonic growth in owned textures, geometry, listeners, or pending work after caches settle. |

Estimate texture bytes from dimensions, format, mip levels, and copies; compressed network size is a different metric. For context, a 512 by 704 RGBA8 texture is 1.375 MiB before mipmaps, or approximately 1.83 MiB with a full mip chain. One hundred such faces would be about 183 MiB before other scene resources. This is a calculation under stated assumptions, not a measurement of this application.

Use named standard and simplified tiers. Lower the device pixel ratio and resident detail first, then remove optional fill/shadows or page deformation if present. Preserve the selected image's useful reading presentation and all DOM content. Avoid rapid quality oscillation: evaluate sustained movement samples, ignore idle intervals, and apply hysteresis. A visible “Simplified view” control explains the current setting and allows a stable user choice.

Do not add a new rendering framework, post-processing stack, compression pipeline, physics engine, or dependency merely because it might help. Profile first and use the pinned Three.js version unless a separate, justified change is approved.

## 10. Deep links

Preserve every route in the source draft. Parse routing before loading the renderer. Normalize old forms through one compatibility adapter rather than duplicating parsing in sheets, volumes, and panels.

| Link | Result |
|---|---|
| `?view=3d&pub=ID` | Hall at that sheet, unless forced text/fallback takes precedence. |
| `?view=hall&pub=ID` | Canonical new publication form. |
| `?view=woven` | Legacy alias for the hall. |
| `?view=timeline` | Existing flat timeline. |
| `?id=story-NNN` | Open that story; use the hall unless an explicit supported non-hall view or fallback applies. |
| `?id=ID` | Open that publication with the same mode rules. |
| `?decade=1930s` | Open the 1930s section, or the equivalent fallback destination. |
| `?twin=1`, `?nogl=1` | Text archive, while preserving the requested record/story. |
| `woven.html?...` | Existing forwarding behavior, retaining query parameters and supported fragment state. |

Proposed additive route: `?view=hall&id=story-NNN&stop=STOP_ID` opens a specific stop. Use an existing stable stop ID if one exists. Otherwise introduce a persistent ID mapping as an explicit data-contract change, rather than inventing IDs from mutable array positions. Until that mapping is established, do not emit unsupported stop URLs.

### Precedence and history

Resolve rendering mode separately from content identity. Forced-text flags override every visual mode. Then honor a valid explicit view. Without one, use a compatible current/session choice, then the hall default. Automatic renderer fallback never discards a valid target.

For conflicting target parameters, use the verified existing precedence where defined. For previously undefined conflicts, this proposed rule is: a valid `id` target, then valid `pub`, then valid `decade`. A stop applies only to its selected story. Add tests and document this rule; do not silently change a known legacy behavior.

Invalid IDs, malformed decades, or invalid stops produce a visible explanation and an available index/contents control. Do not throw, produce an empty scene, or silently show an unrelated publication.

Create browser-history entries for deliberate view changes and opening distinct publications/stories. Replace the current entry for continuous rail movement and within-story stop updates so Back is not flooded. Restore state on Back/Forward without creating a new entry. Copy link includes the current publication or story/stop, not transient camera coordinates.

Closing an overlay restores the prior logical state without navigating away from a page entered by a deep link. Do not call `history.back()` blindly when no in-app parent entry exists.

## 11. Files

Retain the draft's proposed modules and add only the separations needed for testability and ownership.

| File | Responsibility |
|---|---|
| `docs/js/hall/hall.js` | Mount/dispose, lifecycle coordination, view integration. |
| `docs/js/hall/state.js` | Commands, authoritative state, return contexts; no Three.js dependency. |
| `docs/js/hall/layout.js` | Data normalization adapter and deterministic slots, sections, bounds, camera anchors; no renderer dependency. Split the adapter later only if warranted. |
| `docs/js/hall/space.js` | Floor, walls, markers, reading bays, lighting. |
| `docs/js/hall/sheets.js` | Sheet instances, detail levels, selection appearance, picking. |
| `docs/js/hall/paint.js` | Textures for labels, plates, covers, and pages; font handling. |
| `docs/js/hall/assets.js` | Manifest lookup, loading priority, cancellation, caches, memory estimates, resource ownership. |
| `docs/js/hall/rail.js` | Camera fitting, constrained travel, input arbitration, motion policy. |
| `docs/js/hall/volumes.js` | Table/book geometry, opening, closing, page rendering. |
| `docs/js/hall/reader.js` | Independent DOM story reader, clipping inspection, responsive/focus behavior; no Three.js dependency. |
| Existing route adapter or `docs/js/hall/links.js` | Canonical URL parsing, aliases, precedence, history; no renderer dependency. Reuse the existing router where possible. |
| `docs/css/hall.css` | Scene controls, reader, modal/mobile layouts, focus and motion styling. |
| `data/make_wall_copies.py` | Approved derivative build and manifest. |
| `scripts/test-hall.mjs` | Pure state, layout, camera-fit, route, and formatting checks. |
| `data/test_hall_assets.py` | Asset eligibility, determinism, hashes, dimensions, updates, removal. |

Use named exports, clear interfaces, and localized state. Keep modules small, but treat 400 lines as a review signal, not a rule to satisfy by compressing code or splitting one cohesive behavior across many files.

### Integration and removal

First inspect `main.js`, `panel.js`, the current exhibit entry point, the timeline/fallback entry points, and the referenced tests. Identify shared imports before removing anything. The file names and removal candidates below come from the source draft, not a current dependency audit.

Remove `exhibit.js`, `exhibit-geometry.js`, `woven-exhibit.css`, and `test-woven-exhibit.mjs` only after their replacements and import paths are verified. Remove the obsolete geometry/state referenced by issue 72 only after confirming it is unused by the retained timeline and fallback paths. Do not delete a file merely because its name is old.

Update `CLAUDE.md`, `WOVEN_REVIEW.md`, and `CODEBASE_OVERVIEW.md`. Preserve legacy documentation filenames where they are part of existing workflows.

### Delivery order

1. Audit current data/contracts and implement the pure layout, state, route, and asset checks. Document actual publication density and story metadata.
2. Build a representative vertical slice: a dense decade, a sparse decade, an undated record, a long title, an unavailable clipping, a credited/cropped public clipping, and one multi-stop volume. Include mobile, reduced motion, and no-WebGL behavior.
3. Review that slice in a browser for art direction, framing, readability, gesture behavior, and page-turn quality. Resolve the spatial decisions before applying them to the full collection.
4. Expand the verified design to all records and stories; complete bounded resource management and compatibility coverage.
5. Run the full review matrix, remove obsolete code, and update documentation. Make the hall the release default only after the gates pass.

The slice is a sequencing tool, not a reduction in final scope. Use stacked reviewable changes where they separate cleanly. Do not mark the project complete after only the slice works.

## 12. Tests and review

Retain the existing relevant tests from the source draft, but inspect their current behavior before replacing assertions. Add executable behavior tests; source-string checks alone do not prove usability.

### Pure tests

Test deterministic placement; non-overlap; same-year capacity beyond six titles; section membership; empty decades; stable layout under filtering; unknown/out-of-range dates; undated access; story/table placement; frame-to-viewport fit; and every supported date/credit case.

Test the state machine under repeated commands, interrupted movement, opening another story during image load, closing during a page turn, and nested return contexts. Confirm that the latest state cannot be overwritten by stale asynchronous work.

Test URL aliases, forced-text precedence, conflicting targets, missing IDs, invalid stops, Back/Forward, direct entry, and stop-link persistence if introduced.

### Asset tests

The expected derivative set equals the eligible public clipping set—not every research or metadata record. Verify source/output hashes, naming uniqueness, correct encoded format, dimension bounds, exact required credits, resolved public crops, missing-source errors, and removal when eligibility changes.

Run the builder twice and compare both content and unchanged-file rewrites. Change one source and confirm only affected outputs change. Test two source files with identical basenames. Test that no path reaches outside the approved public input and generated output locations.

### Browser interaction tests

Use real pointer events to select a sheet, select a nearby book, drag without accidental activation, scroll past the stage, and operate touch-sized controls. Test picking after a resize, panel opening, scrolling, and a device-pixel-ratio change.

Open a volume, move forward/backward, skip through contents, rapidly request several stops, open the credited clipping, close it, and return to the precise originating publication/rail context. Check that image, text, title, stop count, attribution, and URL agree after each settled state.

Test every route in section 10 and verify zero Three.js network requests in forced-text mode. Simulate renderer creation failure, context loss during a turn, image failure, delayed image/font completion after disposal, and repeated Hall/Timeline/Text archive switches.

Test filters with many matches, one match, zero matches, and a deep-linked record outside the filter. Do not validate only the unfiltered hall.

### Accessibility and responsive review

Use keyboard-only navigation, a representative Windows screen-reader/browser combination, and VoiceOver/Safari on an Apple device where available. Record exactly what was tested and what was not. Automated accessibility tools supplement these checks; they do not replace them.

Review 375 by 812, 320-pixel width, short landscape, tablet, and desktop layouts. Test text enlargement and a 320-CSS-pixel reflow condition separately from the image's two-dimensional zoom interface. Confirm modal/non-modal focus behavior, visible focus, Escape, scroll preservation, and all non-drag alternatives.

### Visual and performance review

Capture the entrance, dense and sparse sections, both wall focus poses, a long title, a no-clipping sheet, all relevant credit/date states, an open volume, forward/reverse page turns, mobile reading, reduced motion, and simplified quality.

Review at actual display size, not only a large screenshot. Inspect title wrapping, readable hierarchy, frame/page edges, shadows, texture resolution, cropping, color fidelity, table clearance, selection distinction, and whether a new visitor can see what to do.

Record cold-start and warm behavior, frame intervals during movement, input feedback, asset transfer, draw calls, and owned-resource counts. Run a repeated tour and view-switch sequence long enough to reveal accumulating resources. State the measurement method and reference device; do not claim a generic “60 fps” without them.

Conduct a small formative task check with people unfamiliar with the controls: find a publication, identify a source, read a story stop, inspect a clipping, and return. Record confusion and corrections. This is a qualitative design check, not a statistical usability claim.

## 13. Acceptance

The work is done when all of the following are demonstrated:

1. The hall provides the intended spatial exhibit and working physical-volume interaction, not only compliant geometry or a static mockup.
2. Every public publication has one unique sheet/layout slot, and every public guided story has one volume and complete DOM reading path.
3. Chronological order is clear, the variable physical scale is disclosed, and source date uncertainty is preserved.
4. No frame overlap, inaccessible high-row placement, camera collision, unintended scene movement, or mobile scroll trap occurs in the reviewed fixtures and real dataset.
5. A selected publication or story becomes readable without waiting for animation. Clipping inspection, required credits, and story text remain available in every renderer mode.
6. Page turns are visually correct, interruptible, and synchronized with the authoritative story state. Close and return behavior work during loading and animation.
7. Existing timeline, Canvas 2D, text archive, filters, record actions, and supported links pass the verified compatibility tests. Forced-text routes do not load Three.js.
8. Accessibility, responsive, failure, performance, asset-policy, and resource-lifetime checks in section 12 pass, with actual test conditions recorded. Any budget revision is explained rather than silently ignored.
9. Joe's visual review accepts the entrance, dense section, sheet focus, open volume, and mobile reading experience. Automated checks alone do not satisfy this condition.
10. Documentation and obsolete-code removal are complete. Issues 58 and 72 are closed only if their verified requirements are met by the delivered work.

## 14. Out of scope

Do not rename the old `docs/js/woven/` modules, legacy `woven-` DOM IDs, or Tailwind color-token names as a separate cleanup project. Retain only the compatibility references actually needed by the integration.

Do not add evidence files, reinterpret rights decisions, fabricate historical imagery/mastheads, rewrite sourced narratives without editorial review, or change publication dates to simplify layout.

Sound, free walking, avatars, physics simulation, WebXR, multiplayer, automatic camera tours, and a renderer/framework migration are not part of this work.

The scope exclusions do not excuse inaccessible reading, missing error states, unreadable mobile controls, unbounded resource use, or unresolved layout density. Those are part of making the hall work.

## References and basis

**Source draft:** `hallspec.md`, September 9, 2026. Key source locations: purpose and preserved views, lines 5–14; spatial rules, lines 24–37; sheets, lines 39–60; movement, lines 62–86; volumes, lines 88–129; assets, lines 131–145; mobile/accessibility, lines 147–172; links and files, lines 174–208; tests/acceptance/scope, lines 210–241.

External references were checked on September 9, 2026. They support specific implementation/accessibility considerations, not the proposed aesthetic choices, dataset assumptions, or performance targets. Match any API use to the repository's installed version.

- [T1] Three.js, Texture documentation: `https://threejs.org/docs/pages/Texture.html` — format/mipmap defaults, color-space annotation, explicit texture disposal.
- [T2] Three.js, PerspectiveCamera documentation: `https://threejs.org/docs/pages/PerspectiveCamera.html` — projection and view-size helpers.
- [T3] Three.js, InstancedMesh documentation: `https://threejs.org/docs/pages/InstancedMesh.html` — repeated shared geometry/material rendering and related resource handling.
- [A1] W3C, WAI-ARIA 1.2, application role: `https://www.w3.org/TR/wai-aria-1.2/#application`.
- [A2] W3C, Understanding SC 2.5.7, Dragging movements: `https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html`.
- [A3] W3C, Understanding SC 2.3.3, Animation from interactions: `https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html`.
- [A4] W3C, Understanding SC 2.5.8, Target size (minimum): `https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html`.
- [A5] W3C, Understanding SC 1.4.10, Reflow: `https://www.w3.org/WAI/WCAG22/Understanding/reflow.html`.
- [A6] W3C, ARIA Authoring Practices, Dialog (modal) pattern: `https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/`.

## 15. Draft 3 addendum: decisions and repository facts

Added September 9, 2026 after Joe reviewed the revision above. This section
takes precedence where it conflicts with sections 1 to 14. Facts here were
checked against the repository.

### Decisions by Joe

1. Public name: **History hall**. Button label: **History hall**. The page
   stays "Historical notes". The other view button stays "Flat timeline".
   Section 2's "The hall" and "Walk the hall" are replaced.
2. Internal `woven` file names, DOM ids, CSS classes, `window.__woven`, the
   `WOVEN_REVIEW.md` file name, and the Tailwind tokens stay. The allowlist
   in section 2 is recorded in `WOVEN_REVIEW.md`. No visitor sees the word
   woven.
3. Routes: keep every route the code reads today. Add `?decade=` and
   `?stop=`. Do not add `?id=` on this page. The table in section 10 is
   replaced by the table below.
4. Screen reader sessions, the formative task check, and reference device
   measurements are Joe's checks after the pull request. The review document
   records exactly what was tested in this environment and what was not.
5. The vertical slice is reviewed from desktop and mobile screenshots before
   the full build continues.

### Routes

| Link | Result |
|------|--------|
| `?view=3d&pub=ID`, `?view=hall&pub=ID`, `?view=woven&pub=ID` | History hall at that sheet. `hall` is the canonical new form |
| `?pub=ID` with no view | History hall at that sheet. Today this opens the flat timeline. The browser review check changes with it |
| `?view=timeline` | Flat timeline |
| `?story=story-NNN` | Opens that story. History hall when WebGL is available, the flat timeline card tour when it is not |
| `?story=story-NNN&stop=evt-NNN` | Opens that stop. Event ids are stable, so no data change is needed. An unknown stop opens the first stop and explains |
| `?decade=1930s` or `?decade=undated` | History hall at that section's entry anchor |
| `?ghost=1` | The gaps in the record sequence on the flat timeline, as today |
| `?twin=1`, `?nogl=1` | Text archive, without fetching Three.js. The requested record or story opens in the text archive |
| `#woven-twin` | The text archive region |
| `woven.html?...` | Forwards query and fragment as today |

Precedence for content targets: `story` (with its `stop`), then `pub`, then
`decade`. Forced text flags override every visual mode.

### Integration facts

- `main.js` mounts the 3D view at the end of `startScene` with
  `app.exhibit = mountExhibit(app, params)`. `app.three` exposes `renderer`,
  `canvas`, `stage`, `controls`, `panel`, and the flat timeline objects. The
  hall mounts in the same slot with the same five fields and keeps the
  property name `app.exhibit` so the five call sites in `main.js` and the
  browser review keep working. `window.__woven.app.exhibit` stays the review
  handle.
- The 3D view replaces `app.select`, `app.playStory`, and `app.showGhost` at
  mount. The hall restores the originals on dispose. The old view did not.
- The frame loop in `main.js` skips its frame time sampler while the 3D view
  has the frame, so the adaptive tier never changes in 3D today. The hall
  must report its frame interval to the sampler or run its own.
- `guide.js` keeps a `hasDeepLink` list of parameters. Add `decade` and
  `stop`.
- `explorer.js` imports `matchesFilters`, `publicationYears`, and
  `threadColor` from `exhibit-geometry.js`. Move those three to
  `docs/js/woven/records.js` before `exhibit-geometry.js` is removed.
- The canvas is shared by the hall and the flat timeline. `role="application"`
  and `tabindex` are set per view: the flat timeline keeps them, the hall
  removes them and hides the canvas from the accessibility tree.
- `tour.js` stays for the flat timeline card tour. It writes `?story=` with
  `history.replaceState` and clears it on exit. The hall's route adapter and
  `tour.js` must agree on that parameter.

### Story and evidence facts

- `model.tours[]` has `id, title, era, strength, people, thread, threadIds,
  stops[]`. Each stop has `kind, eventId, event, dateLabel, precision,
  threadId, clipping, confidence`. `event` is the raw record with `title`,
  `description`, `date`, `people`, `publicationIds`, `sourceFiles`.
  `clipping` has `webPath, width, height, rightsStatus, citation, caption,
  altText, publicationIds`. Clippings match stops by date, never by title.
  `tx` and `ty` are flat timeline coordinates and are ignored in the hall.
- A stop without a clipping gets its citation from `model.citeSource(file)`
  and its rights from `model.sourceRights(file)`.
- 55 public clippings: 32 `crop_first`, 16 `publishable`, 7
  `publishable_with_credit`. All are `.jpg`. Every public file is already
  cropped by `data/make_clippings.py` from crop boxes decided by hand. The
  hall never crops.
- 39 publications have a cleared clipping. 97 do not. 3 have no founding
  year. 17 are active. 119 have a cessation year.
- Titles per decade: 1880s 3, 1900s 2, 1910s 2, 1920s 2, 1930s 13, 1940s 3,
  1950s 9, 1960s 10, 1970s 29, 1980s 21, 1990s 25, 2010s 8, 2020s 6,
  undated 3. The 1890s and 2000s are empty decades and keep a marker. Seven
  titles were founded in 1972.
- Story era fixture: 1880s 001, 002, 003, 010; 1900s 004; 1930s 005, 006,
  007, 008, 009, 012; 1970s 011; 1980s 013. Stories 001 and 010 begin before
  1880 and carry "Begins before 1880".

### Texture budget facts

136 faces at 512 by 704 RGBA8 with mipmaps is about 249 MiB. That breaks the
section 9 budget. The hall keeps a bounded pool of painted faces for sheets
near the visitor and the selected sheet. Far sheets use one shared low detail
material: frame, paper, era accent, no text. The pool size per tier is chosen
to meet the 128 MiB and 64 MiB budgets including wall copies and page
textures, and the chosen numbers are recorded in `WOVEN_REVIEW.md`.

### Tests to change

`scripts/review_woven.py` gates every check on `window.__woven.app.exhibit`
and reads `exhibit.active`, `exhibit.motion`, `exhibit.nodes`, the
`#woven-exhibit-axis` text, the bar position formula, `#woven-motion`, the
turn controls, and the bare `?pub=` flat timeline rule. All of these change.
`scripts/test-woven-exhibit.mjs` tests only `exhibit-geometry.js` and is
replaced by `scripts/test-hall.mjs`. `data/test_woven_layout.py` asserts
literal strings in `main.js` and must be updated with the issue 72 removal.

### Tooling facts

Playwright's pip package must match the Chromium build installed at
`/opt/pw-browsers` (build 1194, Playwright 1.56). The review script launches
Chromium with SwiftShader.

### Work packages

| Package | Delivers | Spec sections | Agent |
|---------|----------|---------------|-------|
| 1 Foundations | Data audit; `layout.js`, `state.js`, `links.js` with no renderer dependency; `make_wall_copies.py` with manifest; `test-hall.mjs`; `test_hall_assets.py`; `records.js` move | 3, 7, 10, 11, 12 pure and asset tests | Opus |
| 2 Vertical slice | `hall.js`, `space.js`, `sheets.js`, `paint.js`, `assets.js`, `rail.js`, `volumes.js`, `reader.js`, `hall.css`; the slice fixtures; `main.js` and page integration; screenshots for Joe | 1, 3 to 6, 8, 9 | Opus |
| 3 Full collection | All sheets and volumes; bounded resources; filters; history; fallbacks; adaptive tiers | 4, 5, 9, 10 | Opus |
| 4 Verification | Browser review matrix; obsolete code removal including issue 72; docs; record of untested checks | 11, 12, 13 | Sonnet |
| 5 Review | Independent review of the diff; fixes | 13 | Opus review |

### Decisions during the build

6. Entrance: the first settled view stands in the 1880s bay and looks down
   the hall. The 1880s sheets are on both walls at reading distance, the
   first reading table is ahead, and the hall recedes toward the 2020s.
7. Sheets without a cleared clipping show the first sentence of the record's
   `historicalNotes` field as an exhibit label under the name, city, and
   dates. A record with no notes shows only the "No copies cleared for
   display here" line.
