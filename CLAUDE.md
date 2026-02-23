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
- `isActive` is determined by absence of a `yearCeased` value, not an explicit flag in the CSV.
- The Tailwind config (colors, fonts, etc.) is duplicated in each HTML file's inline `<script>` tag. Changes must be applied to all three HTML files.
- Publication detail page (`publication.html`) loads from two data sources (`publications.json` + `featured-publications.json`) and merges them for display.
