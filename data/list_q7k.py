"""List last five searched_none titles with catalog notes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
pubs = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))["publications"]
cat = json.loads((ROOT / "research/source-catalog.json").read_text(encoding="utf-8"))
rows = {r["id"]: r for r in cat["publications"]}

print("counts", cat.get("counts"))
print()
for p in pubs:
    r = rows[p["id"]]
    if r["status"] != "searched_none":
        continue
    print("=" * 70)
    print(p["id"], p["name"], "|", p.get("city"), p.get("yearFounded"), "-", p.get("yearCeased"))
    print("publishers:", p.get("publishers"))
    print("staff:", p.get("keyStaff"))
    print("archive:", p.get("archiveUrl"))
    print("web:", p.get("websiteUrl"))
    print("notes:", (p.get("historicalNotes") or "")[:400])
    for key, src in r["sources"].items():
        print(f"  {key}: searched={src.get('searched')} notes={(src.get('notes') or '')[:220]}")
        for h in (src.get("hits") or [])[:3]:
            print("   hit:", h.get("kind"), h.get("title"), h.get("url"))
    print("  keepers:", len(r.get("keepers") or []))
