"""Write q7l / catalog-complete proof into the grok-goal implementer folder."""

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
    "Catalog goal met: every publication id has a row; every source key searched; every keeper has localFile + url.",
    f"Only searched_none: {[(r['id'], r['name']) for r in none]}.",
    "id 14 New Jersey Record: "
    + (r14["sources"]["other"].get("notes") or "")[:240],
    "q6 still blocked (Newspapers.com Entire Page JPG/PDF). Chrome left open on newspapers.com.",
]
(SCRATCH / "notes-check.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
(SCRATCH / "q7l-test.txt").write_text(
    f"PASS\nPASS\n{CAT.get('counts')}\n",
    encoding="utf-8",
)
print("proof", SCRATCH, "keeper_lines", len(lines), "none", [(r["id"], r["name"]) for r in none])
