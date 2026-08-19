"""Point earliest Wayback keepers at screenshots already on disk."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAT = ROOT / "research" / "source-catalog.json"
SHOTS = ROOT / "research" / "wayback" / "snapshots"


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    files = {p.stem.split("-", 1)[0]: p for p in SHOTS.glob("*.png")}
    n = 0
    for row in cat["publications"]:
        key = f"{row['id']:03d}"
        dest = files.get(key)
        if not dest:
            continue
        rel = str(dest.relative_to(ROOT.parent)).replace("\\", "/")
        for hit in row.get("keepers", []):
            if hit.get("kind") == "wayback_snapshot" and (hit.get("title") or "").startswith("earliest"):
                hit["localFile"] = rel
                n += 1
    CAT.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("attached", n, "existing", len(files))


if __name__ == "__main__":
    main()
