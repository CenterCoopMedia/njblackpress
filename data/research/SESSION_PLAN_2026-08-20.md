# Session plan — commit and milestones 2–3 (2026-08-19, second session)

Director: Claude (this session). Subagents do all hands-on work. The director assigns, verifies against disk, rules, and keeps this plan current.

## Session goal

Carry the archive from "captures done, uncommitted" toward launch. In order: commit the prior session's work safely (no secrets, no rights-restricted binaries in git), then milestone 2 (editorial deep-read → events.json, stories.json, editorial memo, issues #25–28), then milestone 3 (rights triage manifest, issues #29–32). Further milestones as time allows. Post a plain-English update on discussion #47 after each completed milestone.

## Task list

| ID | Task | Owner | Status |
| --- | --- | --- | --- |
| s0 | Verify prior session state on disk | director | done — counts match handoff, test_source_catalog.py PASS (138 rows, 182 keepers) |
| s1 | Director ruling: git scope for binaries | director | decided — .chrome-cdp/ never committed (login cookies); all image/PDF media under data/research/ stays out of git via .gitignore; JSON logs, catalogs, scripts, and docs are committed. Local disk remains the archival store. Joe can override |
| s2 | Commit session work: .gitignore, secret scan on logs, stage, commit | agent: commit | done — commits 060c93d + 76cc330, 240 files, media/profile ignored and verified untracked; one secret caught (Cloudflare challenge token in depth-hunt/apex_titles.json, excluded from git). Not pushed |
| s3 | Fetch issue specs #25–36 from GitHub | agent: issues | done — data/research/issue-specs.md; milestone-1 update already on #47 |
| s4 | Milestone 2: deep-read workflow (sonnet readers → opus synthesis) → events.json, stories.json, editorial memo | workflow: deep-read | first pass done — 42 readings, 70 events, 13 stories, memo written. Adversarial verify FAILED with 13 defects (issue dates as event dates, pre-dated citations, name contradictions, 1 weak story, 2 broken reading JSONs) + 1 unread artifact (Nubian News PDF over read limit). Round 1 corrections fixed all 13; Nubian PDF salvaged (text layer, full read) and integrated (+9 events, now 79). Re-verify round 2: 11/13 fixes hold, 4 new defects (evt-021 announced-vs-held, evt-074 photographer attribution, story-009 untraceable claims, memo count) + mojibake note. Round 2 fixed 4 defects +2 traceability events (evt-080/081, now 81 events); round 3 fixed 6 framing/disclosure items; final scoped verify PASS with 0 defects. Done — 81 events, 13 stories, memo, 42 readings, 3 adversarial passes. Known nits deferred to fact-check milestone: "Newark weeklies" plural outside thread 10, memo line 99 evidence-count wording, ids 9/24 duplication question |
| s5 | Milestone 3: rights triage manifest per file | agent: rights | done — data/research/rights/rights-manifest.json, 325 files: 34 publishable, 5 publishable_with_credit, 50 crop_first, 236 metadata_only. check_manifest.py PASS, director re-ran it and spot-checked the 1930 boundary and Danky citations |
| s6 | Discussion #47 updates after each milestone | agent | milestone 3 posted (discussioncomment-18082534), issues #29–32 closed; milestone 2 posted (discussioncomment-18082891), issues #25–28 closed. Editorial+rights+evidence committed as ea6ac11 (52 files, verified clean, not pushed) |
| s7 | Milestone 4: evidence arrays (#33) | agent: evidence | done — 182 evidence entries across 137 pubs (id 14 honest empty), data/add_evidence.py + data/test_evidence.py PASS, docs copy byte-identical. Gap found and fixed: 2 LOC catalog screenshots added to rights manifest as publishable_with_credit (director ruling, Joe can override); manifest now 327 files, 0 unlisted, all checks re-run PASS by director |
| s8 | Milestone 4: events/stories into site data + pipeline + data dictionary (#34–36) | — | pending, blocked on s4 |

## Rules in force

- All prior standing rulings hold (Right On! exclusion, NJ-only keepers, nothing to docs/ until cropped, cited, cleared).
- .chrome-cdp/ and archival media never enter git history. Treat any commit as permanent.
- Every agent report checked against disk before it is believed.
- Sentence case everywhere. Plain-English #47 updates after each milestone.

## Verified state

- Start: working tree has ~80 untracked scripts, session docs, modified data JSONs; nothing committed since ce7deed.
- data/research/ media on disk: newspapers-com/downloads 61 files (83M), wayback/clean 18 (68M), ia/clean 10 PDFs + log (401M), danky 233 (280M), depth-hunt 47M.

## Operational notes

- Update this table as tasks complete; record counts, methods, and paths in the status cell.
