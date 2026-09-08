# Woven exhibition review

Woven has two views of the same publication records. The default 3D weave presents a folded textile. Timeline retains the existing date-based layout and sourced story tours. Both use one renderer, one data adapter, one publication panel, and one complete text archive.

## Reading the sculpture

Each colored strand represents one publication. Color groups founding eras. Thickness reflects the number of evidence records, not circulation or influence. Faint, interrupted strands mean that no evidence is cleared for display here; they do not establish that no copies survive elsewhere. Undated titles use fragments. Active titles have loose ends.

**Thread length and folds in 3D are artistic, not publication lifespans or relationships.** Use Timeline for dates. Missing end dates are distinguished from active titles. Publication records, IDs, citations, rights, events, and stories are unchanged.

## Interaction

Use the native publication index, city and evidence/status filters, title search, or the canvas to select a publication. The record replaces the index dock rather than covering the drawing. On narrow screens, the index and record sit below the drawing.

Drag sideways or use the turn buttons to rotate the sculpture. The canvas supports up/down to browse titles, Enter to open, left/right to turn, Home to reset the pose, and Escape to clear selection. Reduced motion starts paused. Paused scenes render only when something changes; hidden and offscreen scenes do not draw.

The full text archive uses a native disclosure. Its direct link and `?twin=1` open it. `?nogl=1`, unavailable WebGL, and a lost WebGL context promote that same archive. The no-WebGL route does not import Three.js. Existing `?pub=ID`, `?story=ID`, and `?ghost=1` links keep the timeline/narrative behavior. `?view=woven&pub=ID` opens a record in the sculpture.

## Checks

Run the existing data, navigation, Woven layout, and Woven usability Python checks, then `node scripts/test-woven-exhibit.mjs`. The browser review runs with `python scripts/review_woven.py --output /tmp/woven-review`; install Python Playwright 1.55.0 and its Chromium browser first.

The browser script checks the real WebGL scene, native record index, filters, record focus, pointer picking after scrolling, keyboard selection, both views, sourced stories, deep links, reduced motion, idle drawing, failed data, no-WebGL behavior, context loss, and 375/390/768px touch-emulated layouts. It saves screenshots and a JSON result file. These are Chromium checks, not a claim of real-device, screen-reader, Safari, or Firefox certification.

Review the desktop, record, timeline, story, and mobile screenshots before merge. This change does not deploy itself. Revert the feature PR to restore the prior presentation; no data migration or dependency change is required.
