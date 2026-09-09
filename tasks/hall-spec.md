# Specification: the history hall

Status: draft 2, waiting for Joe's updated plan. Owner: Joe Amditis.
Written 2026-09-09. Draft 2 folds in a code feasibility review.

## 1. Purpose

Replace the 3D timeline on `historical-notes.html` with a walk through the
history hall of New Jersey's Black press. The hall is a museum corridor. Each publication is
a framed sheet on a wall. Guided stories are bound volumes on reading tables.
The visitor opens a volume and turns its pages to read the documented events
and see the clippings.

The flat timeline, the Canvas 2D fallback, the text archive, and all deep
links stay as they are.

## 2. Names

- The page stays "Historical notes". The 3D view is "History hall". Button
  label: "History hall". The other button stays "Flat timeline".
- Nothing public or internal is called woven. New modules live in
  `docs/js/hall/`. The old `docs/js/woven/` folder, the `woven-` DOM ids and
  CSS files, `window.__woven`, `WOVEN_REVIEW.md`, and the `*woven*` test and
  review scripts are renamed to `notes` in work package 0. `docs/woven.html`
  stays as a forwarder for old links only.
- No textile words in public copy or in new code. Do not use loom, cloth,
  weave, thread, warp, weft, stitch, or fabric. Use publication, sheet, frame,
  volume, page, section, and rail.

## 3. The space

The hall runs along the z axis. Time runs from the entrance to the far end.

| Item | Rule |
|------|------|
| Year range | 1880 to 2026, the same as the flat timeline |
| Order | Time is in order along the hall but not to scale. The flat timeline is the view for exact dates |
| Sections | One section per decade, 1880s to 2020s. A short alcove at the end holds the 3 undated titles |
| Section length | Long enough to hang its sheets at 1.6 units apart in up to 3 rows per wall, with a 3 unit margin. Minimum 8 units. The 1970s, with 29 titles, is about 16 units |
| Section marker | A painted lintel across the hall at each decade change. The decade label is a canvas texture in Libre Franklin |
| Floor | Dark walnut planks (`walnut-900` to `walnut-700`) with a faint grain texture made in code |
| Walls | Linen plaster (`linen-200` at low light). Both walls hold sheets |
| Ceiling | Not drawn. The top fades to `walnut-950` |
| Light | One hemisphere light, one directional light, and one warm point light that travels with the visitor. Sheets near the visitor read as lit. Far sheets read as dim |

## 4. Sheets

Each publication is one framed sheet.

| Property | Rule |
|----------|------|
| Position along the hall | Founding order inside the decade section, even spacing along the wall. The founding year is on the plate, and small year marks run along the floor edge |
| Wall | Alternate left and right in founding order inside each decade. This balances the walls |
| Row | When a wall has more sheets than fit in one row at 1.6 units apart, hang them in 2 rows, then 3. Row 1 is at eye height. This is a salon hang. Never more than 3 rows |
| Size | 1.4 units wide, 1.9 units tall. A sheet with a cleared clipping uses the clipping's aspect inside the frame |
| Frame color | The founding era color already used by the flat timeline legend |
| Face | Painted into a shared atlas texture, 16 faces per 2048 by 2816 atlas, 512 by 704 pixels each. Nine atlases cover 136 sheets. The masthead is the publication name in Libre Franklin bold, at 34 pixels or more, wrapped to fit. Under it: city and years in DM Sans. Anisotropy is set on the atlas |
| Years text | "1934–1966". Active: "1990–present". Unrecorded end: "1955, end unrecorded". Undated: "date unrecorded" |
| Clipping | If the publication has a cleared clipping, the wall copy (section 7) fills the lower two thirds of the face. The masthead sits above it |
| No clipping | The face shows the masthead and one line: "No copies cleared for display here." Copies may survive elsewhere. Do not say lost |
| Credit | A `publishable_with_credit` clipping shows its citation on the brass plate under the frame. A `crop_first` clipping shows "Cropped detail" on the plate |
| Active mark | A small warm lamp on the frame of a title that still publishes |
| Evidence count | The plate shows "3 records" style text from the evidence array length |

Hover or focus highlights the frame. Selection turns the visitor to face the
sheet and opens the existing record panel (`panel.js`). The record panel is
unchanged.

## 5. Movement

The visitor moves on a rail along the hall center line. There is no free walk.

| Input | Result |
|-------|--------|
| Wheel or trackpad over the canvas | Move along the rail. Vertical wheel maps to forward and back. The page does not scroll while the pointer is over the canvas and the hall is active |
| Drag sideways | Move along the rail |
| Drag up or down | Tilt the view a little. Limit ±12 degrees |
| Arrow left and right | Move one year |
| Shift + arrow left and right | Move one decade |
| Arrow up and down | Select the previous or next sheet in founding order |
| Enter | Open the selected sheet |
| Escape | Close the record panel or the open volume |
| Previous era and Next era buttons | Move to the start of the previous or next decade section |
| Year rail | Shows the year at the visitor's position. Click or drag it to move |
| Whole hall button | Move to the entrance and face down the hall |
| Reset the view | Same as whole hall |

