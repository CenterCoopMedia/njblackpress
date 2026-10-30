---
type: "schema"
title: "Data model"
description: "Field guide for the publication records used by the wiki."
tags:
  - "nj-black-press"
  - "schema"
  - "data"
timestamp: "2026-10-30"
---

# Data model

Publication pages are generated from `docs/data/publications.json`. Source values are preserved as written; empty values render as `Unknown` in tables.

## Fields

| Field | Origin | Description |
|---|---|---|
| `id` | source | Unique integer identifier for the record. |
| `name` | source | Publication name. |
| `alternateName` | source | Other names the publication used. |
| `city` | source | Primary city of operation. |
| `publishers` | source | Publishing entity or individuals. |
| `yearFounded` | source | Year the publication started. |
| `yearCeased` | source | Year it stopped (blank if still active or unknown). |
| `frequency` | source | Cadence such as weekly, monthly, or daily. |
| `format` | source | Self-described format string (newspaper, periodical, magazine, etc.). |
| `languages` | source | Primary language(s); defaults to English. |
| `archiveUrl` | source | Link to a holding archive (Library of Congress, WorldCat, Internet Archive). |
| `websiteUrl` | source | Current website, for active outlets. |
| `targetAudience` | source | Intended readership. |
| `primaryFocus` | source | Subject matter the publication covers. |
| `medium` | computed | Print, Digital, or Print/Digital. |
| `missionStatement` | source | Editorial philosophy or stated mission. |
| `keyStaff` | source | Notable editors, publishers, or contributors. |
| `historicalNotes` | source | Context, significance, and research findings. |
| `isActive` | source | True for active titles, false for historical titles, null when activity is unverified or the record is a collection. Independent of yearCeased. |
| `decade` | computed | Decade of founding, derived from yearFounded. |
| `isFeaturedHistoric` | source | Highlighted as a featured historic publication on the site. |
| `isFeaturedContemporary` | source | Highlighted as a featured contemporary publication on the site. |

_Origin `source` comes straight from the dataset; `computed` is derived during the data pipeline._
