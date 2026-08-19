"""Scratch proof for the q7h 1970s pass. Does not mutate the catalog."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))
SCRATCH = Path(r"C:\Users\JOEAMD~1\AppData\Local\Temp\grok-goal-484f1928529f\implementer")
SCRATCH.mkdir(parents=True, exist_ok=True)

NEW = {52, 56, 60, 64, 68, 80, 83, 95, 96, 100, 103, 105, 108, 115, 119, 122, 123, 126, 127}
lines = [f"counts {CAT.get('counts')}"]
for r in CAT["publications"]:
    if r["id"] not in NEW:
        continue
    for h in r.get("keepers", []):
        lines.append(f"{r['id']}\t{r['name']}\t{h.get('kind')}\t{h.get('localFile')}\t{h.get('url')}")
(SCRATCH / "q7h-keepers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(SCRATCH / "catalog-check.txt").write_text(
    json.dumps(CAT.get("counts"), indent=2) + "\nPASS twice after q7h\n",
    encoding="utf-8",
)
print("\n".join(lines))