Selection of a sheet moves the visitor to a reading position 2.6 units from
the sheet and turns to face it. Selection from the publication index, search,
or a deep link uses the same move.

Reduced motion: every move is a cut with a 200 millisecond fade, not a glide.
The page turn is instant.

The travelling light snaps to the rail position. It has no easing of its own.
The scene is marked dirty only when the rail position changes by more than
0.01 units, so an idle hall draws nothing.

## 6. Volumes and the reading table

Each guided story is a bound volume. Volumes lie on a long reading table in the
middle of the hall, in the section where the story's era starts. A story whose
era starts before 1880 sits in the 1880s section.

| Section | Stories |
|---------|---------|
| 1880s | 001, 002, 003, 010 |
| 1900s | 004 |
| 1930s | 005, 006, 007, 008, 009, 012 |
| 1970s | 011 |
| 1980s | 013 |

Closed volume: a box 0.9 by 1.2 by 0.12 units. The cover is a canvas texture
with the story title and era in Libre Franklin. The spine shows the title.
Cover color is the era color, darkened.

Open volume: select a volume from the table, from the Guided stories picker,
from a record panel, or from a `?story=story-NNN` deep link. The volume lifts,
turns to the visitor, and opens. The visitor moves to a reading position above
the table.

Each story stop is one spread.

| Page | Content |
|------|---------|
| Left page | The clipping for the stop, full public file, lazy loaded. A `crop_first` clipping has an accent outline. A stop with no clipping shows a plain page with the stop date in large type |
| Right page | The stop title and date, painted at headline size |

The full stop text, citation, confidence, and rights note are in a DOM reader
panel beside the open volume. This keeps the text selectable, crisp, and
readable by screen readers. The reader panel has Previous, Next, and Close
buttons and shows "Stop 3 of 9".

Page turn: the turning page is two single sided half planes with opposite
normals on one spine pivot. The front carries the current right page. The back
carries the next left page. The pivot rotates 180 degrees in 650 milliseconds
with a small bend from a segmented plane. Previous turns the page back.

Stories always play in the history hall when WebGL is available. The Guided
stories button, story links, record panel story buttons, and `?story=` links
switch to the hall and open the volume. The flat timeline keeps its card tour
(`tour.js`) only as the no WebGL and Canvas 2D fallback. `playStory` branches
on WebGL availability, not on the open view.

Closing the volume returns it to the table and returns the visitor to the rail.

Keyboard: Left and Right turn pages while a volume is open. Escape closes it.

## 7. Wall copies of clippings

A builder script `data/make_wall_copies.py` reads `docs/data/clippings.json`
and writes one JPEG for each public clipping to `docs/images/evidence/wall/`.

| Rule | Value |
|------|-------|
| Source | The public file at `webPath`. The script does not need the research corpus |
| Width | 400 pixels. Height keeps the aspect |
| Quality | JPEG 78 |
| Name | The same file stem as the public file, always `.jpg` |
| Repeat run | A second run changes no file |
| Rights | The public file is already cropped and cleared. The wall copy inherits its status. The credit rules in section 4 apply |

The builder joins the generated files list in `CLAUDE.md`.

## 8. Small screens

At 375 by 812 the stage is `62svh` tall, not `vh`, so iOS toolbars do not cut
it. The hall uses a
narrower field of view in portrait so sheets stay large. Sheets are tappable at
44 pixels or more.

An open volume fills the stage as a reader sheet. The reader panel slides up
over the lower half of the stage. The open volume stays visible in the upper
half, with the clipping page facing the visitor. Swipe left and right turns the
page. This closes issue 58.

## 9. Accessibility and fallbacks

- The publication index, search, filters, and the text archive are unchanged.
  Every publication keeps a native button in `#woven-publications`.
- The canvas keeps `role="application"` and the help text is updated for the
  hall.
