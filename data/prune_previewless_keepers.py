"""Move keepers without a local preview out of the keepers list."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "data" / "research" / "source-catalog.json"
CLIPS = ROOT / "data" / "research" / "newspapers-com" / "clips"


def exists(local: str | None) -> bool:
    if not local:
        return False
    p = ROOT / local if not Path(local).is_absolute() else Path(local)
    return p.exists() or (CLIPS / Path(local).name).exists()


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    pruned = 0
    for row in cat["publications"]:
        keep, drop = [], []
        for hit in row.get("keepers", []):
            if exists(hit.get("localFile")):
                keep.append(hit)
            else:
                drop.append(hit)
                pruned += 1
        row["keepers"] = keep
        if drop:
            row.setdefault("previewlessHits", []).extend(drop)
        if row["keepers"]:
            row["status"] = "has_keeper"
        else:
            row["status"] = "searched_none"
    cat["counts"] = {
        "has_keeper": sum(1 for r in cat["publications"] if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in cat["publications"] if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in cat["publications"] if r["status"] == "not_searched"),
    }
    CAT.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("pruned", pruned, "counts", cat["counts"])


if __name__ == "__main__":
    main()
