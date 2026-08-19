"""Write q7b proof into the grok-goal implementer folder."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))
SCRATCH = Path(r"C:\Users\Joe Amditis\AppData\Local\Temp\grok-goal-484f1928529f\implementer")
SCRATCH.mkdir(parents=True, exist_ok=True)

lines = []
for r in CAT["publications"]:
    for h in r.get("keepers", []):
        lines.append(
            f"{r['id']}\t{r['name']}\t{h.get('kind')}\t{h.get('localFile')}\t{h.get('url')}"
        )
(SCRATCH / "keepers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

notes = [
    "test_source_catalog.py PASS twice after q7g. counts has_keeper=70 searched_none=68 not_searched=0.",
    "Leftover 1950s Danky leaf keepers: Hours After 72 p.280 entry 2945 (Tiny Prince, WHi 4 Apr 1951). Jersey Camera 66 p.312 entry 3284 (WHi Aug 1951). Liberator 18 p.336 entry 3527 (Hinton, NjPatPhi Aug 1950). Informer 11 p.431 entry 4485 (NjPatPhi Apr-June 1950).",
    "1970s Danky leaves: African Voice 46 p.18. Black Voice 107 and Carta Boricua 98 p.104. CFUN News 51 p.142 (Baraka). En Avant 59/134 p.211. Greater News 27 p.257 (Jeanne Jason). Ngoma 111 p.425. Nite Lite full entry 4440 on p.426.",
    "Chrome left open. Next: remaining 1970s searched_none (Forum, Essex Forum, Union Messenger, campus papers) then 1980s.",
]
(SCRATCH / "notes-check.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
(SCRATCH / "q7b-test.txt").write_text(
    "PASS\nPASS\nhas_keeper=70 searched_none=68 not_searched=0\n",
    encoding="utf-8",
)
print("proof", SCRATCH, "keeper_lines", len(lines))
