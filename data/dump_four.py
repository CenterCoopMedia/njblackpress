"""Dump catalog + publication fields for the four leftover civic titles."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pubs = {p["id"]: p for p in json.loads((ROOT / "data/publications.json").read_text(encoding="utf-8"))["publications"]}
cat = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))
rows = {r["id"]: r for r in cat["publications"]}

for pid in (7, 3, 45, 79):
    p = pubs[pid]
    r = rows[pid]
    print("=" * 70)
    print(pid, p["name"], p.get("city"), p.get("yearFounded"), p.get("yearCeased"), r["status"])
    print("pub", p.get("publishers"), "| staff", p.get("keyStaff"))
    print("notes", (p.get("historicalNotes") or "")[:400])
    print("archive", p.get("archiveUrl"), "web", p.get("websiteUrl"))
    for key, src in r["sources"].items():
        print(f"  {key} searched={src.get('searched')} notes={(src.get('notes') or '')[:220]}")
        for h in (src.get("hits") or [])[:3]:
            print("    hit", (h.get("title") or "")[:120], h.get("url"))