- Live announcements name the position ("1930s. 13 publications began in this
  decade.") and each selection.
- No WebGL: the flat timeline opens in Canvas 2D. The hall button is disabled
  and the renderer note explains it.
- `?nogl=1` and `?twin=1` open the text archive without Three.js.
- Context loss: the text archive is promoted, as today.
- The adaptive ladder stays: lower pixel ratio, then no travelling light, then
  no frame shadows, then a visible "simplified" notice. The frame time sampler
  in the page controller must run while the hall is active. Today it is
  skipped when the 3D view has the frame.
- Idle rendering: draw only when something moves or changes.
- The hall restores the page controller's `select`, `playStory`, and
  `showGhost` functions when it is disposed. The old 3D view did not.

## 10. Deep links

| Link | Result |
|------|--------|
| `?view=3d&pub=ID` | Opens the history hall at that sheet. Kept for old links |
| `?view=hall&pub=ID` | Same. New links use this form |
| `?view=woven` | Same as `?view=3d`. Old links only |
| `?pub=ID` | Opens the history hall at that sheet. Today this opens the flat timeline; the browser review check changes |
| `?view=timeline` | Flat timeline |
| `?story=story-NNN` | Opens the history hall and that volume. Without WebGL, the card tour on the flat timeline |
| `?ghost=1` | The gaps in the record sequence on the flat timeline, as today |
| `?twin=1`, `?nogl=1` | Text archive |
| `#notes-twin` | The text archive region. Was `#woven-twin`. The old fragment is mapped to the new id |
| `woven.html?...` | Forwards as today |

No new `?id=` or `?decade=` parameter. `?id=` already means a publication on
`publication.html` and a story on `story.html`.

## 11. Files

Renamed in work package 0: `docs/js/woven/` to `docs/js/notes/`, `docs/css/woven*.css` to
`docs/css/notes*.css`, `woven-` ids and classes to `notes-`, `window.__woven`
to `window.__notes`, `WOVEN_REVIEW.md` to `NOTES_REVIEW.md`,
`scripts/review_woven.py` to `scripts/review_notes.py`, `data/test_woven_*` to
`data/test_notes_*`, `data/test_woven_model.mjs` to `data/test_notes_model.mjs`.

New:

- `docs/js/hall/hall.js`: mount, dispose, view switch, deep links. Replaces `exhibit.js`. Mounts in the same slot with the same contract: renderer, canvas, stage, controls, panel.
- `docs/js/hall/constants.js`: decade table, era colors, section lengths, shared sizes.
- `docs/js/hall/space.js`: floor, walls, lintels, lights, sections.
- `docs/js/hall/sheets.js`: sheet layout, frames, faces, plates, picking.
- `docs/js/hall/paint.js`: canvas textures for mastheads, plates, lintels, covers, and pages.
- `docs/js/hall/rail.js`: camera rail, inputs, moves, reduced motion.
- `docs/js/hall/volumes.js`: tables, volumes, open and close, page turn.
- `docs/js/hall/reader.js`: DOM reader panel, small screen sheet, keyboard.
- `docs/css/hall.css`: replaces `woven-exhibit.css`.
- `data/make_wall_copies.py` and `docs/images/evidence/wall/`.
- `scripts/test-hall.mjs`: replaces `test-woven-exhibit.mjs`.
- `data/test_hall_assets.py`: every clipping has a wall copy, the builder is stable.

Moved: `matchesFilters`, `publicationYears`, and `threadColor` from
`exhibit-geometry.js` to `docs/js/notes/records.js`, because the publication
index imports them. `threadColor` becomes `eraColor`.

Removed: `exhibit.js`, the rest of `exhibit-geometry.js`, `woven-exhibit.css`,
`test-woven-exhibit.mjs`, the unused warp meshes and pluck and fray state in
`main.js` (issue 72). `cloth.js` stays because the flat timeline draws with
it.

Each new JavaScript file stays under 400 lines.

## 12. Tests and review

- `node scripts/test-hall.mjs`: year to position, wall alternation, row
  stacking, section membership, volume placement per story, years text for
  every date case, credit line for every `publishable_with_credit` clipping.
- `python3 data/test_hall_assets.py`: wall copies exist and match.
- `python3 data/test_notes_usability.py` and `test_notes_layout.py`: updated
  for the hall controls and the renamed files.
- `scripts/review_notes.py`: replace the exhibit checks with hall checks. Add:
  sheet count equals publication count, pointer selection of a sheet, open a
  volume, Next advances the stop and the reader text, Escape closes, all deep
  links in section 10, the 375 by 812 reader sheet shows the open volume and
  the reader text together, Three.js never loads with `?nogl=1`.
- Desktop and mobile screenshots reviewed before merge.

## 13. Acceptance

The work is done when:

1. The hall is the default view and passes every check in section 12.
2. Every publication is a sheet. Every story is a volume that opens and turns.
3. The flat timeline, Canvas 2D, text archive, and deep links behave as before.
4. Issue 58 and issue 72 close.
5. `CLAUDE.md`, `NOTES_REVIEW.md`, `CODEBASE_OVERVIEW.md`, and `AGENTS.md`
   describe the history hall.
6. No public copy or new code uses a textile word. Nothing is called woven
   except the `woven.html` forwarder.

## 14. Work packages

| Package | Owns | Depends on |
|---------|------|------------|
| 0 Rename | Every `woven` path, id, class, global, script, and doc name. No behavior change | None |
| 1 Foundations | `hall.js`, `constants.js`, `paint.js`, `hall.css`, `historical-notes.html`, `main.js` changes, `make_wall_copies.py`, wall copies | 0 |
| 2 Space and rail | `space.js`, `rail.js` | 1 |
| 3 Sheets | `sheets.js` and its exported layout functions | 1 |
| 4 Volumes | `volumes.js` | 1, 2 |
| 5 Reader and small screens | `reader.js`, the small screen block of `hall.css` | 1, 4 |
| 6 Tests and docs | `test-hall.mjs`, `test_hall_assets.py`, the Python checks, `review_notes.py`, the docs | 2 to 5 |

Packages 2 and 3 run in parallel. Package 0 is a mechanical rename and lands
as its own commit so the diff of the real change stays readable.

## 15. Out of scope

- Renaming the Tailwind color tokens `linen` and `thread`. Filed as an issue.
- New evidence files or rights changes.
- Sound.
