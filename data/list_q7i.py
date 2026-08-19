"""List Forum leftovers and 1980s searched_none civic titles."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
pubs = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))["publications"]
cat = json.loads((ROOT / "research/source-catalog.json").read_text(encoding="utf-8"))
rows = {r["id"]: r for r in cat["publications"]}

print("FORUMS")
for p in pubs:
    name = (p.get("name") or "").lower()
    if "forum" in name or p["id"] in {39, 42}:
        r = rows[p["id"]]
        print(p["id"], p["name"], p.get("city"), p.get("yearFounded"), r["status"])

print("\n1980s searched_none")
none = [p for p in pubs if rows[p["id"]]["status"] == "searched_none"]
for p in none:
    y = p.get("yearFounded") or 0
    if 1980 <= y <= 1989:
        print(
            f"{p['id']:3} {p['name'][:44]:44} {str(p.get('city') or ''):16} {y} "
            f"{(p.get('keyStaff') or '')[:40]}"
        )
print("1980s none", sum(1 for p in none if 1980 <= (p.get("yearFounded") or 0) <= 1989))
print("total none", len(none))
print("counts", cat.get("counts"))
