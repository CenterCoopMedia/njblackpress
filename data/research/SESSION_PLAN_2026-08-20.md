# Session plan — commit and milestones 2–5 (2026-08-19, second session)

Director: Claude (this session). Subagents do all hands-on work. The director assigns, verifies against disk, rules, and keeps this plan current.

## Session goal

Carry the archive from "captures done, uncommitted" toward launch: safe commit, milestone 2 (editorial deep-read), milestone 3 (rights triage), milestone 4 (site data), milestone 5 (redesign incl. Joe's "wood and fabric" + "Woven" directives), milestone 6 as time allows. Plain-English #47 update after each milestone.

## Incident log (2026-08-19)

- A hotfix agent ran `git reset --hard` while the working tree held uncommitted redesign work. Wiped: the #39 timeline upgrade (docs/js/timeline.js, index.html, styles.css), the #48 styling pass (all three pages + styles.css + favicon), and this plan's latest edits. Untracked files (design docs, research artifacts) survived. Plan restored from director context; code must be redone.
- Discovered origin/master moved 18 commits ahead (tip d1367cb), pushed by a separate workstream — includes the same publication.js fix (ba25d47), a merged PR #16, and "Add the Tailwind build and first compiled stylesheet (#24)", which may conflict with the zero-build architecture. Local master (7f1bfad) has 4 local-only commits; rebase attempt hit real conflicts (.gitignore, data/publications.json, docs/data/publications.json) and was aborted cleanly.
- New rule in force: no agent may run `git reset --hard`, `git checkout --`, `git clean`, or any destructive git command. Recovery/reconciliation commands are director-approved only, and only after `git stash` or a WIP commit protects the working tree.

## Task list

| ID | Task | Owner | Status |
| --- | --- | --- | --- |
| s0 | Verify prior session state on disk | director | done — counts match handoff, test_source_catalog.py PASS (138 rows, 182 keepers) |
| s1 | Director ruling: git scope for binaries | director | decided — .chrome-cdp/ never committed; media stays out of git via .gitignore; JSON/md/py committed. Joe can override |
| s2 | Commit session work | agent: commit | done — 060c93d + 76cc330, 240 files, verified clean; Cloudflare token file excluded. Not pushed |
| s3 | Fetch issue specs #25–36 | agent: issues | done — data/research/issue-specs.md (later #37–44 appended) |
| s4 | Milestone 2: deep-read → events/stories/memo | workflow + 3 fix rounds | done — 42 readings, 81 events, 13 stories, memo; 3 adversarial passes, final scoped verify PASS 0 defects. Nits deferred to fact-check: "Newark weeklies" plural outside thread 10, memo line 99 wording, ids 9/24 duplication |
| s5 | Milestone 3: rights manifest | agent: rights | done — rights-manifest.json 327 files (34 publishable, 7 with credit incl. 2 LOC, 50 crop_first, 236 metadata_only), check PASS, director spot-checked 1930 boundary |
| s6 | GitHub closeouts + #47 updates | agents | done — milestones 2, 3, 4 posted (…18082534, …18082891, …18082918); issues #25–36 closed; #37/#39/#41 closed later |
| s7 | Milestone 4: evidence arrays (#33) | agent: evidence | done — 182 entries/137 pubs, tests PASS, docs copy identical |
| s8 | Milestone 4: site data + pipeline + dictionary (#34–36) | agent: site-data | done — events.json (81), stories.json (13) in data/ and docs/data/, convert_csv.py round-trip proven, DATA_DICTIONARY.md, test_site_data.py PASS. Committed 7f1bfad |
| s9 | Milestone 5: design direction (#37) + map decision (#41) | agent: design | done — DESIGN_DIRECTION.md (now 366 lines incl. material language); #41 decided skip-map with city bar alternative; both closed |
| s10 | Milestone 6: fact-check, alt text, usability (#42–44) | — | pending |
| s18 | Land sweep + clippings: commit, push, closeout | agent: commit | done — 7e5143d (263 files, sweep + wiki regen) + 60bba17 (57 files, 55 clippings). Pushed 425b831..60bba17, noreply email verified. #54 closed, #47 comment ...18083539. type-specimen.html deliberately uncommitted pending Joe's font pick |
| s19 | Mobile audit #56 (launch gate) | agents: audit + fix | audit done — 0 overflow, 0 console errors, hero 2 lines, menu/search/filters/pagination all work by touch. 8 tap-target defects (mobile menu links/buttons, footer links, timeline bar 18px hit area, wiki tag/city links 17px, top nav 14px at 768). Director spot-verified defect 2 (#mobile-menu-btn has no padding). Fix agent running: pages + styles + generator template (never hand-edit docs/wiki), re-measure to >=44px. Woven agent fenced to new files only to avoid collisions |
| s20 | Woven build #50–53 | agent: woven-build (opus) | running — from WOVEN_SPEC.md; must derive true ghost count (spec 98 vs issue 93), vendor three.js r171, a11y twin, 375px mode, no commit. Joe directive after preview: concept approved, but "impossible to read and parse even on desktop" — legibility is now the top acceptance criterion (progressive disclosure, readable labels, hover isolation, legend, readable default camera). Steering sent |
| s11 | Joe directive: "wood and fabric" material language | agent: design-amend | spec done (tokens walnut/linen/oak/thread, stain accent ramp #e2662b/#f0854a/#8f3a14, 16-pair AA contrast table, CSS texture recipes with opt-outs). Implementation (#48) was done pass 1+2 with screenshot verification, then WIPED by the reset incident — must be redone after remote reconciliation |
| s12 | Joe directive: "Woven" three.js experience (#49–53) | agent: woven-spec | WOVEN_SPEC.md done. Clip production (#54): agent produced 63 clips + docs/data/clippings.json; director verify caught 8 exclusion violations (2 Right On! CA-era, 6 out-of-state — the 6 empty-publicationIds entries); fixed and director-verified: 55 clips on disk = 55 entries (crop_first 32, publishable 16, with_credit 7), 0 empty publicationIds, EXCLUDED set enforced in all 5 processors. #54 done pending commit |
| s13 | Joe directive: full GitHub tracking | agent: tracking | done — issues #48–55 on milestone 5 + project 3, #47 creative-direction update posted (…18083077) |
| s14 | #39 timeline upgrade | agent: timeline | was done and browser-verified (stacked bars, incident row, keyboard a11y), then WIPED by the reset incident — redo after reconciliation. #39 is closed on GitHub; reopen or track redo under #48 |
| s15 | Production bug: publication.js duplicate const years | — | already fixed on origin (ba25d47) by the other workstream; live site OK |
| s16 | Reconcile local commits vs remote 18 | agents: analysis, merge, remap | merged (8b6c60a) with remote activity corrections canonical + evidence regenerated (d13ac61); id-60 duplicate remapped onto 126 (968b6f5, catalog 137 rows / 181 keepers, ALL tests pass). Remote briefing: no live build step (Tailwind scaffolding unreferenced, CDN stays), provenance = Joe + Cassandra + a Claude web session + a Codex PR. No peer session on this repo |
| s17 | Push blocked by GH007 (montclair.edu email on all 7 local commits; GitHub privacy guard) | director | ruling: rewrite local-only commits to Joe's GitHub noreply (6799804+jamditis@users.noreply.github.com — matches remote's existing practice); repo-local git config already set for future commits; history rewrite + push runs after the redo agents' work is committed (needs clean tree). Joe can override |

## Rules in force

- All prior standing rulings hold (Right On! exclusion, NJ-only keepers, cropped/cited/cleared before docs/).
- .chrome-cdp/ and archival media never enter git history.
- Every agent report checked against disk before it is believed.
- NO destructive git commands by agents (see incident log).
- NO blanket process kills by agents (no taskkill /IM, no pkill by name). An agent must kill only the exact PID it started. Incident 2026-08-19: a cleanup taskkill /IM python.exe killed 4 unrelated processes, including the docs preview server and browser_daemon.py.
- Sentence case everywhere. Plain-English #47 updates after each milestone.
- Strict ASD-STE100 in all director communication: replies to Joe, this plan, the handoff, agent briefs, and #47 updates. Use short sentences, active voice, and simple tenses. Give one instruction per sentence. Director ruling: the rule does not change the website's editorial text; Joe can override.

## Directives from Joe this session

- Design must feel like "wood and fabric" (intentionally vague, creative interpretation wanted).
- Build something interactive, beautiful, culturally meaningful with the data in three.js. Think big and ambitious. Concept pitched and elaborated: "Woven" (loom of 138 threads, evidence-weight thickness, 13 story tours, ghost cloth for the 93 catalog-only pubs, a11y twin, WebGL fallback).
- The redesign must be fully tracked on GitHub issues, milestone, project board, and discussion — done (issues #48–55, plus #56 mobile).
- Every page must be fully responsive and mobile friendly (issue #56; also a launch gate and a Woven requirement).
- Type/slop sweep status: pass 1 verified on disk (no hover:italic, hero clamp text-[clamp(1.9rem,6vw,4.75rem)] = 2 lines everywhere, pills gone, Fraunces out of main pages + js). Root cause of Joe's "not responsive": 128px hero overflowed its 8-col track after tracking-tighter removal — layout break, not JS (0 console errors, no 375px overflow). CAUGHT: Fraunces still in ~190 generated wiki pages — agent resumed to fix scripts/generate_html_wiki.py template and regenerate. docs/css/tailwind.css keeps Fraunces but is unreferenced (Codex artifact) — left alone by ruling. Font pick pending: Joe chooses from docs/type-specimen.html (Libre Franklin provisional, Archivo, Oswald, Barlow Condensed, League Gothic).
- Global prohibition on AI slop design tells: no eyebrow text, no italics in hero titles, no status pills/badges, no serif overuse — and Joe has since ruled Fraunces OUT entirely: pick a new display face (wood-type-era condensed grotesque direction, judged against the slop list), DM Sans body stays unless the type agent argues otherwise; plus the researched definitive list (data/research/design/AI_SLOP_PROHIBITIONS.md, being compiled). Applies to all pages and Woven.
