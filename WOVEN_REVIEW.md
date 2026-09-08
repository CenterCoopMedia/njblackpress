# Woven exhibition review

Woven has two views of the same publication records. The default 3D weave presents a folded textile. Timeline retains the existing date-based layout and sourced story tours. Both use one renderer, one data adapter, one publication panel, and one complete text archive.

## Reading the sculpture

Each colored strand represents one publication. Color groups founding eras. Thickness reflects the number of evidence records, not circulation or influence. Faint, interrupted strands mean that no evidence is cleared for display here; they do not establish that no copies survive elsewhere. Undated titles use fragments. Active titles have loose ends.

**Both views use recorded publication spans.** New Jersey Trumpet runs from 1887 to 1897. Same-year titles have a small selectable mark. Dashed continuations show unrecorded end dates, not confirmed survival to the present. Undated fragments stay in the separate undated band without an inferred founding year. Only active titles have loose ends. Year labels follow the folded surface; folds and crossings do not imply relationships. Publication records, IDs, citations, rights, events, and stories are unchanged.

## Interaction

Use the native publication index, founding-era, city, and evidence/status filters, title search, or the canvas to select a publication. The record replaces the index dock rather than covering the drawing. On narrow screens, the index and record sit below the drawing.

Drag sideways or use the turn buttons to rotate the sculpture. The canvas supports up/down to browse titles, Enter to open, left/right to turn, Home to reset the pose, and Escape to clear selection. Reduced motion starts paused. Paused scenes render only when something changes; hidden and offscreen scenes do not draw.

The full text archive uses a native disclosure. Its direct link and `?twin=1` open it. `?nogl=1` and a lost WebGL context promote that same archive. The explicit text route does not import Three.js. When WebGL is unavailable, a Canvas 2D timeline keeps the camera, picking, index, search, and stories. The 3D button is disabled with a visible explanation. Existing `?pub=ID`, `?story=ID`, and `?ghost=1` links keep the timeline/narrative behavior. `?view=woven&pub=ID` opens a record in the sculpture.

## Checks

Run the existing data, navigation, Woven layout, and Woven usability Python checks, then `node scripts/test-woven-exhibit.mjs` and `node data/test_woven_model.mjs` (Node 22.15 or later). The browser review runs with `python scripts/review_woven.py --output /tmp/woven-review`; install Python Playwright 1.55.0 and its Chromium browser first.

The browser script checks the real WebGL scene, native record index, filters, record focus, pointer picking after scrolling, keyboard selection, both views, sourced stories, deep links, reduced motion, idle drawing, failed data, no-WebGL behavior, context loss, and 320/375/390/768px touch-emulated layouts. It saves screenshots and a JSON result file. These are Chromium checks, not a claim of real-device, screen-reader, Safari, or Firefox certification.

Review the desktop, record, timeline, story, and mobile screenshots before merge. A merge to `master` publishes the page through GitHub Pages. Revert the feature PR to restore the prior presentation; no data migration or dependency change is required.
