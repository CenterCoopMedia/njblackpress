"""List Wayback hits missing a local preview."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))

for r in CAT["publications"]:
    hits = r["sources"].get("wayback", {}).get("hits") or []
    if not hits:
        continue
    keepers = [
        h
        for h in r.get("keepers", [])
        if "wayback" in (h.get("kind") or "") or "Wayback" in (h.get("source") or "")
    ]
    nulls = [h for h in hits if not h.get("localFile")]
    print(
        f"{r['id']:3} {r['name'][:42]:42} {r['status']:14} "
        f"hits={len(hits)} keepers={len(keepers)} null={len(nulls)}"
    )
    for h in hits:
        print("   ", h.get("title"), "file=", h.get("localFile"), "url=", (h.get("url") or "")[:100])
