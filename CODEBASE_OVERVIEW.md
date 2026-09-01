# NJ Black Press Archive: Codebase overview

## System boundary

The project is a static site. Browsers load HTML, CSS, JavaScript, and JSON from
GitHub Pages. There is no application server, database server, authentication,
or write API.

Python scripts build data and pre-rendered pages before publication. GitHub
Pages serves the committed results from `docs/`.

## Public surfaces

| Surface | Entry point | Main data |
|---|---|---|
| Home and timeline | `docs/index.html` | Publications and featured records |
| Archive | `docs/archive.html` | Publications |
| Publication detail | `docs/publication.html?id=` | Publications, evidence, and recent stories |
| Stories | `docs/story.html?id=` | Stories, events, and publications |
| Eras | `docs/era.html?decade=` | Events, stories, and publications |
| Map | `docs/map.html` | Generated map publication data |
| Woven | `docs/woven.html` | Publications, stories, events, and evidence |
| Public wiki | `docs/wiki/` | Pre-rendered publication and browse pages |
| Portable wiki | `okf/` | Markdown pages with YAML frontmatter |

## Frontend organization

The main site scripts live in `docs/js/`:

- `app.js`: Home data loading, filters, cards, and counters.
- `archive.js`: Archive filters, sorting, URL state, and pagination.
- `publication.js`: Publication details, evidence, and related records.
- `featured.js`: Featured record sections.
- `timeline.js`: Decade timeline.
- `story.js`: Story detail rendering.
- `era.js`: Era detail rendering.
- `map.js`: Map rendering and decade filtering.
- `site-nav.js`: Shared navigation.

Woven uses ES modules under `docs/js/woven/`. Its modules separate data,
layout, rendering, labels, selection, story tours, evidence panels, fallback
behavior, and first-visit guidance. Three.js is vendored under `docs/vendor/`.

## Styling

`src/input.css` is the Tailwind input. `tailwind.config.js` defines scan paths,
fonts, colors, and the noise texture. `npm run build:css` writes the minified
stylesheet to `docs/css/tailwind.css`.

Custom styles live in:

- `docs/css/styles.css`: Shared site styles.
- `docs/css/woven.css`: Woven layout and rendering interface.
- `docs/css/woven-guide.css`: Woven guidance and progressive controls.

## Data flow

```text
Current publication record
  -> data/publications.json

Source catalog + rights manifest
  -> data/add_evidence.py
  -> data/publications.json
  -> docs/data/publications.json

Hand-curated featured records
  -> data/featured-publications.json
  -> explicit copy and comparison
  -> docs/data/featured-publications.json

Rights manifest + local evidence corpus
  -> data/make_clippings.py
  -> docs/data/clippings.json and docs/images/evidence/

Editorial events and stories
  -> data/build_site_events_stories.py
  -> data/events.json and data/stories.json
  -> docs/data/events.json and docs/data/stories.json

Publications + municipality rules
  -> data/build_map_data.py
  -> data/map-publications.json
  -> docs/data/map-publications.json

Publication data
  -> scripts/generate_html_wiki.py
  -> docs/wiki/
  -> scripts/generate_okf_wiki.py
  -> okf/
```

The `data/` copies are pipeline data. The `docs/data/` copies are browser data.
Builders keep the paired files equal.

`data/convert_csv.py` is for a controlled full refresh from a new Notion CSV.
The checked-in CSV does not reproduce the current curated publication record.
Do not use the converter for a routine correction.

## Generated boundaries

Do not hand-edit compiled CSS, browser data copies, or generated wiki files.
Change the source and run its builder.

The public HTML wiki generator removes and rebuilds `docs/wiki/`. The open
knowledge format generator removes and rebuilds `okf/`. Review the full
generated diff before commit.

The clipping builder rewrites the clipping index but does not remove every old
image. A rights downgrade must also remove any public image that the new index
does not list.

## Validation model

The repository uses small Python checks in `data/test_*.py`. Each check covers
a stable data, navigation, map, wiki, or Woven contract. Run the checks that
match the changed surface.

Browser checks remain necessary for layout, keyboard interaction, focus,
responsive behavior, WebGL, and reduced motion.

## Publication

GitHub Pages serves `docs/` from `master` at
`https://centercoopmedia.github.io/njblackpress/`. A merge can publish the site
without a separate deploy command.
