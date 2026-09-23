# NJ Black Press Archive: Repository instructions

## Project overview

This repository contains a static historical archive of Black-owned and
Black-focused publications in New Jersey from 1880 to the present. The Center
for Cooperative Media at Montclair State University maintains it.

GitHub Pages publishes the `docs/` directory from `master`. The live site is
`https://centercoopmedia.github.io/njblackpress/`.

The project has no backend, database server, or JavaScript framework.

## Development

The site uses static HTML, CSS, and JavaScript. Tailwind CSS is compiled, not
loaded from a CDN.

```bash
npm ci
npm run build:css
cd docs
python3 -m http.server 8000
```

`docs/css/tailwind.css` is generated. Never edit it by hand. Rebuild it after
you add or change a Tailwind class in HTML or JavaScript.

Tailwind scans `docs/**/*.html` and `docs/js/**/*.js`. JavaScript class names
must use complete literal strings. Add a dynamic class to the safelist in
`tailwind.config.js` when a literal is not possible.

## Site architecture

Main pages:

- `docs/index.html`: Home, featured records, timeline, and search.
- `docs/archive.html`: Filterable publication directory.
- `docs/publication.html`: Publication detail selected with `?id=`.
- `docs/story.html`: Sourced narrative selected with `?id=`.
- `docs/era.html`: Historical era selected with `?decade=`.
- `docs/map.html`: Publication map and decade filter.
- `docs/historical-notes.html`: Guided stories, an era index, and a
  publication browser, shown through the history hall by default. Three.js
  renders each publication as a framed sheet in founding order, with a
  section per decade and a section for unrecorded dates. Each guided story is
  a bound volume on a reading table, read through a DOM reader. A flat
  timeline gives the precise view for comparing exact dates. Canvas 2D
  supports browsers without WebGL, and the full text archive is the last
  fallback. `?nogl=1` opens the text archive without fetching Three.js. See
  `WOVEN_REVIEW.md` for what each view shows, its routes in full, and the
  checks to run. `docs/woven.html` forwards old links and preserves their
  query and fragment.
- `docs/wiki/`: Generated public HTML wiki.

The scripts in `docs/js/` support the main site. Most older scripts use the
IIFE pattern. Historical notes uses ES modules under `docs/js/woven/` (data,
the flat timeline, the record panel, fallbacks) and `docs/js/hall/` (the
history hall: layout, state, the room, the sheets, the reading tables and
their reader, routing), plus vendored Three.js files under `docs/vendor/`.

`docs/js/site-nav.js` defines the shared site navigation. Update its regression
check when you change the global navigation.

## Design system

- Colours: `walnut`, `oak`, `linen`, `thread`, and `stain` in
  `tailwind.config.js`. Do not add Tailwind default colours or raw white.
  `src/input.css` exposes the same tokens as CSS variables (`--walnut-900`,
  `--stain`, `--font-display`, `--mono`) for hand-written CSS.
- Fonts: Libre Franklin for display, DM Sans for text, the system monospace
  stack for labels. Every page loads the same Google Fonts link.
- Header and footer: `docs/js/site-nav.js` renders the navigation links and the
  footer into `<footer data-site-footer>`. Keep the footer outside `<main>`.
- Focus: `docs/css/styles.css` holds the one `:focus-visible` rule. Do not use
  `focus:outline-none` or a per-page focus colour.
- Mobile menu: `site-nav.js` builds it as a modal dialog on every page. A page
  supplies only a `#mobile-menu-btn` button or an `a.md:hidden` placeholder.
- Targets: interactive elements are at least 44px tall where they stand alone.
  `min-height` has no effect on an inline link; use `inline-flex` or padding.
- Motion: `styles.css` stops animation and smooth scrolling under
  `prefers-reduced-motion`.
- `data/test_design_system.py` enforces these rules, and
  `scripts/review_site.py` checks them in a browser.

## Data sources

- `data/publications.json`: Current publication record.
- `data/publications.csv`: Notion export for a controlled full refresh only.
- `data/research/source-catalog.json`: Source searches and retained evidence.
- `data/research/rights/rights-manifest.json`: Rights decisions for evidence.
- `data/research/editorial/events.json`: Editorial event source.
- `data/research/editorial/stories.json`: Editorial story source.
- `data/municipality-centers.json`: Map grouping and coordinate rules.
- `data/featured-publications.json`: Hand-curated featured records.

Read `data/DATA_DICTIONARY.md` before you change a data contract.

## Generated files

Do not hand-edit these outputs:

