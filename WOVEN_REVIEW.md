# Historical notes review

Historical notes presents the archive as a walk through a history hall, plus
two supporting views: a flat timeline for exact dates and a full text
archive. `tasks/hall-spec.md` is the specification; this document records
what the delivered page actually shows, what governs its content, and what
has and has not been checked.

## What the hall shows

Three.js renders each public publication as a framed sheet, hung on one of
two walls at reading height, in one section per founding decade from the
1880s to the 2020s, plus a section for publications whose founding date is
unrecorded. A section is as long as the sheets and reading tables it holds,
not a fixed distance per year; a note beside the decade navigator says so.
Every guided story is a bound volume on a reading table in a shallow bay off
the main corridor.

Selecting a sheet opens the existing record panel and brings the sheet into a
comfortable focus pose. Selecting a volume opens the story's own DOM reader
immediately, without waiting for the book to finish opening. The reader holds
the full stop text, its citation and confidence wording, the required
credit, a "Stop N of M" counter, Previous/Next/Close, a "View clipping"
action that opens a large credited image with zoom controls, and a contents
selector. Closing a story or a record restores the visitor's previous
position: camera pose, filters, and DOM focus.

## Dates and evidence rules

Both the hall and the flat timeline use each publication's recorded span, not
an inferred one. New Jersey Trumpet runs 1887 to 1897. A publication founded
and ceased in the same year shows that single year rather than a zero-length
range. Same-year publications each keep a separate slot with the shared date
still shown. Dashed marks and "end unrecorded" wording identify a title with
no recorded ending; a small "Still publishing" mark and label identify an
active title. Titles with no recorded founding year sit in their own
undated section rather than being placed at an invented date.

A sheet with a cleared clipping shows it, credited exactly as its rights
status requires; `crop_first` and `publishable_with_credit` files carry the
credit next to the image, not only on a brass plate. A sheet with no cleared
clipping shows the publication's name, city, and dates plus the first
sentence of its historical notes where one exists, or the line "No copies
cleared for display here. Copies may survive elsewhere." when it does not.
This is the majority case: 39 of 136 publications have anything cleared to
show. A record count is how much research is attached to an entry, never a
measure of a publication's importance; the hall reports it the same way the
site already does on a publication's own page — "1 record" or "N records"
for the full evidence array, with cleared records counted separately.

## Interaction

Use the era, city, and evidence filters, title search, the publication
index, or the hall itself to select a publication. Filtering never rebuilds
or reorders the gallery: it dims sheets that do not match and keeps every
slot in place, and it says how many publications match, including "no
publications match these filters." A publication selected from outside the
current filters stays reachable and is marked as revealed past them, with an
action to clear the filters; the visitor's own filter choices are never
changed silently.

Inside the hall, dedicated controls move Previous/Next publication in
gallery order, Previous/Next decade, and to a named decade or the undated
section directly; a "Back to entrance" control returns to the first section.
A horizontal drag moves along the rail; vertical drag and the wheel scroll
the page as normal until "Use scroll to move" is turned on. Optional
Left/Right and Shift+Left/Right shortcuts apply only while focus is inside
the hall's own controls. A "Simplified view" control lets a visitor pin the
adaptive tier themselves. Inside an open story, Previous/Next buttons and
Left/Right (scoped to the reader) turn pages; a swipe on the picture turns
the page while the surrounding text still scrolls normally.

The flat timeline keeps its own interaction: drag or the turn controls pan
and zoom, up/down choose a publication on the canvas, Enter opens a record,
and the same filters, search, and record panel apply. Reduced motion starts
both views settled, with no animation left running. Paused and hidden views
render only when something changes. Browsers without WebGL use Canvas 2D. The
full text archive uses a native disclosure; `?twin=1` opens it directly, and
`?nogl=1` opens it without importing Three.js at all. A lost WebGL context
also promotes the same text archive, carrying the selection, story, stop, and
filters that were open at the time.

## Routes

| Link | Result |
|------|--------|
| `?view=3d&pub=ID`, `?view=hall&pub=ID`, `?view=woven&pub=ID` | History hall at that sheet. `hall` is the canonical new form |
| `?pub=ID` with no view | History hall at that sheet |
| `?view=timeline` | Flat timeline |
| `?story=story-NNN` | Opens that story. History hall when WebGL is available, the flat timeline card tour when it is not |
| `?story=story-NNN&stop=evt-NNN` | Opens that stop. Event ids are stable. An unknown stop opens the first stop and explains |
| `?decade=1930s` or `?decade=undated` | History hall at that section's entry anchor |
| `?ghost=1` | The gaps in the record sequence on the flat timeline |
| `?twin=1`, `?nogl=1` | Text archive, without fetching Three.js. The requested record or story opens in the text archive |
| `#woven-twin` | The text archive region |
| `woven.html?...` | Forwards query and fragment as today |

Precedence for content targets: `story` (with its `stop`), then `pub`, then
`decade`. Forced-text flags override every visual mode. An invalid id,
decade, or stop produces a visible explanation and keeps the index or
contents usable rather than an empty scene.

## The woven naming allowlist

The public name is **History hall**; the button that opens it reads **History
hall**. The page itself stays "Historical notes," and the other view button
stays "Flat timeline." No visitor-facing text, on the page or in
`docs/js/hall/`, uses the word "woven" or a textile word (loom, cloth, weave,
thread, warp, weft, stitch, fabric).

The following internal names are kept because renaming them is a separate
migration, not part of this work (`tasks/hall-spec.md` section 2 and section
15 decision 2):

