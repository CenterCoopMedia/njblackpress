# Session plan — commit and milestones 2–3 (2026-08-19, second session)

Director: Claude (this session). Subagents do all hands-on work. The director assigns, verifies against disk, rules, and keeps this plan current.

## Session goal

Carry the archive from "captures done, uncommitted" toward launch. In order: commit the prior session's work safely (no secrets, no rights-restricted binaries in git), then milestone 2 (editorial deep-read → events.json, stories.json, editorial memo, issues #25–28), then milestone 3 (rights triage manifest, issues #29–32). Further milestones as time allows. Post a plain-English update on discussion #47 after each completed milestone.

## Task list

| ID | Task | Owner | Status |
| --- | --- | --- | --- |
| s0 | Verify prior session state on disk | director | done — counts match handoff, test_source_catalog.py PASS (138 rows, 182 keepers) |
| s1 | Director ruling: git scope for binaries | director | decided — .chrome-cdp/ never committed (login cookies); all image/PDF media under data/research/ stays out of git via .gitignore; JSON logs, catalogs, scripts, and docs are committed. Local disk remains the archival store. Joe can override |
| s2 | Commit session work: .gitignore, secret scan on logs, stage, commit | agent: commit | pending |
| s3 | Fetch issue specs #25–36 from GitHub | agent: issues | pending |
| s4 | Milestone 2: deep-read workflow (sonnet readers → opus synthesis) → events.json, stories.json, editorial memo | workflow: deep-read | pending |
| s5 | Milestone 3: rights triage manifest per file | agent: rights | pending |
| s6 | Discussion #47 updates after each milestone | agent | pending |
| s7 | Milestone 4 and beyond as time allows | — | pending |

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
