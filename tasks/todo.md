# Session plan: the history hall

Goal: replace the 3D timeline on Historical notes with the history hall.
Milestone: https://github.com/CenterCoopMedia/njblackpress/milestone/7
Specification: `tasks/hall-spec.md` (draft 3: Joe's revision plus the
section 15 addendum).

## Plan

- [x] Confirm the milestone and the concept with Joe.
- [x] Survey the current code, data, tests, and tooling.
- [x] Feasibility review of the draft against the code.
- [x] Merge Joe's revised spec and record decisions in section 15.
- [x] Create milestone 7 and issues 74 to 78. Assign 58 and 72 to it.
- [x] Package 1 (#74): data audit, layout, state, links, wall copies, pure tests. Commit 7b41d57.
- [x] Package 2 (#75): vertical slice. Commit 5569588. Joe approved the screenshots.
- [x] Package 3 (#76): full collection, resources, filters, history, fallbacks. Commit 095a2b6.
- [x] Package 4 (#77): browser review matrix, obsolete code removal, docs.
- [ ] Package 5: independent review of the diff. Fix findings.
- [ ] Push and open the pull request. Joe runs the human checks after.

## Rules for this session

- Fable directs. Opus and Sonnet agents write code. Every diff is read before
  commit.
- Commit messages explain why. No AI attribution lines.
- Sentence case. Plain English. No textile words in new copy or code.

## Review notes

Package 4 (#77), Sonnet.

### Review command

`scripts/review_hall.py` is now the one browser review command; it already
carried the hall's own checks and now also carries the flat timeline,
fallback, mobile, and context-loss checks that used to live in
`scripts/review_woven.py`. `scripts/review_woven.py` is a thin wrapper that
subprocess-calls `review_hall.py` with the same `--output`, kept only for the
old command name. Folded in: full text archive starts collapsed, the bare
`?pub=` link now opening the hall, record-close focus restore and index
`inert` toggling, "Find a title" and "Read as a list," era browsing and a
record panel and keyboard selection and post-scroll picking and idle drawing
on the flat timeline, and the three mobile viewports (390×844, 320×740,
768×1024) beyond the 375×812 one the hall checks already covered in detail.

### Issue 72

`docs/js/woven/main.js` no longer allocates `warpFull`/`warpCoarse` (they
were built, textured, and toggled every frame, but never added to the
scene), and no longer drives the pluck ripple (`canHover`, `pluckStart`,
`applyMotionPref`, `pluck()`, and every call site) — `shaders.js`'s
`pluckWeight()` is defined but never called from its vertex shader's `main`,
so the ripple had no visual effect left to preserve. `cloth.js` still
exports `buildWarp` (read directly by `data/test_woven_model.mjs`) and
`shaders.js` still declares the pluck and fray uniforms unused, so both were
left in place rather than touched. `data/test_woven_layout.py` now asserts
that `warpFull`, `warpCoarse`, `buildWarp`, `pluckUniforms`, and `canHover`
are gone from `main.js`, so a regression is caught immediately.

### Obsolete code removed

`docs/js/woven/exhibit.js`, `docs/js/woven/exhibit-geometry.js`,
`docs/css/woven-exhibit.css`, and `scripts/test-woven-exhibit.mjs` are
deleted; nothing imported or linked them (`explorer.js` already reads
`matchesFilters`/`publicationYears`/`threadColor` from `records.js`, and
`main.js` mounts `hall.js`, never `exhibit.js`). The flat-timeline rules
`woven-exhibit.css` still carried — the dock offset for `#woven-yearrail`,
`#woven-labels`, and `#woven-eras`, the `.woven-legend-hidden` toggle, and
`#woven-timeline-controls` — moved into `docs/css/woven.css`. The exhibit-only
markup (`#woven-exhibit-axis`, `#woven-turn-controls`, `#woven-motion`,
`#woven-exhibit-caption`) is gone from `historical-notes.html`; none of it
was reachable any more; `data-view="3d"` never fires now that only `hall.js`
sets `dataset.view`, so those elements stayed permanently hidden already.

### Commands run and results

```
node data/test_woven_model.mjs                    PASS
node scripts/test-hall.mjs                         PASS
python3 data/test_hall_assets.py                   PASS (5 checks)
python3 data/test_site_data.py                     PASS
python3 data/test_navigation.py                    PASS
python3 data/test_map.py                            PASS
python3 data/test_wiki_publications.py              PASS
python3 data/test_woven_layout.py                   PASS
python3 data/test_woven_usability.py                PASS
python3 scripts/generate_okf_wiki.py --check        validated 249 markdown files
npm run build:css                                   tailwind.css unchanged
python3 scripts/review_hall.py --output <scratchpad>/final-review
                                                     158 checks, 0 errors, 0 uncaught browser errors
```

`test_evidence.py` and `test_source_catalog.py` were skipped; this checkout
has no local evidence corpus. Screenshots reviewed from `final-review/`:
`desktop-entrance`, `desktop-dense-1970s`, `desktop-sheet-focus`,
`desktop-volume-open` and the reading pose, `desktop-flat-timeline`,
`desktop-filtered`, `desktop-simplified`, `mobile-entrance`,
`mobile-sheet-focus`, and `mobile-reading-sheet`. No visible textile or
"woven" language on screen anywhere.

A note for the record: `docs/js/hall/*.js` changed under this session while
package 4 ran, from work outside this package's scope (per the
instruction to leave `docs/js/hall/` untouched, nothing there was edited
here). `node scripts/test-hall.mjs` failed once mid-session on a signature
mismatch in `matchingOrder` and passed again once that settled; the final
run above is the current state.
