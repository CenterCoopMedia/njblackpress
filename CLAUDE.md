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
- `docs/era.html`: Historical era selected with `?id=`.
- `docs/map.html`: Publication map and decade filter.
- `docs/woven.html`: Interactive timeline loom.
- `docs/wiki/`: Generated public HTML wiki.

The scripts in `docs/js/` support the main site. Most older scripts use the
IIFE pattern. Woven uses ES modules under `docs/js/woven/` and vendored Three.js
files under `docs/vendor/`.

`docs/js/site-nav.js` defines the shared site navigation. Update its regression
check when you change the global navigation.

## Data sources

- `data/publications.csv`: Notion export for base publication fields.
- `data/publications.json`: Pipeline publication data.
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
- `docs/data/events.json`
- `docs/data/stories.json`
- `data/map-publications.json`
- `docs/data/map-publications.json`
- `docs/wiki/`
- `okf/`

Run the smallest builder that covers the source change:

```bash
cd data
python3 convert_csv.py
python3 merge_research.py
python3 add_evidence.py
cd ..
python3 data/build_site_events_stories.py
python3 data/build_map_data.py
python3 scripts/generate_html_wiki.py --base-url https://centercoopmedia.github.io/njblackpress/
python3 scripts/generate_okf_wiki.py
python3 scripts/generate_okf_wiki.py --check
```

`convert_csv.py` rebuilds publication data from the CSV and reattaches evidence.
Run `merge_research.py` and `add_evidence.py` after it when research enrichment
must also be applied and copied to the browser data.

The HTML wiki generator also rebuilds Tailwind unless `--skip-css` is present.
Always pass the live Pages URL through `--base-url`.

## Evidence and rights

Evidence is traceable by publication ID through the source catalog. The rights
manifest controls whether each evidence file can be published.

Do not hand-edit a publication's `evidence` array. Update the source catalog or
rights manifest, then run `data/add_evidence.py`.

Do not publish a file marked `metadata_only` or `unlisted`. Follow the citation
and crop requirements for `publishable_with_credit` and `crop_first` files.

## Validation

Run the focused checks for the changed area. Useful checks include:

```bash
npm run build:css
python3 data/test_site_data.py
python3 data/test_source_catalog.py
python3 data/test_map.py
python3 data/test_navigation.py
python3 data/test_wiki_publications.py
python3 data/test_woven_layout.py
python3 data/test_woven_usability.py
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
- Use query parameters for publication, story, and era detail routes.
- Keep changes focused. Do not edit generated files without their source.
- Preserve unrelated worktree changes.
