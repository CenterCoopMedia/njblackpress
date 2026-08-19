"""Attach leftover 1950s Danky leaf keepers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DANKY = ROOT / "data" / "research" / "danky"
CAT = ROOT / "data" / "research" / "source-catalog.json"
PUBS = ROOT / "data" / "publications.json"
CLIP_CAT = ROOT / "data" / "research" / "newspapers-com" / "clips" / "catalog.json"

KEEPERS = [
    {
        "id": 72,
        "clip_id": "danky-1998-hours-after",
        "src": "danky-leaf-p280-n323-hours-after.jpg",
        "dest": "danky-1998-p280-hours-after.jpg",
        "page": "280",
        "url": "https://archive.org/details/africanamericanne00dank/page/280/mode/1up",
        "caption": "Danky entry 2945: Hours After, biweekly, Newark, editor Tiny Prince. WHi 4 Apr 1951.",
        "quote": "Hours After. 1951?-? Frequency: Biweekly. Newark, NJ. Published by B.K. & L. Printing Co. Last issue 28 pages. Height 19 cm. Previous editor(s): Tiny Prince. OCLC no. 35268993. \"The picture guide to entertainment.\" WHi Apr 4, 1951 Pam 96-536.",
    },
    {
        "id": 66,
        "clip_id": "danky-1998-jersey-camera",
        "src": "danky-leaf-p312-n355-jersey-camera.jpg",
        "dest": "danky-1998-p312-jersey-camera.jpg",
        "page": "312",
        "url": "https://archive.org/details/africanamericanne00dank/page/312/mode/1up",
        "caption": "Danky entry 3284: Jersey Camera, monthly, Newark, 48 pages. WHi v.1 n.6 Aug 1951.",
        "quote": "Jersey Camera. 1951-? Frequency: Monthly. Newark, NJ. Published by Jersey Camera Publishing Co. Last issue 48 pages. Height 18 cm. OCLC no. 35047555. Subject focus: Profiles, Fraternal organizations. WHi v.1, n.6 Pam 72-1634 Aug, 1951.",
    },
    {
        "id": 18,
        "clip_id": "danky-1998-liberator-paterson",
        "src": "danky-leaf-p336-n379-liberator-paterson.jpg",
        "dest": "danky-1998-p336-liberator-paterson.jpg",
        "page": "336",
        "url": "https://archive.org/details/africanamericanne00dank/page/336/mode/1up",
        "caption": "Danky entry 3527: The Liberator, weekly, Paterson, editor Theodore Hinton. NjPatPhi v.1 n.1-4 Aug 5-26 1950.",
        "quote": "The Liberator. 1950-? Frequency: Weekly. Paterson, NJ. Last issue 8 pages. Height 43 cm. Previous editor(s): Theodore Hinton. NjPatPhi v.1, n.1-4 Periodicals Aug 5-26, 1950.",
    },
    {
        "id": 11,
        "clip_id": "danky-1998-nnj-informer",
        "src": "danky-leaf-p431-n474-informer.jpg",
        "dest": "danky-1998-p431-nnj-informer.jpg",
        "page": "431",
        "url": "https://archive.org/details/africanamericanne00dank/page/431/mode/1up",
        "caption": "Danky entry 4485: The Northern New Jersey Informer, weekly, Paterson. NjPatPhi v.1 Apr 1-June 17 1950.",
        "quote": "The Northern New Jersey Informer. 1950-? Frequency: Weekly. Paterson, NJ. Last issue 8 pages. Height 43 cm. NjPatPhi v.1 Periodicals Apr 1-June 17, 1950.",
    },
]

FACTS = {
    72: (
        " Danky and Hady 1998 entry 2945: biweekly entertainment picture guide, Newark, "
        "B.K. & L. Printing Co., editor Tiny Prince, 28 pages. WHi holds 4 Apr 1951 (Pam 96-536). "
        "OCLC 35268993."
    ),
    66: (
        " Danky and Hady 1998 entry 3284: monthly, Newark, Jersey Camera Publishing Co., "
        "48 pages, 18 cm, profiles and fraternal organizations. WHi v.1 n.6 Aug 1951 (Pam 72-1634). "
        "OCLC 35047555."
    ),
    18: (
        " Danky and Hady 1998 entry 3527: weekly, Paterson, 8 pages, editor Theodore Hinton. "
        "Passaic County Historical Society (NjPatPhi) holds v.1 n.1-4 dated 5-26 Aug 1950. "
        "Not the 1831 Garrison Liberator, the 1970 Edison college paper, or the 1961 New York monthly."
    ),
    11: (
        " Danky and Hady 1998 entry 4485: weekly, Paterson, 8 pages. "
        "NjPatPhi holds v.1 dated 1 Apr-17 June 1950."
    ),
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}
    clip_doc = json.loads(CLIP_CAT.read_text(encoding="utf-8"))
    existing = {c["id"] for c in clip_doc["clips"]}

    for item in KEEPERS:
        src = DANKY / item["src"]
        dest = DANKY / item["dest"]
        if not src.exists():
            raise SystemExit(f"missing {src}")
        dest.write_bytes(src.read_bytes())
        rel = str(dest.relative_to(ROOT)).replace("\\", "/")
        hit = {
            "kind": "catalog_record",
            "title": item["caption"],
            "url": item["url"],
            "localFile": rel,
            "source": "Danky and Hady, African-American Newspapers and Periodicals",
            "date": "1998",
            "caption": item["caption"],
        }
        row = rows[item["id"]]
        if not any(h.get("url") == item["url"] for h in row["keepers"]):
            row["keepers"].append(hit)
        row["status"] = "has_keeper"
        ia = row["sources"]["internet_archive"]
        ia["searched"] = True
        if not any(h.get("url") == item["url"] for h in ia.get("hits") or []):
            ia.setdefault("hits", []).append(hit)
        if "Danky and Hady 1998" not in (ia.get("notes") or ""):
            ia["notes"] = ((ia.get("notes") or "") + "; " + item["caption"]).strip("; ")
        other = row["sources"]["other"]
        other["searched"] = True
        if "Danky and Hady 1998" not in (other.get("notes") or ""):
            other["notes"] = (
                (other.get("notes") or "")
                + "; NPL/Rutgers/NJSL pages do not list this title. Danky and Hady 1998 does."
            ).strip("; ")
        if item["clip_id"] not in existing:
            clip_doc["clips"].append(
                {
                    "id": item["clip_id"],
                    "about": row["name"],
                    "aboutId": item["id"],
                    "sourcePaper": "Danky and Hady 1998",
                    "sourceCity": "Cambridge, Massachusetts",
                    "date": "1998",
                    "page": item["page"],
                    "url": item["url"],
                    "localImage": item["dest"],
                    "quote": item["quote"],
                    "why": item["caption"],
                }
            )
            existing.add(item["clip_id"])

    for pid, extra in FACTS.items():
        pub = by_pub[pid]
        if extra[20:50] not in (pub.get("historicalNotes") or ""):
            pub["historicalNotes"] = (pub.get("historicalNotes") or "") + extra

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
