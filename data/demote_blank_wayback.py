"""Remove Wayback keepers that are blank replays or the offline interstitial."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "data" / "research" / "source-catalog.json"
SHOTS = ROOT / "data" / "research" / "wayback" / "snapshots"

# Visual review 2026-08-17: these PNGs are not publication pages.
DEMOTE = {
    4: "004-black-in-jersey.png",  # donate overlay + blank replay
    12: "012-five-wards-media.png",  # empty white replay
    17: "017-trenton-journal.png",  # empty grey replay
    20: "020-new-jersey-urban-news.png",  # empty white replay
    43: "043-public-square-amplified.png",  # empty white replay
    95: "095-right-on-.png",  # Temporarily Offline interstitial
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    names = set(DEMOTE.values())
    for row in cat["publications"]:
        if row["id"] not in DEMOTE:
            continue
        dropped = []
        keep = []
        for hit in row.get("keepers", []):
            name = Path(hit.get("localFile") or "").name
            if name in names or hit.get("kind") == "wayback_snapshot":
                dropped.append(name or hit.get("url"))
                continue
            keep.append(hit)
        row["keepers"] = keep
        row["status"] = "has_keeper" if keep else "searched_none"
        note = row["sources"]["wayback"].get("notes") or ""
        extra = "replay was blank or Temporarily Offline; not a keeper 2026-08-17"
        if extra not in note:
            row["sources"]["wayback"]["notes"] = (note + "; " + extra).strip("; ")
        print("demoted", row["id"], dropped)
    for name in names:
        path = SHOTS / name
        if path.exists():
            path.unlink()
            print("deleted", name)
    cat["counts"] = {
        "has_keeper": sum(1 for r in cat["publications"] if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in cat["publications"] if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in cat["publications"] if r["status"] == "not_searched"),
    }
    CAT.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("counts", cat["counts"])


if __name__ == "__main__":
    main()
