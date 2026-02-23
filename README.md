# NJ Black Press Archive

**[→ View the live archive](https://centercoopmedia.github.io/njblackpress/)**

A historical database documenting Black publications in New Jersey from 1880 to present day. Built and maintained by the [Center for Cooperative Media](https://centerforcooperativemedia.org/) at Montclair State University.

## Overview

The database catalogs 137 Black-owned and Black-focused publications that have operated in New Jersey — newspapers, magazines, newsletters, and digital outlets. The data spans 145 years of Black press history across 45+ cities statewide.

**Project lead:** Cassandra Etienne, Associate Director of Programming and Membership
**Data curator:** Amanda Alicea
**Project owner:** [Center for Cooperative Media](https://centerforcooperativemedia.org/)

## The website

The archive is a static site deployed via GitHub Pages from the `/docs` directory. It includes:

- **Home** (`/`) — featured historic and contemporary publications, decade timeline, and search preview
- **Archive** (`/archive.html`) — full directory with filtering by city, decade, format, and status
- **Publication** (`/publication.html?id=N`) — individual record pages with full historical detail

No build step. Vanilla JavaScript, Tailwind CSS via CDN.

## Data structure

### Source files

| Path | Contents |
|------|----------|
| `data/publications.csv` | Primary dataset (exported from Notion) |
| `data/publications.json` | Generated JSON (used by the site) |
| `data/featured-publications.json` | Curated records with richer detail |
| `data/convert_csv.py` | CSV → JSON converter |
| `data/merge_research.py` | Merges research findings into JSON |
| `docs/data/` | Deployed copies of the above JSON files |

### Publication record schema

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
| `archiveUrl` | string\|null | Library of Congress, WorldCat, Internet Archive links |
| `websiteUrl` | string\|null | Current website URL |
| `targetAudience` | string\|null | Intended readership |
| `primaryFocus` | string\|null | Subject matter coverage |
| `medium` | string | "Print", "Digital", or "Print/Digital" |
| `missionStatement` | string\|null | Editorial philosophy |
| `keyStaff` | string\|null | Notable editors/publishers |
| `historicalNotes` | string\|null | Context and significance |
| `isActive` | bool | Whether the publication is still operating |
| `decade` | string | Decade of founding (e.g. "1880s") |

### Data pipeline

```
Notion → data/publications.csv
              ↓
         convert_csv.py  →  data/publications.json
              ↓
         merge_research.py (enriches from data/research/*.json)
              ↓
         Copy to docs/data/ (manual step)
```

## Notable publications

### Historical (pre-1950)
- **The Sentinel** (1880, Trenton) — one of NJ's earliest Black newspapers
- **New Jersey Trumpet** (1887–1897, Jersey City / Newark)
- **The Echo** (1904–1943, Long Branch/Red Bank) — "Oldest colored paper in New Jersey"
- **NJ Afro-American** (1941–present, Newark) — the longest-running Black newspaper in NJ

### Civil rights era (1950–1980)
- **Black Newark** (1968–1974) — published by the Committee for Unified Newark following the 1967 uprising
- **Unity and Struggle** (1972, Newark) — connected to the Congress of Afrikan People

### Contemporary digital outlets (2010s–present)
- **Black In Jersey** (2021, Trenton) — "Our Voices, Our Perspectives"
- **NJ Urban News** (2018, Newark) — "A Voice for the Voiceless"
- **Trenton Journal** (2021) — solutions-based journalism
- **Ark Republic** (2017, Newark) — multimedia journalism

## Geographic coverage

Publications span all regions of New Jersey:
- **North Jersey:** Newark, Paterson, East Orange, Teaneck, Montclair, Jersey City
- **Central Jersey:** Trenton, Princeton, Plainfield, Somerset, New Brunswick
- **South Jersey:** Camden, Atlantic City, Swedesboro, Pleasantville

## Working with the data

The full dataset is available as JSON at:
```
https://centercoopmedia.github.io/njblackpress/data/publications.json
```

To regenerate from source:
```bash
cd data/
python3 convert_csv.py          # Regenerate publications.json from CSV
python3 merge_research.py       # Merge research findings
cp publications.json ../docs/data/publications.json
```

External archives referenced in the data:
- [Library of Congress](https://loc.gov)
- [WorldCat](https://search.worldcat.org)
- [Internet Archive](https://archive.org)

## Contributing

If you have information about NJ Black publications not in the database, or corrections to existing records, open an issue or submit a pull request.

## License

This dataset is made available for research and educational purposes. Please cite the Center for Cooperative Media when using this data.
