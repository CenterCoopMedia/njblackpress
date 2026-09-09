# Historical notes review

Historical notes presents the archive through guided stories and two interactive timeline views. Three.js renders the default 3D view. Each publication has a separate, straight bar. The bars sit at different depths in a curved gallery. Readers can turn the view, select a bar, or use the publication index.

## Dates and evidence

Both views use recorded publication spans. New Jersey Trumpet runs from 1887 to 1897. Same-year publications have a small selectable mark. Dashed bars identify unrecorded end dates. Arrows identify active titles. Undated titles stay in a separate group without an inferred founding year.

Color groups founding eras. Bar width reflects the number of evidence records. Faint bars identify titles without evidence cleared for display here. This does not establish whether copies survive elsewhere. Publication IDs, dates, citations, and rights remain the same.

## Interaction

Use the era, city, and evidence filters, title search, or canvas to select a publication. The record replaces the index dock. On narrow screens, the index and record sit below the drawing.

Drag sideways or use the turn buttons to rotate the 3D view. Use up and down to browse titles, Enter to open a record, and left and right to turn. Reduced motion starts paused. Paused views render only when something changes. Hidden and offscreen views do not draw.

The flat timeline supports pan, zoom, keyboard navigation, and sourced story tours. Browsers without WebGL use Canvas 2D. The full text archive uses a native disclosure. `?twin=1` opens it. `?nogl=1` opens the text archive without importing Three.js. A lost WebGL context also opens the text archive.

## Routes

The public route is `historical-notes.html`. The old `woven.html` route forwards query parameters and fragments. Existing publication, story, and text-view links still work. New 3D links use `?view=3d&pub=ID`. Old `?view=woven` links remain supported.

Internal module paths and DOM identifiers retain their existing names to preserve links and avoid an unrelated code migration. Public labels, instructions, metadata, and visual treatments use publication and timeline language.

## Checks and deployment

Run the data, navigation, layout, and usability Python checks. Run `node scripts/test-woven-exhibit.mjs` and `node data/test_woven_model.mjs`. Run `python3 scripts/review_woven.py --output /tmp/notes-review` for Chromium checks and screenshots.

The browser review covers WebGL, filters, records, focus, pointer selection after scrolling, keyboard access, both views, stories, deep links, reduced motion, idle drawing, failed data, Canvas 2D, context loss, and mobile layouts. Review the desktop and mobile screenshots before merge.

GitHub Pages publishes `docs/` from `master`. Verify the Pages build and the public route after merge. Git history provides rollback. No data migration or dependency change is required.

## History hall: texture budget (work package 2)

The hall paints a bounded pool of 24 sheet faces. A face is 512 by 704 RGBA8,
about 1.83 MiB with its mip chain, so the painted faces hold about 44 MiB. With
their 24 brass plates (about 8 MiB), the 16 decade markers (about 11 MiB), the
13 book covers (about 6 MiB), and the open volume's pages and clipping (about
11 MiB), the hall's own resident textures come to roughly 80 MiB, inside the
128 MiB standard budget. Painting all 136 faces at that size would take about
249 MiB, which is why the pool exists. Sheets outside the pool share one low
detail paper material with an era accent and no type. The simplified tier and
its own pool size arrive with the adaptive work in the next package.
