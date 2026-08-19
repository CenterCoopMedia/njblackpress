# Session goal

Find, save, and catalog archival records for every publication in the NJ Black Press Archive (~140 titles). For each title, collect whatever exists: newspaper clippings, full issues, mastheads, Wayback snapshots, website screenshots, catalog records, and other primary materials. Sources include Newspapers.com (New Jersey papers only for clippings), the Internet Archive / Wayback Machine, Chronicling America, library digital collections, and other public archives.

Work oldest ceased titles first. Prefer materials printed in or published from New Jersey. Save a local preview file plus a shareable source URL for every keeper. Do not mark a title done until it has been searched in the source list and the result (hit or none) is written into the catalog.

## Done when

Every publication id in `data/publications.json` has a row in `data/research/source-catalog.json` that records which sources were searched, what was found, file paths, and URLs. Keeper clips live under `data/research/` with a caption, date, source paper or site, and an embed/share URL. New facts (founding, move, fire, fold, staff) are written back into the publication notes. The Chrome session stays open. Newspapers.com clips stay New Jersey-only. Full page scans do not go on the public site until they are cropped, cited, and cleared for sharing.

## Search order

1. Pre-1950 newspapers with no digitized issue in our files.
2. Titles that folded, especially 1930s–1940s and 1991 Afro-American.
3. Contemporary sites on the Wayback Machine (earliest and latest snapshot).
4. Remaining magazines, newsletters, and camp papers.

## Sources to check per title

Newspapers.com (location = New Jersey). Internet Archive item search and collection `newarkafamnewspapers` (124+ New Jersey Herald News issues, 1938–1945, public domain per Newark Public Library). Wayback Machine CDX for any `websiteUrl`. Chronicling America / LOC. Newark Public Library, Rutgers Newark Black Newspapers, Red Bank Public Library, NJ State Library (Ironsides Echo). WorldCat only as a pointer, not as the clip.

## Already in hand (do not redo)

Newspapers.com NJ keepers for The Echo (1904 fire; 1909 move to Red Bank), Herbert/Sentinel (1893 Bradley letter; 1895 GOP committee), Trumpet/Murrell (Asbury Park 1893), Daily Record 2023 on the NJ Afro-American. Wayback CDX index for 18 current sites. IA Herald News run starting 21 May 1938.

## Output

`data/research/source-catalog.json` (one record per publication). Clip files and `catalog.json` under `data/research/newspapers-com/clips/` and `data/research/wayback/`. Notes in `data/research/SESSION_GOAL.md` and the existing NOTES files.
