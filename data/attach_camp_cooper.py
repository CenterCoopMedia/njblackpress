"""Attach the 1936 Camp Cooper paper mention and write CCC none notes."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "data" / "research" / "newspapers-com" / "screenshots"
CLIPS = ROOT / "data" / "research" / "newspapers-com" / "clips"
CAT = ROOT / "data" / "research" / "source-catalog.json"
PUBS = ROOT / "data" / "publications.json"
CLIP_CAT = CLIPS / "catalog.json"

KEEPER = {
    "id": 87,
    "clip_id": "camp-cooper-1936-courier-post",
    "src": "q7gopen-reed-berlin-1936.png",
    "dest": "camp-cooper-1936-01-06-courier-post.png",
    "source": "Courier-Post",
    "sourceCity": "Camden, New Jersey",
    "date": "1936-01-06",
    "page": "3",
    "url": "https://www.newspapers.com/image/447571125/",
    "caption": "Courier-Post: CCC Company 1275 at Erlton started a journalism class and turns out a paper, Camp Cooper, regularly. Educational advisor A. W. Reed.",
    "quote": "There has been started a class in journalism, and the students turn out a paper, \"Camp Cooper,\" regularly.",
}

NONE_NOTES = {
    48: "Bertram Totten quoted search: 0 NJ cards. Ash Can plus CCC/Chatsworth was a 1934 trash-can coupon story.",
    55: "Rugcuttings / Point Breeze CCC 1937-1939: 0 NJ cards on first page.",
    89: "Sixty Niner / Sixty-Niner CCC: one NJ card, 2000 Courier-Post horse racing, not the camp paper.",
    90: "Little Ease Echo: 1 match, 0 NJ cards.",
    94: "Dias Creek Echo: no result cards.",
    97: "Rifle Ranger CCC 1937-1939: 0 NJ cards.",
    102: "A. W. Reed CCC opened 1936 Camden pages about Company 1275 at Erlton. The named paper is Camp Cooper, not Camp Berlin Broadcast.",
    136: "Penn Crusader and James W. Richardson CCC: 0 NJ cards.",
    137: "Pine Needle New Lisbon opened 1975/1994 pages (Tokyo Pine Needle House; unrelated). Milledge Cato / Marvello Gilbert: 1994 Courier-Post, not the camp paper.",
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}
    clip_doc = json.loads(CLIP_CAT.read_text(encoding="utf-8"))
    seen = {c["id"] for c in clip_doc["clips"]}

    src = SHOTS / KEEPER["src"]
    dest = CLIPS / KEEPER["dest"]
    if not src.exists():
        raise SystemExit(f"missing {src}")
    dest.write_bytes(src.read_bytes())
    rel = str(dest.relative_to(ROOT)).replace("\\", "/")
    hit = {
        "kind": "clip",
        "title": KEEPER["caption"],
        "url": KEEPER["url"],
        "localFile": rel,
        "source": KEEPER["source"],
        "date": KEEPER["date"],
        "caption": KEEPER["caption"],
    }
    row = rows[KEEPER["id"]]
    if not any(h.get("url") == KEEPER["url"] for h in row["keepers"]):
        row["keepers"].append(hit)
    row["status"] = "has_keeper"
    np = row["sources"]["newspapers_com"]
    np["searched"] = True
    if not any(h.get("url") == KEEPER["url"] for h in np.get("hits") or []):
        np.setdefault("hits", []).append(hit)
    if KEEPER["clip_id"] not in seen:
        clip_doc["clips"].append(
            {
                "id": KEEPER["clip_id"],
                "about": row["name"],
                "aboutId": KEEPER["id"],
                "sourcePaper": KEEPER["source"],
                "sourceCity": KEEPER["sourceCity"],
                "date": KEEPER["date"],
                "page": KEEPER["page"],
                "url": KEEPER["url"],
                "localImage": KEEPER["dest"],
                "quote": KEEPER["quote"],
                "why": KEEPER["caption"],
            }
        )

    for pid, note in NONE_NOTES.items():
        np = rows[pid]["sources"]["newspapers_com"]
        np["searched"] = True
        old = np.get("notes") or ""
        if note[:30] not in old:
            np["notes"] = (old + "; " + note).strip("; ")

    cc = by_pub[87]
    extra = (
        " Courier-Post 6 Jan 1936: Company 1275 at the Erlton camp (after two years in North Jersey) "
        "started a journalism class and turns out a paper titled Camp Cooper regularly. Educational "
        "advisor A. W. Reed. Commanding officer Capt. A. C. Wiese. Same Company 1275-C also cataloged "
        "with Camp Berlin Broadcast and later Cape May / Glassboro titles."
    )
    if "Camp Cooper" not in (cc.get("historicalNotes") or ""):
        cc["historicalNotes"] = (cc.get("historicalNotes") or "") + extra
    if cc.get("alternateName") in (None, ""):
        cc["alternateName"] = "Camp Cooper"

    cat["publications"] = [rows[i] for i in sorted(rows)]
    cat["counts"] = {
        "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
    }
    CAT.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    PUBS.write_text(json.dumps(pubs, indent=2, ensure_ascii=False), encoding="utf-8")
    CLIP_CAT.write_text(json.dumps(clip_doc, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copyfile(PUBS, ROOT / "docs" / "data" / "publications.json")
    print("counts", cat["counts"])


if __name__ == "__main__":
    main()
