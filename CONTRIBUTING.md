# Contributing

Thank you for helping improve the NJ Black Press Archive.

## Report a correction

Use the repository's data correction issue form for a missing or incorrect
publication fact. Include:

- The publication name and record URL.
- The exact field that needs a change.
- The proposed value.
- A reliable source link or full citation.
- Any rights or access limits on supporting files.

Do not upload copyrighted newspaper pages unless you have permission to share
them.

## Development setup

Install Node.js, npm, and Python 3. Then run:

```bash
npm ci
npm run build:css
cd docs
python3 -m http.server 8000
```

Open `http://localhost:8000/`.

## Choose the correct source

| Change | Source |
|---|---|
| Shared page content | HTML under `docs/` |
| Shared navigation | `docs/js/site-nav.js` |
| Publication fields | `data/publications.csv` or the applicable research source |
| Publication evidence | `data/research/source-catalog.json` |
| Evidence rights | `data/research/rights/rights-manifest.json` |
| Events and stories | `data/research/editorial/` |
| Map locations | `data/municipality-centers.json` |
| Tailwind styles | `src/input.css`, HTML classes, or JavaScript class strings |
| Public wiki | `scripts/generate_html_wiki.py` and its source data |
| Portable wiki | `scripts/generate_okf_wiki.py` and its source data |

Read [data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md) before you change data
shapes. Do not hand-edit generated files.

## Build generated outputs

Run only the builders needed for the change:

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
```

Commit the source and its generated outputs together.

## Validate the change

Use the smallest checks that cover the changed area:

| Area | Checks |
|---|---|
| Shared styles | `npm run build:css` and browser checks |
| Publications and evidence | `python3 data/test_evidence.py` and `python3 data/test_source_catalog.py`, with the local evidence corpus |
| Events and stories | `python3 data/test_site_data.py` |
| Map | `python3 data/test_map.py` |
| Navigation | `python3 data/test_navigation.py` |
| Public wiki | `python3 data/test_wiki_publications.py` |
| Portable wiki | `python3 scripts/generate_okf_wiki.py --check` |
| Woven | `python3 data/test_woven_layout.py` and `python3 data/test_woven_usability.py` |

Check visible changes in a browser at desktop and mobile sizes. Check keyboard
navigation when the change affects controls, dialogs, or focus.

Git ignores most large research files. Evidence checks need the separate local
evidence corpus and will fail in a normal clone without it.

## Pull request process

1. Branch from the latest `master` branch.
2. Make one focused change.
3. Update source and generated files together.
4. Run the applicable checks.
5. Complete the pull request template.
6. Address review comments and resolve their conversations.
7. Wait for approval before merge.

GitHub Pages publishes changes under `docs/` after merge. Verify the live route
after publication.
