# Historical notes review

Historical notes presents the archive as a time map and a flat timeline. The
time map places publications at recorded towns and uses height for recorded
publication years. It uses the Census 2023 New Jersey outline and the existing
map centers. A displaced cluster is an approximate display position and does
not identify a publisher address.

The page preserves uncertainty. Unknown founding or end dates remain explicit.
Unknown places stay on their recorded shelf. A year-only event date stays a
year-only date. Events before 1880 are marked as before the map begins.
Evidence images appear only when the exact event source has a permitted public
clip. Citations and crop notices stay with those images.

The year plane counts only titles with recorded spans. It reports the separate
count of titles with unrecorded years.

## Routes and views

The public route is `historical-notes.html`. Canonical view values are
`?view=map` and `?view=flat`. `?view=woven` and `?view=3d` resolve to the time
map. `?view=timeline` resolves to the flat timeline.

The page accepts `?pub=ID` and the legacy `?id=ID` publication links,
`?story=ID&stop=N`, `?year=YYYY`, and `?nogl=1`. `?nogl=1` promotes the full
text archive. The legacy `woven.html` route forwards its query and fragment.

## Required checks

Run the focused checks before a pull request:

```bash
npm run build:css
python3 data/test_site_data.py
python3 data/test_navigation.py
node data/test_notes_model.mjs
python3 scripts/review_notes.py --output /tmp/notes-review
```

Review the browser output before merge. Check all 13 stories, a real WebGL time
map, the year plane, pointer selection, keyboard navigation, mobile layouts,
reduced motion, the flat view, and the no-WebGL fallback. Check that every
story image has a permitted exact source match and that the complete list stays
usable with JavaScript visual rendering unavailable.

GitHub Pages publishes `docs/` from `master`. Verify the Pages build and the
public route after merge.