- File and directory names under `docs/js/woven/`, and the file name
  `WOVEN_REVIEW.md` itself.
- DOM ids and classes such as `#woven-publications`, `#woven-panel`,
  `#woven-stage`, `.woven-btn`, and the reading key's `.woven-key-thread`
  class names.
- `window.__woven`, the page's debugging handle for both views.
- Tailwind color tokens such as `--thread-color` and the `surface-cloth`
  class name.
- The retained data model's own field names — `model.threads`,
  `tour.thread`, `threadIds`, `threadIndex`, `threadColor` — documented at
  the top of `docs/js/hall/layout.js` and `docs/js/hall/views.js`, where a
  one-line comment marks the boundary: the model still calls a publication a
  thread; nothing above that boundary does.
- The `view=woven` URL alias and the `woven` route key that maps it to the
  hall.

`data/test_woven_usability.py` enforces this allowlist: it scans
`docs/js/hall/*.js` and `docs/css/hall.css` for the textile words above
(with the exact allowed tokens excluded), scans the visible text of
`docs/historical-notes.html` and the text hall modules render into the page
for the same words, and separately checks that neither surface shows the
word "woven" to a visitor.

## Texture budget and quality tiers

The hall paints a bounded pool of sheet faces: **24 in the standard tier and
12 in the simplified tier**, recorded as `FACE_POOL_SIZES` in
`docs/js/hall/sheets.js`. A face is 512 by 704 RGBA8, about 1.83 MiB with its
mip chain, so the painted faces hold about 44 MiB in the standard tier and
about 22 MiB in the simplified one. With their brass plates (about 8 and 4
MiB), the 16 decade markers (about 11 MiB), the 13 book covers (about 6 MiB),
and the open volume's pages and clipping (about 11 MiB), the hall's own
resident textures come to roughly 80 MiB standard and roughly 50 MiB
simplified, inside the 128 MiB and 64 MiB budgets. Painting all 136 faces at
that size would take about 249 MiB, which is why the pool exists. Sheets
outside the pool share one low-detail paper material with an era accent and
no type.

Decoded images are owned rather than cached: the working set is the wall
copies the painted pool is showing plus the open spread and the stop either
side of it, and everything else is released. Only those adjacent stops are
preloaded.

The two named tiers are standard and simplified. Simplified lowers the device
pixel ratio to 1.25, halves the face pool, drops the optional fill light, and
turns a flat leaf instead of a bending one. The hall has no shadows, so
shadows are not in the ladder. The tier is judged only on frame intervals
measured while something was moving, over windows of 30 samples, with
separate thresholds for falling back and returning so it cannot oscillate. A
**Simplified view** control in the hall controls explains the current
setting and pins the visitor's choice, after which measurement never changes
it.

`window.__woven.app.exhibit.stats()` reports what the hall owns: resident
bytes, decoded images, pending images, painted faces, pending paints,
listeners registered by the hall, and the renderer's texture and geometry
counts. `scripts/review_hall.py` runs ten hall and timeline switches and ten
story open and close cycles and asserts that those counters return to their
settled values.

## Checks and deployment

Run the data, navigation, layout, and usability Python checks. Run
`node scripts/test-hall.mjs` (pure layout, state, camera-fit, route, and
formatting checks) and `node data/test_woven_model.mjs` (the flat timeline's
own model and geometry checks). Run `python3 data/test_hall_assets.py`; it
reads only the public files already committed under `docs/`, so it needs no
local evidence corpus. Run
`python3 scripts/review_hall.py --output /tmp/hall-review` for the Chromium
checks and screenshots; `scripts/review_woven.py` is a thin wrapper that
calls the same script, kept for the old command name.

The browser review covers the hall's entrance, a dense and a sparse section,
sheet focus, an open volume read from above, forward and reverse page turns,
filters (many matches, one match, zero matches, a record revealed past the
filters), Previous/Next publication and decade, browser history, invalid
routes, the adaptive tier, bounded resource use across repeated view and
story cycles, an offscreen or hidden scene, a failed image, the flat
timeline (era browsing, its own record panel, keyboard selection, picking
after the page scrolls, idle drawing), both forced-text routes, no usable
WebGL, a hall that fails to open, a lost WebGL context, a missing font, and
four mobile viewports (375×812, 390×844, 320×740, 768×1024) including the
portrait entrance. Review the desktop and mobile screenshots before merge.

GitHub Pages publishes `docs/` from `master`. Verify the Pages build and the
public route after merge. Git history provides rollback. No data migration or
dependency change is required.

## What was tested and what was not

This remote Chromium environment ran, and this review recorded the results
of: SwiftShader-rendered WebGL and the Canvas 2D fallback, keyboard-only
interaction with the hall's own controls and the flat timeline's canvas,
`prefers-reduced-motion: reduce` at startup, a denied WebGL context, a lost
WebGL context mid-story, four mobile viewports at `device_scale_factor: 1`,
and the hall's own resource counters (`stats()`) sampled after ten hall and
timeline switches and twenty story open/close cycles.

Not tested here, and left for Joe's checks after this pull request, per
`tasks/hall-spec.md` section 15 decision 4:

- A screen reader session on Windows, and on VoiceOver/Safari where
  available.
- A small formative task check with people unfamiliar with the controls:
  find a publication, identify a source, read a story stop, inspect a
  clipping, and return.
- Frame-interval, memory, and asset-transfer measurements on named reference
  devices and browsers, at their own device pixel ratio.
- Visual review at actual display size, rather than only the screenshots
  this review captured.
