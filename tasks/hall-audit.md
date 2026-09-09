# History hall: data audit

Date: September 9, 2026. Work package 1, issue 74.

Everything below was counted from the files the page actually loads:
`docs/data/publications.json`, `docs/data/stories.json`, `docs/data/events.json`,
and `docs/data/clippings.json`. Nothing here is an estimate, and nothing here
changes a record. Where the data does not support a distinction the hall wants,
that is written down as an open question rather than filled in.

## Publications by section

The archive holds 136 publications. The hall keeps one labelled section per
decade from the 1880s to the 2020s, plus one section for titles whose founding
date is unrecorded. Two decades hold no titles at all and keep a marker and a
navigation destination. The section length column is what `docs/js/hall/layout.js`
produces from the current data; it is the room the sheets and reading tables
need, not a measure of time.

| Section | Titles | With a cleared clipping | Still publishing | Volumes | Length |
|---|---|---|---|---|---|
| 1880s | 3 | 3 | 0 | 4 | 15.7 |
| 1890s | 0 | 0 | 0 | 0 | 6.0 |
| 1900s | 2 | 1 | 0 | 1 | 8.7 |
| 1910s | 2 | 1 | 0 | 0 | 6.0 |
| 1920s | 2 | 1 | 0 | 0 | 6.0 |
| 1930s | 13 | 4 | 0 | 6 | 30.25 |
| 1940s | 3 | 2 | 0 | 0 | 6.6 |
| 1950s | 9 | 2 | 0 | 0 | 12.6 |
| 1960s | 10 | 2 | 0 | 0 | 13.6 |
| 1970s | 29 | 4 | 1 | 1 | 35.7 |
| 1980s | 21 | 2 | 1 | 1 | 27.7 |
| 1990s | 25 | 2 | 1 | 0 | 28.6 |
| 2000s | 0 | 0 | 0 | 0 | 6.0 |
| 2010s | 8 | 8 | 6 | 0 | 11.6 |
| 2020s | 6 | 6 | 6 | 0 | 9.6 |
| Date unrecorded | 3 | 1 | 2 | 0 | 6.6 |
| Total | 136 | 39 | 17 | 13 | 231.25 |

Three facts follow from this table and should shape the design.

The collection is bottom heavy. The 1970s, 1980s, and 1990s hold 75 of the 136
titles, and the 1930s hold 13. A design that looks right for three sheets in the
1880s has to survive twenty-nine in the 1970s.

Cleared display material is not spread evenly. Only 39 titles have any record the
rights manifest allows us to show, and 14 of those are the recent websites in the
2010s and 2020s. Most of the historic wall is publication-record design, not
photographs of newsprint.

The whole hall is about 231 units long end to end. Walking that distance is not
the way to reach the 1990s. The decade navigator, the publication index, and
search have to be the primary way to move, with travel reserved for the short
distances around where the visitor already is.

## Same-year clusters

Founding years repeat often: 106 of the 133 dated titles share their founding
year with at least one other title, and only 27 titles have a year to themselves.
Every title in a cluster still gets its own slot, and every one of them shows the
same date. Largest clusters first.

| Founding year | Titles |
|---|---|
| 1972 | 7 |
| 1938, 1970, 1989 | 5 each |
| 1968, 1971, 1983, 1988, 1990, 1991, 1993, 1994, 2021 | 4 each |
| 1936, 1950, 1974, 1978, 1979, 1982, 1992, 1996 | 3 each |
| 1934, 1935, 1951, 1952, 1966, 1973, 1985, 1987, 1995, 2016, 2017, 2022 | 2 each |

The 1972 cluster is the layout fixture: seven titles, seven slots, one shared
date. It sits inside the 1970s, the densest section, so it also exercises the
section-length rule.

## Date cases in the data

`yearFounded` and `yearCeased` are whole years or null. There is no field for an
approximate year, a date interval, or a season, and no record uses one. The only
qualified date wording in the archive is inside a quoted source caption, for
example a bibliography entry reading "1990?-1993" for Hype. That qualification
belongs to the quotation and is shown as part of it; it is not a date value the
hall can read.

| Case | Wording the hall shows | Records | Notes |
|---|---|---|---|
| Known range | 1934–1966 | 110 | Founding and cessation years both recorded |
| Single year | 1940 | 8 | Founded and ceased in the same year |
| Still publishing | 1990–present | 15 | Dated and flagged active |
| Date unrecorded, still publishing | Date unrecorded, still publishing | 2 | New Jersey Record, New Jersey Deadline |
| Date unrecorded, ceased | Date unrecorded, ceased 1979 | 1 | Newark Black Newspapers Collection |
| End unrecorded | 1955, end unrecorded | 0 | No record is in this state today; kept as a test fixture |
| Date unrecorded | Date unrecorded | 0 | No record is in this state today; kept as a test fixture |

