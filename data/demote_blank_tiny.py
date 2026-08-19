"""Remove the 7758-byte blank identity captures from keepers."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "data" / "research" / "source-catalog.json"
SHOTS = ROOT / "data" / "research" / "wayback" / "snapshots"
BLANK = {4: "004-black-in-jersey.png", 17: "017-trenton-journal.png"}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    names = set(BLANK.values())
    for row in cat["publications"]:
        if row["id"] not in BLANK:
            continue
        keep = []
        for hit in row.get("keepers", []):
            name = Path(hit.get("localFile") or "").name
            if name in names or (
                hit.get("kind") == "wayback_snapshot" and name in names
            ):
                continue
            keep.append(hit)
        row["keepers"] = keep
        row["status"] = "has_keeper" if keep else "searched_none"
        for hit in row["sources"]["wayback"].get("hits") or []:
            lf = hit.get("localFile") or ""
            if Path(lf).name in names:
                hit["localFile"] = None
        note = row["sources"]["wayback"].get("notes") or ""
        extra = "identity replay was a blank page; not a keeper 2026-08-17"
        if extra not in note:
            row["sources"]["wayback"]["notes"] = (note + "; " + extra).strip("; ")
        print("demoted", row["id"], row["status"])
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
