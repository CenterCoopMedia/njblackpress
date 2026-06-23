# wiki build plan

- [x] Verify open knowledge format basics from Google Cloud's announcement and public repo references.
- [x] Inspect the archive dataset and publication schema.
- [x] Add a generator that writes an open knowledge format wiki from `data/publications.json`.
- [x] Generate wiki pages for the repo, archive, publication records, cities, decades, formats, and data model.
- [x] Document how to regenerate the wiki.
- [x] Run validation and review the generated output.

## Review notes

Validated that all 244 markdown pages include YAML frontmatter with a `type` field, regenerated the wiki from source data, ran `git diff --check`, and attempted external review with `claude -p`; the command is not installed in this environment. Follow-up review fixed slug collisions, safer YAML quoting, markdown table escaping, and deterministic timestamps.
