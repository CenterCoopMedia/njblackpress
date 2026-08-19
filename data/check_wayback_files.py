"""Check whether Wayback localFile paths exist on disk."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))

print("=== keepers ===")
for r in CAT["publications"]:
    for h in r.get("keepers", []):
        if "wayback" not in (h.get("kind") or "") and "Wayback" not in (h.get("source") or ""):
            continue
        lf = h.get("localFile")
        p = ROOT / lf if lf else None
        ok = bool(p and p.exists())
        print(r["id"], "OK" if ok else "MISSING", lf, h.get("url"))

print("=== wayback hits ===")
for r in CAT["publications"]:
    for h in r["sources"].get("wayback", {}).get("hits") or []:
        lf = h.get("localFile")
        if not lf:
            print(r["id"], "NULL ", (h.get("title") or "")[:30], (h.get("url") or "")[:80])
            continue
        p = ROOT / lf
        print(r["id"], "OK  " if p.exists() else "GONE", lf)
