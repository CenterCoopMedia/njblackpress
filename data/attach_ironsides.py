"""Attach Ironsides Echo 1932 and 1940 NJ keepers and write staff/award facts."""

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

KEEPERS = [
    {
        "id": 57,
        "clip_id": "ironsides-1932-courier-post",
        "src": "q7d-ironsides-1932-courier.png",
        "dest": "ironsides-1932-03-22-courier-post-leon-snead.png",
        "source": "Courier-Post",
        "sourceCity": "Camden, New Jersey",
        "date": "1932-03-22",
        "page": "14",
        "url": "https://www.newspapers.com/image/446292432/",
        "caption": "Courier-Post: Ironsides Echo, monthly student paper of the Bordentown Manual Training School, won second place in the Columbia Scholastic Press contest. Student editor Leon Snead.",
        "quote": "The Ironsides Echo, published monthly and edited by students of the industrial school, won second place award among the technical and agricultural high schools. Leon Snead is student editor of the Ironsides Echo.",
    },
    {
        "id": 57,
        "clip_id": "ironsides-1940-trenton-times",
        "src": "q7copen-ironsides-school.png",
        "dest": "ironsides-1940-05-07-trenton-times-awards.png",
        "source": "The Times",
        "sourceCity": "Trenton, New Jersey",
        "date": "1940-05-07",
        "page": "13",
        "url": "https://www.newspapers.com/image/1191434889/",
        "caption": "Trenton Times: Ironsides Echo won two second-place Columbia awards. Staff adviser Frances O. Grant; printing instructor L. J. Roberts.",
        "quote": "The 'Ironsides Echo,' monthly newspaper edited and printed by students of Bordentown Manual Training and Industrial School, won two second place awards in the 16th annual contest for student newspapers and magazines recently conducted by Columbia University.",
    },
]

NONE_NOTES = {
    7: "Second founder pass: colored-newspaper Princeton hit the 1904 Echo fire clip, not The Citizen. Du Paur hits were 1952 Atlantic City (wrong person).",
    3: "C. N. Green plus editor/newspaper Camden opened 1921 Courier-Post; highlight was a baseball manager named Green, not the Camden News editor.",
    45: "Sarah Spencer Washington 1929 Press of Atlantic City is an Apex beauty-club reception, not Apex News. Archie J. Morgan search had 0 NJ cards.",
    79: "Hiram Star / Hiram Star-News Vauxhall 1945-1960 returned no result cards.",
    101: "After Hours plus Negro/colored/Newark 1947-1955 opened club/night-life pages, not the magazine.",
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}
    clip_doc = json.loads(CLIP_CAT.read_text(encoding="utf-8"))
    seen = {c["id"] for c in clip_doc["clips"]}

    for item in KEEPERS:
        src = SHOTS / item["src"]
        dest = CLIPS / item["dest"]
        if not src.exists():
            raise SystemExit(f"missing {src}")
        dest.write_bytes(src.read_bytes())
        rel = str(dest.relative_to(ROOT)).replace("\\", "/")
        hit = {
            "kind": "clip",
            "title": item["caption"],
            "url": item["url"],
            "localFile": rel,
            "source": item["source"],
            "date": item["date"],
            "caption": item["caption"],
        }
        row = rows[item["id"]]
        if not any(h.get("url") == item["url"] for h in row["keepers"]):
            row["keepers"].append(hit)
        row["status"] = "has_keeper"
        np = row["sources"]["newspapers_com"]
        np["searched"] = True
        if not any(h.get("url") == item["url"] for h in np.get("hits") or []):
            np.setdefault("hits", []).append(hit)
        if item["clip_id"] not in seen:
            clip_doc["clips"].append(
                {
                    "id": item["clip_id"],
                    "about": row["name"],
                    "aboutId": item["id"],
                    "sourcePaper": item["source"],
                    "sourceCity": item["sourceCity"],
                    "date": item["date"],
                    "page": item["page"],
                    "url": item["url"],
                    "localImage": item["dest"],
                    "quote": item["quote"],
                    "why": item["caption"],
                }
            )
            seen.add(item["clip_id"])

    for pid, note in NONE_NOTES.items():
        np = rows[pid]["sources"]["newspapers_com"]
        np["searched"] = True
        old = np.get("notes") or ""
        if note[:30] not in old:
            np["notes"] = (old + "; " + note).strip("; ")

    ie = by_pub[57]
    extra = (
        " Courier-Post 22 Mar 1932: monthly student paper; second place, Columbia Scholastic "
        "Press Association; student editor Leon Snead. Trenton Times 7 May 1940: two second-place "
        "Columbia awards; staff adviser Frances O. Grant; printing class taught by L. J. Roberts."
    )
    if "Leon Snead" not in (ie.get("historicalNotes") or ""):
        ie["historicalNotes"] = (ie.get("historicalNotes") or "") + extra
    staff = ie.get("keyStaff") or ""
    if "Leon Snead" not in staff:
        ie["keyStaff"] = (
            (staff + "; " if staff else "")
            + "Student editor (1932): Leon Snead; staff adviser (1940): Frances O. Grant; "
            "printing instructor: L. J. Roberts"
        )

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
