"""Point Wayback hits at real local PNGs. Drop paths whose files were deleted."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT_PATH = ROOT / "data" / "research" / "source-catalog.json"
SHOTS = ROOT / "data" / "research" / "wayback" / "snapshots"


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    for row in cat["publications"]:
        keepers = [
            h
            for h in row.get("keepers", [])
            if h.get("localFile") and (ROOT / h["localFile"]).exists()
            and (
                "wayback" in (h.get("kind") or "")
                or "Wayback" in (h.get("source") or "")
            )
        ]
        keeper_file = keepers[0]["localFile"] if keepers else None
        wb = row["sources"]["wayback"]
        for hit in wb.get("hits") or []:
            lf = hit.get("localFile")
            if lf and not (ROOT / lf).exists():
                print("clear gone", row["id"], lf)
                hit["localFile"] = None
        if keeper_file:
            for hit in wb.get("hits") or []:
                if not hit.get("localFile"):
                    hit["localFile"] = keeper_file
                    print("wired", row["id"], hit.get("title"), "->", keeper_file)
                    break
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
