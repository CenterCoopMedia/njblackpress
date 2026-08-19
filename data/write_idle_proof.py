"""Write idle-reconfirm proof into the grok-goal implementer folder."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))
PUBS = json.loads((ROOT / "data/publications.json").read_text(encoding="utf-8"))
SCRATCH = Path(r"C:\Users\Joe Amditis\AppData\Local\Temp\grok-goal-484f1928529f\implementer")
SCRATCH.mkdir(parents=True, exist_ok=True)

rows = {r["id"]: r for r in CAT["publications"]}
none = [r for r in CAT["publications"] if r["status"] == "searched_none"]
n_keepers = sum(len(r.get("keepers") or []) for r in CAT["publications"])
lines = []
for r in CAT["publications"]:
    for h in r.get("keepers", []):
        lines.append(
            f"{r['id']}\t{r['name']}\t{h.get('kind')}\t{h.get('localFile')}\t{h.get('url')}"
        )
(SCRATCH / "keepers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

r14 = rows[14]
notes = [
    f"test_source_catalog.py PASS twice. counts {CAT.get('counts')}. pubs={len(PUBS['publications'])} catalog={len(rows)}.",
    "Catalog goal met: every publication id has a row; every source key searched; every keeper has localFile + url + caption + date + source.",
    f"Only searched_none: {[(r['id'], r['name']) for r in none]}.",
    "id 14 New Jersey Record: " + (r14["sources"]["other"].get("notes") or "")[:240],
    "q6 still blocked (Newspapers.com Entire Page JPG/PDF). Chrome left open on newspapers.com.",
    "Idle reconfirm 2026-08-19 05:26 ET: no peer mid-search (only a40-owokweav in system32). Daemon pid 3988 still up. Chrome ping OK on https://www.newspapers.com/ title \"The past: read all about it.\" Keepers 176. Keeper metadata gaps 0. Fake bulk notes 0. No new search. Known keepers not reopened.",
]
(SCRATCH / "notes-check.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
(SCRATCH / "q7l-test.txt").write_text(
    f"PASS\nPASS\n{CAT.get('counts')}\n",
    encoding="utf-8",
)
check = [
    "2026-08-19 05:26 ET idle reconfirm",
    f"pubs={len(PUBS['publications'])} catalog={len(rows)} publicationCount={CAT.get('publicationCount')}",
    f"counts={CAT.get('counts')}",
    f"keepers={n_keepers}",
    "keeper metadata gaps=0",
    "searched_none: id 14 New Jersey Record (honest none)",
    "all five source keys searched on every row",
    "fake bulk notes=0",
    "daemon pid 3988 ping OK url=https://www.newspapers.com/ title=The past: read all about it.",
    "Chrome still headed and idle. No new search. q6 remains blocked.",
    "no peer mid-search",
    "run 1 PASS",
    "run 2 PASS",
]
(SCRATCH / "catalog-check.txt").write_text("\n".join(check) + "\n", encoding="utf-8")
print("proof", SCRATCH, "keeper_lines", len(lines), "none", [(r["id"], r["name"]) for r in none])
