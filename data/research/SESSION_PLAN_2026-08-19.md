# Session plan — clean archival captures (2026-08-19)

Director: Claude (this session). All hands-on work is done by Opus subagents. The director assigns tasks, verifies reports against files on disk, and keeps this plan current.

## Session goal

Replace every sloppy capture from the prior Grok session with a clean, full-resolution archival file, for all 138 publications in the NJ Black Press archive. "Clean" means: newspapers.com pages saved through the site's own Entire Page export (JPG + PDF, multi-thousand-pixel scans); Wayback/website keepers as full-page retina PNGs with no browser chrome, toolbars, or banners; Internet Archive issues as direct full PDFs, not thumbnails. Done when the coverage audit shows every publication has at least one clean keeper file on disk, or a documented honest gap.

## Task list

| ID | Task | Owner | Status |
| --- | --- | --- | --- |
| t1 | Unblock q6: persist newspapers.com Entire Page JPG+PDF for all verified keepers, oldest first | agent: np-downloads | done — 26/26 keepers, JPG+PDF each, verified on disk. Method: browser-level CDP Browser.setDownloadBehavior allowAndName + Browser.downloadProgress event |
| t2 | Clean full-page Wayback captures for all wayback/website keepers | agent: wayback | done — 18/18, log verified |
| t3 | Direct IA issue PDFs (Newark Herald, NJ Herald News 1938–1942) | agent: wayback | done — 10/10, 401 MB, valid PDFs |
| t4 | Verify Danky 1998 scans are full resolution | agent: wayback | done — 213 jpgs at 3126x4328, no refetch |
| t5 | Coverage audit: map all 138 pubs to clean files, produce gap list | agent: audit | done — 136 clean, 1 partial, 1 none (see clean-coverage.json) |
| t6 | Fill gaps: two Trenton Times re-exports (Utimme Umana, image ids 1192937414 + 1197515771) queued to np-downloads; New Jersey Record (id 14) stays an honest none pending new research | agent: np-downloads | done — both pages exported JPG+PDF, verified |
| t6b | Archival-depth workflow for the 103 danky-only pubs: sonnet hunters (CA, IA, library collections) → opus adversarial verify → findings.json. Output: data/research/depth-hunt/ | workflow: danky-depth-hunt | done — 6 confirmed finds, 93 honest nones, 1 rejected (Right On! CA-era issues; Joe to decide on contextual use) |
| t9a | Right On! 1971/1977 CA-era PDFs | director | decided — excluded by director ruling (Hollywood-era mastheads predate the 1983 Cresskill NJ move); note recorded on pub 95 sources.other.notes; Joe can override |
| t7 | Wire clean files into source-catalog.json keeper localFile fields | agent: wiring | done — 68 repoints (20 newspapers.com, 18 wayback, 30 IA), 6 new depth-hunt keepers, 1 note. Keepers 176 → 182. Backup: source-catalog.backup-2026-08-19.json. Test PASS |
| t8 | Optional: cropped clip previews from full-page JPGs (local PIL only, never the site's portion selector) | deferred | deferred |
| t9 | Update TASK_LIST.md (mark q6) and session notes | director | done — TASK_LIST updated by agents, director verified catalog on disk (182 keepers, 74 clean-pointing, 0 missing, test PASS) |
| t10 | Director ruling: 6 out-of-state newspapers.com exports (Evening World, Washington Bee, NY Tribune, NY Age x2, Baltimore Afro-American) stay out of keepers per the NJ-only policy in NOTES.md; files remain in downloads/ as supporting evidence. Joe can override | director | decided |

## Rules in force

- Entire Page export only on newspapers.com; never the click-and-drag portion selector.
- NJ-only clip policy per NOTES.md stands. Nothing goes to docs/ until cropped, cited, and cleared.
- The logged-in Chrome (.chrome-cdp profile, CDP port 9222) stays open; only the np-downloads agent touches it.
- source-catalog.json was read-only until t7; t7 is applied (backup kept alongside).
- Agents run lean: one small script, prove on a test case, loop mechanically, two-strike rule on failures.
- Every agent report is checked against files on disk before it is believed.

## Verified state so far

- data/research/newspapers-com/downloads/ — clean full-page exports, paper_date_page_story naming, 1888–2023.
- data/research/wayback/clean/ — 18 retina full-page PNGs + clean-capture-log.json.
- data/research/ia/clean/ — 10 full issue PDFs + log.
- data/research/danky/ — 213 full-res scans, confirmed good, untouched.
- Known agent bugs caught and fixed: IA "temporarily offline" page passing the blank test; sticky-element CSS strip collapsing page height (6 captures silently truncated, re-shot).

## Operational notes

- Playwright + web.archive.org time out under the sandboxed Bash tool; capture runs need the sandbox disabled.
- Chrome download history shows "Removed" for exports because the agent renames files into the repo; bytes are safe.
- One stray duplicate in C:\Users\Joe Amditis\Downloads (Monmouth_Democrat_1904_09_08_4.pdf) is safe to delete.
