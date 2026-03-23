# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

NJ Black Press Database — a static site documenting ~140 Black-owned and Black-focused publications in New Jersey from 1880 to present. Built for the Center for Cooperative Media at Montclair State University. Hosted on GitHub Pages from the `docs/` folder.

## Development

**No build step.** The site is vanilla HTML/JS/CSS with Tailwind via CDN. To develop locally, serve the `docs/` folder with any static server:

```bash
cd docs && python -m http.server 8000
```

**Data pipeline:** Notion → CSV export → Python conversion → JSON

```bash
cd data && python convert_csv.py
```

This reads `data/publications.csv` and outputs `data/publications.json`. The generated JSON must then be copied to `docs/data/publications.json` for the frontend. `docs/data/featured-publications.json` is hand-curated and edited directly.

## Architecture

Static site with three HTML pages, no framework, no bundler:

- **`docs/index.html`** — Landing page (hero, featured sections, timeline, searchable database, about)
- **`docs/archive.html`** — Full archive with list/grid toggle, filters, sorting, pagination
- **`docs/publication.html`** — Individual publication detail (loaded via `?id=X` query param)

### JavaScript modules (IIFE pattern, no imports)

- **`docs/js/app.js`** — Core state management, filtering, search, pagination, card rendering. Exposes `window.njbp` for cross-module communication (`removeFilter`, `resetFilters`, `getState`, `filterByDecade`).
- **`docs/js/timeline.js`** — Interactive decade timeline with bar chart visualization. Calls `window.njbp.filterByDecade()`.
- **`docs/js/featured.js`** — Loads and merges `featured-publications.json` with main data for rich featured sections.
- **`docs/js/archive.js`** — Archive page filtering and display logic.
- **`docs/js/publication.js`** — Detail page rendering from query param ID.

### State management

`app.js` uses a single `state` object with `publications`, `filteredPublications`, `filters` (search, city, decade, status, format), `sortBy`, `currentPage`, and `perPage` (24). Filters are applied sequentially; search is debounced at 300ms.

## Data model

**`publications.json`** contains an array of publication objects and a `metadata` block (totalCount, cities, decades, formats, activeCount, ceasedCount). Each publication has: `id`, `name`, `alternateName`, `city`, `publishers`, `yearFounded`, `yearCeased`, `frequency`, `format`, `medium` (computed: Print/Digital/Print+Digital), `languages`, `primaryFocus`, `missionStatement`, `historicalNotes`, `archiveUrl`, `websiteUrl`, `targetAudience`, `keyStaff`, `isActive` (computed: true if yearCeased is null), `decade` (computed from yearFounded).

**`featured-publications.json`** has `featuredHistoric` (11 entries) and `featuredContemporary` (5 entries) with expanded fields: `founders`, `keyStaff` as objects (`{name, role}`), `tags`, `physicalArchive`.

## Styling

Tailwind CSS via CDN with inline config extending colors and fonts:

- **Colors:** ink-950 through ink-700 (dark backgrounds), paper-50 through paper-300 (light text), accent #ff4d00 (orange)
- **Fonts:** Fraunces (serif headings), DM Sans (body), system monospace (labels/filters)
- **Custom CSS** in `docs/css/styles.css`: scrollbar styling, noise grain overlay, timeline bars

## Deployment

GitHub Actions is disabled for the CenterCoopMedia org, so GitHub Pages builds are stuck. Deploy via SFTP to the CCM WordPress server instead.

**SFTP deploy (from officejawn or houseofjawn):**
```bash
# Credentials in pass store
HOST=37.27.121.163
PORT=4377
USER=$(~/.claude/pass-get claude/services/ccm-ftp-user)
PASS=$(~/.claude/pass-get claude/services/ccm-ftp-pass)

# Upload all static files
sshpass -p "$PASS" scp -P $PORT -o StrictHostKeyChecking=no docs/*.html docs/*.xml docs/*.txt docs/*.png docs/*.svg $USER@$HOST:public_html/njblackpress/
sshpass -p "$PASS" scp -P $PORT -o StrictHostKeyChecking=no docs/css/* $USER@$HOST:public_html/njblackpress/css/
sshpass -p "$PASS" scp -P $PORT -o StrictHostKeyChecking=no docs/js/* $USER@$HOST:public_html/njblackpress/js/
sshpass -p "$PASS" scp -P $PORT -o StrictHostKeyChecking=no docs/data/* $USER@$HOST:public_html/njblackpress/data/
```

**Live URLs:**
- Production: `https://centerforcooperativemedia.org/njblackpress/` (WordPress serves the page, static files load from `public_html/njblackpress/`)
- GitHub Pages (stale): `https://centercoopmedia.github.io/njblackpress/`

**Note:** The WordPress page at `/njblackpress/` renders our `index.html` content within the Brooklyn theme wrapper. JS/CSS/data load via relative paths from the static directory. The bare URL path is handled by WordPress; direct file paths (e.g., `/njblackpress/archive.html`) serve our static files.

**Data pipeline caveat:** The JSON has been enriched with fields (`historicalNotes`, `missionStatement`, etc.) that don't exist in the CSV. Do NOT re-run `convert_csv.py` to regenerate the JSON — it will wipe those fields. Edit the JSON directly for metadata changes.

## Conventions

- Sentence case for all headings and UI text (never Title Case)
- CCM brand colors: #000000 (black) and #CA3553 (red) for organizational branding; site uses its own palette (ink/paper/accent)
- External links open in new tabs with `target="_blank" rel="noopener noreferrer"`
- Publication detail pages use client-side routing via query params, not separate HTML files per publication
