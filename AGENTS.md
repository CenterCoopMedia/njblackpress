# Repository guidelines

`CLAUDE.md` is the authoritative project brief. Keep this file aligned with it
when project behavior changes.

## Project context

This repository contains the NJ Black Press Archive static site and its data
pipeline. GitHub Pages serves `docs/` from `master`.

The project has no backend, database server, authentication, or write API.

## Important paths

- `docs/`: Published site and browser data.
- `docs/js/woven/`: Woven ES modules.
- `data/`: Pipeline data, research inputs, builders, and checks.
- `data/research/source-catalog.json`: Evidence provenance.
- `data/research/rights/rights-manifest.json`: Evidence rights decisions.
- `scripts/`: Public and portable wiki generators.
- `okf/`: Generated portable wiki.
- `src/input.css`: Tailwind source.

## Generated files

Do not hand-edit these outputs:

- `docs/css/tailwind.css`
- Browser data under `docs/data/`
- `data/map-publications.json`
- `docs/wiki/`
- `okf/`

Update the source and run its builder. Review generated diffs before commit.

## Common commands

```bash
npm ci
npm run build:css
cd docs && python3 -m http.server 8000
```

Common focused checks:

```bash
python3 data/test_site_data.py
python3 data/test_source_catalog.py
python3 data/test_map.py
python3 data/test_navigation.py
python3 data/test_wiki_publications.py
python3 data/test_woven_layout.py
python3 data/test_woven_usability.py
python3 scripts/generate_okf_wiki.py --check
```

The evidence and source-catalog checks require the local evidence corpus. Most
large research files are ignored by Git and are not present in a normal clone.

## Data and evidence rules

- Read `data/DATA_DICTIONARY.md` before changing a data contract.
- Keep pipeline data and browser data copies equal.
- Treat `data/publications.json` as the current publication record.
- Do not run `data/convert_csv.py` for a routine correction.
- Copy and compare featured data after you change its source file.
- Do not hand-edit publication evidence arrays.
- Do not publish evidence without a permitted rights status.
- Rebuild the clipping index after a rights change.
- Remove an old public evidence image after its rights status is downgraded.
- Preserve publication IDs and verify all cross-file references.
- Regenerate the map and both wikis after applicable publication changes.

## Interface rules

- Use sentence case for headings and interface text.
- Preserve keyboard access, focus behavior, reduced motion, and semantic HTML.
- Use complete Tailwind class strings in JavaScript.
- Rebuild Tailwind after a class change.
- Check visible changes at desktop and mobile sizes.

## Pull requests

Keep each pull request focused. Explain the source and rights basis for data or
evidence changes. Include screenshots for visible changes and name every check
you ran.

Do not merge without Joe's approval. After a merged achievement, add the
required plain-language update to the Road to launch discussion.
