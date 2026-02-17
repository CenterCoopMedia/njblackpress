# NJ Black Press Database — Codebase Overview

## What It Does

A static website cataloging **138+ Black publications in New Jersey from 1880 to present**. It provides a searchable/filterable archive, featured publication showcases, an interactive decade-by-decade timeline, and individual publication detail pages. Built for the **Center for Cooperative Media** at Montclair State University.

## Tech Stack

| Layer | Technology |
|---|---|
| Markup | Static HTML5 (3 pages) |
| Styling | Tailwind CSS 3 (CDN) + custom CSS |
| JavaScript | Vanilla ES6+ (~2,000 LOC across 5 IIFE modules, no framework) |
| Data | Static JSON files (no database, no backend server) |
| Data pipeline | Python 3 scripts (CSV → JSON conversion) |
| Hosting | GitHub Pages (served from `docs/` folder) |
| Fonts | Google Fonts (Fraunces serif, DM Sans sans-serif) |

## Main Entry Points

### Pages

- **`docs/index.html`** — Homepage with hero stats, hardcoded featured publications, interactive timeline, and database search section
- **`docs/archive.html`** — Full searchable/filterable directory with grid and list views, URL state persistence
- **`docs/publication.html`** — Individual publication detail page (loaded via `?id=` query parameter)

### JavaScript Modules

All modules use the IIFE pattern and are loaded per-page:

- **`docs/js/app.js`** (~490 lines) — Homepage: data loading, filtering, search, card rendering, counter animation
- **`docs/js/archive.js`** (~607 lines) — Archive page: advanced filters, URL state sync, grid/list views, pagination
- **`docs/js/publication.js`** (~440 lines) — Detail page: multi-source data loading, rich content rendering, related publications
- **`docs/js/featured.js`** (~299 lines) — Featured publications rendering with expand/collapse
- **`docs/js/timeline.js`** (~231 lines) — Interactive bar chart timeline with decade navigation

### Data Pipeline

- **`data/publications.csv`** — Master source data (exported from Notion)
- **`data/convert_csv.py`** — Converts CSV → `publications.json` with derived fields (decade, isActive, medium)
- **`data/merge_research.py`** — Merges enriched research data into publication records
- **`data/publications.json`** — Runtime data file (138 publications with full metadata)
- **`data/featured-publications.json`** — Enriched data for highlighted publications
- **`data/research/`** — 6 batch JSON files of historical research findings
- **`data/publications/`** — 130+ individual Markdown files per publication

## Project Structure

```
njblackpress/
├── docs/                          # Static website (GitHub Pages root)
│   ├── index.html                 # Homepage
│   ├── archive.html               # Full archive directory
│   ├── publication.html           # Publication detail template
│   ├── css/styles.css             # Custom CSS (scrollbars, animations, responsive)
│   ├── js/                        # JavaScript modules
│   │   ├── app.js
│   │   ├── archive.js
│   │   ├── featured.js
│   │   ├── timeline.js
│   │   └── publication.js
│   ├── data/                      # Runtime data files
│   │   ├── publications.json
│   │   └── featured-publications.json
│   └── images/
├── data/                          # Data layer (source of truth)
│   ├── publications.csv           # Master CSV from Notion
│   ├── publications.json          # Generated JSON
│   ├── featured-publications.json
│   ├── convert_csv.py             # CSV → JSON converter
│   ├── merge_research.py          # Research data merger
│   ├── publications/              # Individual markdown records (130+)
│   └── research/                  # Batch research JSON files
└── README.md
```

## Security Vulnerabilities

### 1. XSS via unescaped URLs in `href` attributes (Medium)

Multiple files interpolate `pub.websiteUrl` and `pub.archiveUrl` directly into HTML `href` attributes without escaping. While text content is properly escaped via `escapeHtml()`, URLs are not. A value like `javascript:alert(1)` in the JSON data would execute.

**Affected locations:**
- `app.js:276-279` — `websiteLink` and `archiveLink`
- `archive.js:373-376` — `pub.websiteUrl` in grid cards
- `publication.js:324,335` — `pub.websiteUrl` and `pub.archiveUrl`
- `featured.js:104,207` — `pub.archiveUrl` and `websiteUrl`

The `archiveUrl.startsWith('http')` check in some places partially mitigates this, but `websiteUrl` has no such guard.

### 2. Inline `onclick` handlers with string interpolation (Low)

- `app.js:365` — `onclick="window.njbp.removeFilter('${f.type}')"`
- `archive.js:437-443` — Same pattern with `chip.type`
- `timeline.js:209` — `onclick="window.njbp.filterByDecade('${decade.label}')"`

Values currently come from hardcoded sources so this is safe in practice, but the pattern is fragile and invites injection if data sources change.

### 3. URL parameters used without validation (Low)

`archive.js:63-71` reads `sort` and `view` from URL params and sets them directly into state without validating against allowed values. This doesn't lead to XSS but crafted URLs could produce unexpected UI behavior.

### 4. Tailwind CSS CDN loaded without Subresource Integrity (Low)

All three HTML pages load `https://cdn.tailwindcss.com` without an `integrity` attribute. A CDN compromise would allow arbitrary script execution.

## Inefficiencies

### 1. Triple-loading `publications.json` on the homepage

The homepage loads `app.js`, `timeline.js`, and (if included) `featured.js`, each of which independently `fetch('data/publications.json')`. That's up to 3 identical HTTP requests on every homepage load. Browser caching helps on repeat visits but the first load is wasteful. A shared data loader would fix this.

### 2. Full DOM re-render on every filter/sort change

`app.js:260` and `archive.js:335` reconstruct the entire results grid via `innerHTML = ...map(...).join('')` on every interaction. For 138 records this is fast enough, but it discards and recreates all DOM nodes unnecessarily.

### 3. Duplicated utility functions across all 5 JS files

`escapeHtml()`, `truncate()`, `debounce()`, `animateCounter()`, `getOneLiner()`, and `hideLoadingOverlay()` are copy-pasted across multiple files. Bug fixes must be applied in 3-5 places.

### 4. Tailwind CSS JIT build in production

All pages use `<script src="https://cdn.tailwindcss.com">` which is the JIT development build. Tailwind's docs explicitly warn against this for production. It loads ~300KB+ of JavaScript to generate CSS at runtime. A build step producing a purged CSS file would reduce this to a few KB.

### 5. Google Fonts loaded render-blocking

Font `<link>` tags are render-blocking. Using `media="print" onload="this.media='all'"` or `font-display: optional` would improve Largest Contentful Paint (LCP).

### 6. Fixed grain overlay at z-50

A full-viewport `<div>` with `z-50` is rendered permanently for a noise texture effect. While `pointer-events-none` prevents interaction issues, it forces a compositing layer on every frame.