Eight titles opened and closed inside one year. Printing those as "1940–1940"
reads as a range that is not one, so the shared formatter prints the single year.

Two points matter here. First, "unrecorded" and "still publishing" are different
answers to different questions, and the three undated records prove it: two are
active and one has a recorded ending but no beginning. Dropping the recorded
ending to fit the four-case list in the specification would lose source data, so
the formatter keeps it and says the founding date is unrecorded. Second, active
status comes from the dataset's own `isActive` flag, the same flag the archive
and the wiki count, so the hall never derives a second answer from the years.

All 133 dated titles fall between 1880 and 2022, inside the chronology the flat
timeline uses. No record needs clamping today. The layout still reports an
out-of-range year as a placement decision rather than hiding the record.

## Stories and their sections

There are 13 guided stories and 59 stops. A story's section comes from the first
decade named in its approved era wording, moved forward to the 1880s when the
story starts earlier than the hall does. That rule reproduces the migration
fixture in the specification exactly.

| Story | Era wording | Section | Stops | Stops with a clipping | Note |
|---|---|---|---|---|---|
| story-001 | 1860s-1900s | 1880s | 9 | 3 | Begins before 1880 |
| story-002 | 1880s-1900s | 1880s | 8 | 1 | |
| story-003 | 1880s-1890s | 1880s | 5 | 2 | |
| story-010 | 1870s-1970s | 1880s | 4 | 0 | Begins before 1880 |
| story-004 | 1900s-1920s | 1900s | 3 | 2 | |
| story-005 | 1930s-1940s | 1930s | 5 | 4 | |
| story-006 | 1930s-1940s | 1930s | 9 | 9 | |
| story-007 | 1930s-1940s | 1930s | 4 | 1 | |
| story-008 | 1930s-1940s | 1930s | 4 | 4 | |
| story-009 | 1930s-1940s | 1930s | 4 | 4 | |
| story-012 | 1930s-1990s | 1930s | 1 | 0 | |
| story-011 | 1970s-1990s | 1970s | 2 | 2 | |
| story-013 | 1980s-1990s | 1980s | 1 | 1 | |

Four stories land in the 1880s and six in the 1930s, so those sections need more
than one reading table. The layout puts two volumes on a table and gives each
section as many tables as it needs: two at the entrance, three in the 1930s, one
each in the 1900s, 1970s, and 1980s. No story lands in an empty decade.

Stops carry stable event ids, so `?stop=evt-NNN` needs no data change. Stop dates
are recorded to the day in 36 cases, to the month in 14, and to the year in 9,
and 6 of the 59 stops are marked medium confidence. Three events in the archive
predate 1880; the earliest is 1843.

## Clippings and rights

`docs/data/clippings.json` holds 55 public clippings, all JPEG, all already
cropped by `data/make_clippings.py` from crop boxes decided by hand. Every file
it names exists under `docs/`, and no two of them share a file name.

| Rights status | Clippings | What it requires |
|---|---|---|
| crop_first | 32 | A cropped public derivative, which these already are |
| publishable | 16 | Citation with the image |
| publishable_with_credit | 7 | The exact required credit with the image |

Statuses that forbid publication, `metadata_only` and `unlisted`, do not appear
in the public clipping index at all; they stop at the rights manifest. The wall
copies therefore start from an already cleared, already cropped set, and the hall
makes no rights judgement of its own. Of the 59 story stops, 33 have a clipping;
the other 26 need the text-only treatment.

`data/make_wall_copies.py` turns those 55 files into 55 wall copies, 2.4 MB in
total, at most 400 pixels wide and 1200 pixels on the long edge.

## How the site counts records today

`docs/js/publication.js` counts every entry in a publication's `evidence` array
and prints "1 source record supports this entry" or "N source records support
this entry". It does not filter by rights status. It then splits the same array
into records it may show as pictures, decided by asking whether
`docs/data/clippings.json` publishes that source file for that publication, and
records it may only cite. The record panel in the historical notes page lists the
same array. The hall follows this policy exactly: `recordCount` is the length of
the evidence array, `recordsLabel` says "1 record" or "3 records", and
`clearedRecordCount` reports separately how many of those may be shown.

The archive holds 171 evidence records: 106 metadata only, 32 crop first, 26
publishable, and 7 publishable with credit. One publication has none; the largest
has ten. A record count says how much research is attached to an entry. It is not
a measure of a publication's importance, and no part of the hall may present it
as one.

## Open questions for later packages

The hall is 231 units long, so travel cannot be the primary way to reach a
decade. Package 2 should confirm that the decade navigator and the index make
every section reachable in one action, and that long jumps go straight to the
target rather than travelling through the sections in between.

Only 39 of 136 titles have anything cleared to show. The publication-record
design for the other 97 is the majority of the wall, not an edge case, and needs
Joe's review as a first-class treatment.

Twenty-six of the 59 story stops have no clipping. The text-only spread is
likewise the normal case, not an exception.
