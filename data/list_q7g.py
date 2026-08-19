"""List leftover 1950s and 1970s searched_none titles."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
pubs = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))["publications"]
cat = json.loads((ROOT / "research/source-catalog.json").read_text(encoding="utf-8"))
rows = {r["id"]: r for r in cat["publications"]}
none = [p for p in pubs if rows[p["id"]]["status"] == "searched_none"]

print("LEFTOVER 1950s")
for p in pubs:
    if p["id"] in {11, 18, 66, 72}:
        print(p["id"], p["name"], p["city"], p["yearFounded"], rows[p["id"]]["status"])

print("\n1970s civic searched_none")
n70 = 0
for p in none:
    y = p.get("yearFounded") or 0
    if 1970 <= y <= 1979:
        n70 += 1
        staff = (p.get("keyStaff") or "")[:50]
        print(f"{p['id']:3} {p['name'][:40]:40} {str(p.get('city') or ''):16} {y} {staff}")
print("count 1970s none", n70, "total none", len(none))
