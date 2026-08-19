"""Do not treat Wayback offline interstitials as publication keepers."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "data" / "research" / "source-catalog.json"
SHOTS = ROOT / "data" / "research" / "wayback" / "snapshots"

# Identical 59084-byte PNGs are the IA "Temporarily Offline" page.
OFFLINE_SIZE = 59084


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    offline_names = set()
    for p in SHOTS.glob("*.png"):
        if p.stat().st_size == OFFLINE_SIZE:
            offline_names.add(p.name)
            p.unlink()
    for row in cat["publications"]:
        keep = []
        for hit in row.get("keepers", []):
            name = Path(hit.get("localFile") or "").name
            if name in offline_names:
                row["sources"]["wayback"]["notes"] = (
                    (row["sources"]["wayback"].get("notes") or "")
                    + "; earliest replay returned Wayback Temporarily Offline 2026-08-17"
                ).strip("; ")
                continue
            keep.append(hit)
        row["keepers"] = keep
        row["status"] = "has_keeper" if keep else "searched_none"
    cat["counts"] = {
        "has_keeper": sum(1 for r in cat["publications"] if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in cat["publications"] if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in cat["publications"] if r["status"] == "not_searched"),
    }
    CAT.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("offline_shots", sorted(offline_names))
    print("counts", cat["counts"])


if __name__ == "__main__":
    main()
