# Session task list

Updated: 2026-08-19 05:26 ET — idle reconfirm. Tests PASS twice. Chrome idle on newspapers.com. Durable Grok loop: `01a01166b94b` every 30 minutes. Do not close Chrome.

Session goal: catalog archival records for every publication id. Done when each of the 138 rows has a catalog row, hit or none notes, and every keeper has a local preview + share URL.

| ID | Task | Status |
| --- | --- | --- |
| q1–q7k | Prior catalog passes | done |
| q6 | Persist Newspapers.com Entire Page JPG/PDF | done |
| q7 | Oldest-first keepers | done |
| q7l | New Jersey Record 14 | done (honest none) |
| q8 | Keep this file current after each pass | done this pass |
| q9 | Fill missing keeper caption/date on 10 existing keepers | done |
| t7 | Wire clean full-resolution files into keeper `localFile` fields; add depth-hunt finds | done 2026-08-19 |

## t7 (2026-08-19): clean-file wiring

`data/wire_clean_files.py` repointed 68 keeper `localFile` fields at the clean
captures: 20 newspapers.com Entire Page JPGs (matched by image id), 18 Wayback
retina PNGs, 30 Internet Archive issue PDFs (10 issues shared across pubs 9, 16,
24). The 106 Danky scan keepers and 2 LOC catalog screenshots were left alone.
0 unmatched.

Added 6 new keepers from `depth-hunt/findings.json`: 40 The Nubian News
(full_issue PDF), 68 MEDIC News (full_issue PDF), 112 Captain Africa
(cover_image), 114 Word Up! (auction_photo), 121 Testimony (cover_image), 135
Rap Masters (cover_image). Keepers 176 → 182.

Right On! (95) is excluded by director ruling — the 1971/1977 PDFs are
Hollywood-era issues that predate the 1983 move to Cresskill NJ. A note records
this on the row; Joe can override.

Dry-run report: `data/research/wiring-dryrun.json`. Backup before apply:
`data/research/source-catalog.backup-2026-08-19.json`.

Six clean newspapers.com exports are supporting out-of-state pages (Evening
World, Washington Bee, NY Tribune, NY Age ×2, Afro-American) that were never
keepers, so they were not wired in.

## Counts now

Catalog: 138 rows. has_keeper 137, searched_none 1, not_searched 0. Keepers: 182 (`counts.keeper_total`). `test_source_catalog.py` PASS. All five source keys searched on every row. Every keeper has a local file, share URL, caption, date, and source. Keeper metadata gaps: 0.

## Status

The catalog goal is met. New Jersey Record 14 is the only searched_none. That is an honest none: no Danky entry, no LOC/library collection, Newspapers.com hits are generic "New Jersey record" phrasing.

This pass (2026-08-19 05:26 ET): no peer mid-search (only `a40-owokweav` in system32). Headed Chrome + `browser_daemon.py` (pid 3988, started 2026-08-18 19:41 ET via `.chrome-cdp`) pinged OK on https://www.newspapers.com/ title "The past: read all about it." No new search. Keeper metadata still 0 gaps (176 keepers). Fake bulk notes: 0. Known keepers not reopened. Proof rewritten to grok-goal implementer folder. Tests PASS twice.

q6 is done (2026-08-19). All 26 verified keeper pages now have a full-resolution
Entire Page JPG and PDF in `data/research/newspapers-com/downloads/`.

What fixed it: Playwright's `expect_download` and `Page.setDownloadBehavior`
never see these files. The working method is the browser-level CDP session
(`browser.new_browser_cdp_session()`) with
`Browser.setDownloadBehavior {behavior: "allowAndName", eventsEnabled: true}`,
then reading the real path from the `Browser.downloadProgress` event whose
`state` is `completed`. `allowAndName` writes GUID-named files, so the CDP
event is the only way to learn the path; the script renames them to the keeper
slug. The JPG pill is a plain anchor with an `a=download` href and works on the
first click. The PDF pill has no href, is JS-driven, and is flaky — it needs a
trusted Playwright click and up to three attempts.

Scripts: `data/clean_np_download.py` (main loop), `data/clean_np_pdf_retry.py`
(PDF retry), `data/clean_np_extra.py` (late-added keepers),
`data/clean_launch.py` (relaunch Chrome on the `.chrome-cdp` profile).
Log: `data/research/newspapers-com/downloads/clean-download-log.json`.

Still do not put uncropped full scans on docs/. (Keeper `localFile` fields now
point at these clean files — see t7 above.)

## Next action (optional)

A later pass can crop cleared keeper previews for the public site. Do not reopen the known keepers. Chrome stays open. Newspapers.com clips stay New Jersey-only.