- `docs/css/tailwind.css`
- `docs/data/publications.json`
- `docs/data/featured-publications.json`
- `docs/data/events.json`
- `docs/data/stories.json`
- `docs/data/clippings.json`
- `docs/data/wall-copies.json`
- `docs/images/evidence/`
- `docs/images/evidence/wall/`
- `data/map-publications.json`
- `docs/data/map-publications.json`
- `docs/wiki/`
- `docs/sitemap.xml`
- `docs/og-image.png`, `docs/favicon-32.png`, `docs/apple-touch-icon.png`
- `okf/`

Run the smallest builder that covers the source change:

```bash
python3 data/add_evidence.py
cp data/featured-publications.json docs/data/featured-publications.json
cmp data/featured-publications.json docs/data/featured-publications.json
python3 data/build_site_events_stories.py
python3 data/build_map_data.py
python3 data/make_wall_copies.py
python3 scripts/generate_html_wiki.py --base-url https://centercoopmedia.github.io/njblackpress/
python3 scripts/generate_okf_wiki.py
python3 scripts/generate_okf_wiki.py --check
python3 scripts/build_sitemap.py
python3 scripts/make_social_assets.py
```

Run `scripts/build_sitemap.py` after a change adds or removes a publication,
story, or decade. Run `scripts/make_social_assets.py` after a visible change to
the home page hero or the navigation; it recaptures the shared social card.

Every public page uses the same head: a title that ends with
`| NJ Black Press Archive` (the home page title is the name alone), a
description, Open Graph and Twitter tags with the shared `og-image.png` and its
alt text, `theme-color`, the SVG favicon, `favicon-32.png`, and
`apple-touch-icon.png`. `data/test_site_metadata.py` enforces it.

The checked-in CSV is stale relative to the current publication record. Do not
run `data/convert_csv.py` for a routine correction. Use it only for a controlled
full refresh after you replace the CSV with a fresh Notion export. Review the
full diff and prove that the refresh preserves curated fields, record count,
publication IDs, cessation years, and active status.

For a routine publication correction, update `data/publications.json`, run
`data/add_evidence.py`, and review both publication JSON files. The builder
also rewrites the derived metadata. To add a Library of Congress directory
record as evidence, run `python3 data/attach_loc_records.py <id>:<lccn>`, then
`data/add_evidence.py`. Use
`data/merge_research.py` only for a reviewed research-enrichment batch.

The HTML wiki generator also rebuilds Tailwind unless `--skip-css` is present.
Always pass the live Pages URL through `--base-url`.

## Evidence and rights

Evidence is traceable by publication ID through the source catalog. The rights
manifest controls whether each evidence file can be published.

Do not hand-edit a publication's `evidence` array. Update the source catalog or
rights manifest, then run `data/add_evidence.py`.

Do not publish a file marked `metadata_only` or `unlisted`. Follow the citation
and crop requirements for `publishable_with_credit` and `crop_first` files.

A rights change also affects the public clipping index and its image files. In
a checkout with the full evidence corpus, record the affected clipping output,
then run `python3 data/make_clippings.py`. Remove each old file under
`docs/images/evidence/` that the new `docs/data/clippings.json` no longer lists.
Confirm that a downgraded source path is absent from the clipping index and its
old public image no longer exists. Review both paths before commit.

## Validation

Run the focused checks for the changed area. Useful checks include:

```bash
npm run build:css
python3 data/test_site_data.py
python3 data/test_publication_record.py
python3 data/test_site_metadata.py
python3 data/test_design_system.py
python3 data/test_source_catalog.py
python3 data/test_map.py
python3 data/test_navigation.py
python3 data/test_wiki_publications.py
python3 data/test_woven_layout.py
python3 data/test_woven_usability.py
python3 data/test_hall_assets.py
node scripts/test-hall.mjs
python3 scripts/review_hall.py
python3 scripts/review_site.py
python3 scripts/generate_okf_wiki.py --check
```

`test_evidence.py` and `test_source_catalog.py` require the local evidence
corpus. Git ignores most large research files, so those checks fail in a normal
clone without the corpus.

Data changes must keep source and browser copies equal. Generated wiki changes
must include their generated outputs. Visible changes need desktop and mobile
browser checks.

## Deployment

GitHub Pages uses the `master` branch and the `docs/` directory. A merge that
changes `docs/` publishes those changes. Verify the Pages build and the live
route after merge.

Do not use the retired SFTP deployment instructions or the former WordPress
host without a new, verified deployment decision.

## Project updates

After a merged achievement, post a plain-language update to the
[Road to launch discussion](https://github.com/CenterCoopMedia/njblackpress/discussions/47).
Use three to six sentences. Explain what changed, why it matters, and what
comes next. Do not include file paths or engineering jargon.

## Conventions

- Use sentence case for headings and interface text.
- Open external links in a new tab with `target="_blank"` and
  `rel="noopener noreferrer"`.
- Use `?id=` for publication and story details. Use `?decade=` for era details.
- Keep changes focused. Do not edit generated files without their source.
- Preserve unrelated worktree changes.
