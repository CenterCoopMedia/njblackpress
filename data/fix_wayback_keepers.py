"""Keep only earliest Wayback snapshot as a keeper; drop latest-only URL keepers."""

from __future__ import annotations

import json
from pathlib import Path

CAT = Path(__file__).resolve().parent / "research" / "source-catalog.json"


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    dropped = 0
    for row in cat["publications"]:
        keep = []
        for hit in row.get("keepers", []):
            if hit.get("kind") != "wayback_snapshot":
                keep.append(hit)
                continue
            title = hit.get("title") or ""
            if title.startswith("latest"):
                dropped += 1
                continue
            keep.append(hit)
        row["keepers"] = keep
        if not row["keepers"] and row["status"] == "has_keeper":
            searched = any(s["searched"] for s in row["sources"].values())
            row["status"] = "searched_none" if searched else "not_searched"
        elif row["keepers"]:
            row["status"] = "has_keeper"
    CAT.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("dropped_latest", dropped)


if __name__ == "__main__":
    main()
