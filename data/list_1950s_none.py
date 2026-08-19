"""List 1950s civic searched_none titles."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pubs = json.loads((ROOT / "data/publications.json").read_text(encoding="utf-8"))["publications"]
cat = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))
rows = {r["id"]: r for r in cat["publications"]}

cands = []
for p in pubs:
    r = rows[p["id"]]
    if r["status"] != "searched_none":
        continue
    yf = p.get("yearFounded")
    if yf is None:
        continue
    yc = p.get("yearCeased")
    cands.append((yf, yc if yc is not None else 9999, p["id"], p["name"], p.get("city"), p.get("publishers"), p.get("keyStaff")))
cands.sort()
print("searched_none", len(cands))
for row in cands[:30]:
    print(f"{row[0]}-{row[1]} id={row[2]} {row[3]} | {row[4]} | pub={row[5]} | staff={row[6]}")
