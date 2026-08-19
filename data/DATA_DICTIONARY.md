# Data dictionary

This documents the full schema for the NJ Black Press Database, in the same
style as the "data model" section of `CLAUDE.md`. It covers `publications.json`
(including the evidence array added for issue #33), `events.json`,
`stories.json`, the rights manifest, and the source-catalog keeper shape.

## publications.json

Location: `data/publications.json` (pipeline source of truth), copied to
`docs/data/publications.json` for the frontend. Built by `data/convert_csv.py`
from `data/publications.csv`, which also re-runs `data/add_evidence.py` to
attach the evidence array.

Top-level shape: `{ "metadata": {...}, "publications": [...] }`.

**metadata**

- `totalCount` — number of publications
- `cities` — sorted list of distinct `city` values
- `decades` — sorted list of distinct `decade` values
- `formats` — sorted list of distinct `format` values
- `activeCount` — count where `isActive` is true
- `ceasedCount` — count where `isActive` is false
- `evidenceCount` — total evidence entries across all publications (added by `add_evidence.py`)

**publication object**

- `id` — integer, matches the Notion export row ID and the `source-catalog.json` id
- `name` — publication name
- `alternateName` — alternate/former name, or null
- `city` — location, or null
- `publishers` — owner/publisher text, or null
- `yearFounded` — integer year, or null
- `yearCeased` — integer year, or null (null means still active unless the raw CSV value was `?`)
- `frequency` — publication frequency text, or null
- `format` — raw format text from the CSV, or null
- `languages` — languages published, defaults to "English"
- `primaryFocus` — content focus text, or null
- `missionStatement` — mission/editorial philosophy text, or null
- `historicalNotes` — free-text notes and impact, or null
- `archiveUrl` — archive/call number text, or null
- `websiteUrl` — website/archive link text, or null
- `targetAudience` — audience text, or null
- `keyStaff` — free-text staff names, or null
- `isActive` — computed boolean: true if the raw "Year ceased" CSV cell was empty, `?`, or unset
- `decade` — computed from `yearFounded` as `"YYYYs"`, or `"Unknown"`
- `isFeaturedHistoric` / `isFeaturedContemporary` — computed booleans against a hardcoded name list in `convert_csv.py`
- `medium` — computed: `"Print"`, `"Digital"`, or `"Print/Digital"`
- `evidence` — array of evidence objects (see below), always present, may be empty

**evidence object** (one per source-catalog keeper for that publication)

- `type` — the catalog keeper's `kind` (for example `catalog_record`, `newspapers_com_download`)
- `source` — one of `newspapers.com`, `wayback`, `ia`, `danky`, `depth-hunt`, `loc`, `other`; derived from the keeper's `localFile` path segment under `data/research/<segment>/`
- `date` — date string from the catalog keeper, may be empty
- `caption` — caption/title text from the catalog keeper
- `file` — repo-relative path to the evidence file, forward slashes
- `rightsStatus` — one of `publishable`, `publishable_with_credit`, `crop_first`, `metadata_only`, `unlisted` (see rights manifest below); `unlisted` means no rights-manifest entry was found for that file
- `citation` — citation text pulled from the rights manifest, empty string if none
- `url` — source URL from the catalog keeper, may be empty

Evidence is rebuilt deterministically from `data/research/source-catalog.json`
and `data/research/rights/rights-manifest.json` every time `add_evidence.py`
(or `convert_csv.py`, which calls it) runs. Do not hand-edit the `evidence`
field in `publications.json` — edit the catalog or rights manifest instead
and re-run the build.

## events.json

Location: `data/events.json` (pipeline source), copied to
`docs/data/events.json` for the frontend. Built by
`data/build_site_events_stories.py` from
`data/research/editorial/events.json` (the editorial source; do not edit
directly — it is milestone-2 output).

Top-level shape: `{ "events": [...], "metadata": {...} }`.

**metadata**

- `totalCount` — number of events
- `generated` — date string carried over from the editorial source
- `byDecade` — object mapping `"YYYYs"` (or `"Unknown"`) to event counts
- `byConfidence` — object mapping confidence level to event counts
- `sourceFiles` — sorted list of every distinct source file referenced across all events

**event object**

- `id` — string, `"evt-NNN"`
- `date` — date string, formats vary (`"1843"`, `"1881-05"`, full ISO dates)
- `title` — one-line event title
- `description` — full description with context and sourcing detail
- `people` — array of person names mentioned
- `publicationIds` — array of `publications.json` `id` values this event relates to; may be empty
- `sourceFiles` — array of source file names (newspaper page captures, etc.) documenting the event
- `confidence` — one of `high`, `medium` (or other levels used by the editorial team); documents how well-sourced the event is

## stories.json

Location: `data/stories.json` (pipeline source), copied to
`docs/data/stories.json` for the frontend. Built by
`data/build_site_events_stories.py` from
`data/research/editorial/stories.json` (editorial source; do not edit
directly — it is milestone-2 output).

Top-level shape: `{ "stories": [...], "metadata": {...} }`.

**metadata**

- `totalCount` — number of stories
- `byEra` — object mapping each story's `era` string to a count

**story object**

- `id` — string, `"story-NNN"`
- `title` — narrative thread title
- `thread` — full narrative text tying events together
- `people` — array of person names in the thread
- `publicationIds` — array of `publications.json` `id` values this story relates to
- `eventIds` — array of `events.json` `id` values (`"evt-NNN"`) that make up this thread
- `era` — free-text date range string, for example `"1880s-1900s"`
- `strength` — editorial rating of how well-supported the thread is (present on some entries)

## Rights manifest

Location: `data/research/rights/rights-manifest.json`. One entry per
physical evidence file (not per publication), covering Internet Archive,
newspapers.com, Danky book scans, and wayback screenshots (issues #29-#32).

Top-level shape: `{ "files": [...], "metadata": {...} }`.

**file entry**

- `path` — repo-relative path to the file, matched against evidence `file` values by `add_evidence.py`
- `source` — origin system, for example `"newspapers.com"`, `"Internet Archive"`
- `publicationIds` — array of `publications.json` ids this file supports; may be empty for corroborating-only files
- `status` — one of:
  - `publishable` — can be published as-is (for example, pre-1930 US public domain Internet Archive/newspapers.com material)
  - `publishable_with_credit` — can be published with attribution
  - `crop_first` — newspapers.com material; only a cited clip/crop may be published, never the full page
  - `metadata_only` — Danky book scans; cite the text, do not publish the image
- `citation` — citation string to display alongside published use
- `cropPlan` — description of what to crop, populated when `status` is `crop_first`
- `notes` — free-text rationale for the rights call

A `rightsStatus` of `unlisted` on an evidence entry in `publications.json`
means the file's path had no matching entry in this manifest at build time —
that is a gap to close, not a valid publish status on its own.

## Source catalog

Location: `data/research/source-catalog.json`. One entry per publication,
listing every search performed across sources and the "keeper" files worth
citing as evidence. This is the input `add_evidence.py` reads to build the
`evidence` array in `publications.json`.

Top-level shape: `{ "generated", "goal", "publicationCount", "counts", "publications": [...] }`.

**counts** — `has_keeper` (publications with at least one keeper), `searched_none` (searched, nothing found), `not_searched`, `keeper_total` (total keeper count across all publications, must equal `publications.json`'s `metadata.evidenceCount`)

**publication row**

- `id`, `name` — matches `publications.json`
- `status` — `has_keeper` or `searched_none`
- `sources` — object keyed by `newspapers_com`, `internet_archive`, `wayback`, `chronicling_america`, `other`, each with `searched` (bool), `hits` (array of candidates found, not necessarily kept), `notes`
- `keepers` — array of the search hits that were promoted to evidence; each keeper has:
  - `kind` — becomes the evidence `type`
  - `title` / `caption` — display text
  - `url` — source URL
  - `localFile` — repo-relative path to the downloaded file, or null if not yet saved locally
  - `source` — human-readable provenance note
  - `date` — date string

Every publication in `publications.json` must have a matching row here by
`id` (enforced by `data/test_source_catalog.py`), and every keeper's
`localFile` must exist on disk.
