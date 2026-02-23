# CLAUDE.md

## Project Overview

NJ Black Press Database — a historical archive documenting Black publications in New Jersey from 1880 to present day. Built as a static website with a JSON/CSV data layer, owned by the [Center for Cooperative Media](https://centerforcooperativemedia.org/).

The dataset catalogs ~138 publications (newspapers, magazines, newsletters, digital outlets) spanning 45+ cities and 15 decades.

## Architecture

**Static site** — no build step, no backend, no package manager. Vanilla JavaScript, Tailwind CSS via CDN, deployed from `/docs/` (GitHub Pages).

```
njblackpress/
├── data/                    # Source data + processing scripts
│   ├── publications.csv     # Primary dataset (exported from Notion)
│   ├── publications.json    # Generated JSON (used by the site)
│   ├── featured-publications.json  # Curated detailed records
│   ├── convert_csv.py       # CSV → JSON converter
│   ├── merge_research.py    # Merges research findings into JSON
│   ├── publications/        # 138 individual .md files (Notion exports)
│   └── research/            # 6 batch JSON files of research findings
├── docs/                    # Static website (GitHub Pages root)
│   ├── index.html           # Landing page (hero, timeline, search)
│   ├── archive.html         # Full directory with advanced filtering
│   ├── publication.html     # Individual publication detail page
│   ├── css/styles.css       # Custom styles (extends Tailwind)
│   ├── js/
│   │   ├── app.js           # Landing page logic
│   │   ├── archive.js       # Archive page filtering/search/views
│   │   ├── publication.js   # Publication detail rendering
│   │   ├── timeline.js      # SVG timeline visualization
│   │   └── featured.js      # Featured publications showcase
│   └── data/                # Deployed data files (copies of above)
│       ├── publications.json
│       └── featured-publications.json
├── featured/                # Featured content markdown
├── images/                  # Image assets
├── README.md                # Project documentation
└── CLAUDE.md                # This file
```

## Data Pipeline

The data flows from Notion exports through Python scripts to the website:

```
Notion → data/publications.csv
              ↓
         convert_csv.py  →  data/publications.json
              ↓
         merge_research.py (enriches from data/research/*.json)
              ↓
         Copy to docs/data/publications.json (manual)
```

### Running data scripts

Scripts must be run from the `data/` directory:

```bash
cd data/
python3 convert_csv.py          # Regenerate publications.json from CSV
python3 merge_research.py       # Merge research findings into publications.json
```

After running scripts, copy updated files to `docs/data/`:
```bash
cp data/publications.json docs/data/publications.json
```

The `featured-publications.json` file is curated separately and lives in both `data/` and `docs/data/`.

## Data Schema

Each publication record in `publications.json`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique identifier |
| `name` | string | Publication name |
| `alternateName` | string\|null | Other names used |
| `city` | string\|null | Primary city of operation |
| `publishers` | string\|null | Publishing entity or individuals |
| `yearFounded` | int\|null | Start year |
| `yearCeased` | int\|null | End year (null if still active) |
| `frequency` | string\|null | Weekly, monthly, daily, etc. |
| `format` | string\|null | Newspaper, periodical, digital |
| `languages` | string | Primary language(s), defaults to "English" |
| `archiveUrl` | string\|null | Library of Congress/WorldCat/Internet Archive links |
| `websiteUrl` | string\|null | Current website URL |
| `targetAudience` | string\|null | Intended readership |
| `primaryFocus` | string\|null | Subject matter coverage |
| `medium` | string | "Print", "Digital", or "Print/Digital" |
| `missionStatement` | string\|null | Editorial philosophy |
| `keyStaff` | string\|null | Notable editors/publishers |
| `historicalNotes` | string\|null | Context and significance |
| `isActive` | bool | Whether the publication is still operating |
| `decade` | string | Decade of founding (e.g. "1880s") |
| `isFeaturedHistoric` | bool | Highlighted in historic section |
| `isFeaturedContemporary` | bool | Highlighted in contemporary section |

The JSON file also includes a `metadata` object with: `totalCount`, `cities`, `decades`, `formats`, `activeCount`, `ceasedCount`.

## Frontend Conventions

### JavaScript

- All modules use **IIFE pattern**: `(function() { ... })()`
- Data loading via **Fetch API** with error handling
- State managed as plain objects; UI re-renders on state changes
- Search input **debounced** at 300ms
- Archive page persists filter state in **URL query parameters** for shareability
- Pagination uses "Load More" pattern (not page numbers)
- No framework, no module bundler, no transpilation

### CSS / Styling

- **Tailwind CSS** loaded from CDN — no local build
- Custom Tailwind config injected via inline `<script>` in HTML files
- Color palette: `ink` (dark background), `paper` (light text), `accent` (orange highlights)
- Fonts: Fraunces (serif headings), DM Sans (sans-serif body) via Google Fonts CDN
- Mobile-first responsive design
- Dark "Newspaper Noir" aesthetic throughout

### HTML

- Three pages: `index.html`, `archive.html`, `publication.html`
- Semantic HTML with ARIA attributes for accessibility
- Publication detail page loads from URL parameter: `publication.html?id=123`

## Python Requirements

- Python 3.x (tested with 3.11)
- Standard library only — no pip dependencies (`csv`, `json`, `re`, `os`, `glob`)

## Key Conventions

- **No build step** — all files served as-is. Changes to HTML/CSS/JS are immediately effective.
- **Two copies of data** — source data lives in `data/`, deployed copies in `docs/data/`. Keep them in sync manually after regeneration.
- **Featured publications** are hardcoded in `convert_csv.py` (`featured_historic` and `featured_contemporary` lists). Update these lists when adding new featured publications.
- **merge_research.py fills gaps only** — it never overwrites existing non-null values.
- **No tests** — there is no test suite. Verify changes manually by opening the HTML files.
- **No CI/CD** — deployment is via GitHub Pages from the `docs/` directory.

## Common Tasks

### Adding a new publication
1. Add a row to `data/publications.csv`
2. Run `cd data && python3 convert_csv.py`
3. Copy `data/publications.json` to `docs/data/publications.json`

### Featuring a publication
1. Edit the `featured_historic` or `featured_contemporary` lists in `data/convert_csv.py`
2. Add detailed content to `data/featured-publications.json`
3. Regenerate and copy as above

### Modifying the website
- Edit HTML files directly in `docs/`
- Edit JS files in `docs/js/`
- Edit styles in `docs/css/styles.css` (or use Tailwind utility classes inline)
- No build, reload the browser to see changes

### Adding research findings
1. Add a JSON file to `data/research/` matching the expected schema (array of objects with `id` and field values)
2. Run `cd data && python3 merge_research.py`
3. Copy `data/publications.json` to `docs/data/publications.json`

## External Dependencies (CDN)

- Tailwind CSS (via CDN)
- Google Fonts: Fraunces, DM Sans
- No npm packages, no local dependencies

## Gotchas

- The `data/` directory contains the _source of truth_ for data. The `docs/data/` copies are what the website reads. They can drift apart if you forget to copy after regeneration.
- Year parsing is lenient — `convert_csv.py` extracts the first 4-digit number from any string. Values like "1880?" or "c. 1920" work fine.
- `isActive` is determined by absence of a `yearCeased` value, not an explicit flag in the CSV. **Caveat:** `?` in yearCeased is treated the same as empty, so publications with an unknown cease date are marked Active. This inflates the active count — 56 pre-1990 publications are currently marked Active despite likely being defunct. A data curation decision, not a bug.
- The Tailwind config (colors, fonts, etc.) is duplicated in each HTML file's inline `<script>` tag. Changes must be applied to all three HTML files.
- Publication detail page (`publication.html`) loads from two data sources (`publications.json` + `featured-publications.json`) and merges them for display.
- ID 128 ("Newark Black Newspapers Collection") is a Rutgers digital library collection, not a standalone publication. Its own `historicalNotes` flag this. It's kept for reference but `isActive: false` and `format: "Digital archive collection"`.
- The CSV uses UTF-8 BOM (`\ufeff`) on the first column. Read with `encoding='utf-8-sig'` in Python.

## Changes log

### 2026-02-23 — SEO, repo hygiene, data audit

**SEO / LLMEO**
- Added `docs/favicon.svg` (dark background, orange "NJ" text)
- Copied `og-image.png` to `docs/` (was only in repo root, not served by GitHub Pages)
- Created `docs/robots.txt` with explicit AI crawler allowances
- Created `docs/llms.txt` (llmstxt.org standard)
- Generated `docs/sitemap.xml` (137 publication URLs + 2 main pages)
- Added full OG + Twitter Card meta tags + `<link rel="canonical">` to all 3 HTML pages
- Added JSON-LD structured data (WebSite + Dataset) to `index.html`
- Updated `docs/js/publication.js` to dynamically rewrite OG/canonical tags per publication

**Repo hygiene**
- Merged PRs #8 (CLAUDE.md) and #9 (CODEBASE_OVERVIEW.md)
- Rewrote `README.md` with accurate schema docs, data pipeline, and prominent live site link
- Set GitHub repo description, homepage URL, and 8 topic tags

**Data fixes**
- The Sentinel (ID 10): `isActive: false`, `yearCeased: 1882` (was showing Active)
- Unity and Struggle (ID 84): `isActive: false`, `yearCeased: 1978` (was showing Active)
- The Black Voice (ID 107): added `yearCeased: 1975`, `isActive: false`
- Deliverance Voice featured card: corrected ID `108 → 70` (108 is Educational Perspectives)
- Removed duplicate ID 60 (Black Women's United Front Newsletter) — ID 126 is the complete record; featured card updated to point at 126
- ID 128: `isActive: false`, `format: "Digital archive collection"` (it's a Rutgers library collection)
- Updated counts throughout: totalCount `138 → 137`, activeCount `97 → 95`

**Pending (curator decision)**
- 56 pre-1990 publications with `?` yearCeased are marked Active — the Notion source data uses `?` to mean "unknown," not "still running." Fixing requires either updating the CSV or changing the `isActive` logic in `convert_csv.py`.
