"""Attach verified 1950s keepers and write Danky facts into notes."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "data" / "research" / "newspapers-com" / "screenshots"
DANKY = ROOT / "data" / "research" / "danky"
CLIPS = ROOT / "data" / "research" / "newspapers-com" / "clips"
CAT = ROOT / "data" / "research" / "source-catalog.json"
PUBS = ROOT / "data" / "publications.json"
CLIP_CAT = CLIPS / "catalog.json"
DANKY.mkdir(parents=True, exist_ok=True)

KEEPERS = [
    {
        "id": 67,
        "clip_id": "bronze-thrills-1960-app",
        "src": SHOTS / "q7nopen-bronze-thrills-1960.png",
        "dest": CLIPS / "bronze-thrills-1960-05-20-asbury-park-press.png",
        "kind": "clip",
        "source": "Asbury Park Press",
        "sourceCity": "Asbury Park, New Jersey",
        "date": "1960-05-20",
        "page": "21",
        "url": "https://www.newspapers.com/image/143086953/",
        "caption": "Asbury Park Press Lakewood column: a book to be published in the July issue of Bronze Thrills.",
        "quote": "recently wrote a book, based on her life entitled \"Out of Darkness to Light\" . . . It is to be published in the July issue of Bronze Thrills.",
    },
    {
        "id": 30,
        "clip_id": "danky-independent",
        "src": SHOTS / "q7q-independent-430.png",
        "dest": DANKY / "danky-1998-p430-north-jersey-independent.png",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "sourceCity": None,
        "date": "1998",
        "page": "430",
        "url": "https://archive.org/details/africanamericanne00dank/page/430/mode/1up",
        "caption": "Danky entry 4470: North Jersey Independent, Paterson, 1950-?, editor Albert E. Hart. NjPatPhi holds v.1 n.1 (18 Nov 1950).",
        "quote": "4470 North Jersey Independent. 1950-? Paterson, NJ. Previous editor(s): Albert E. Hart. NjPatPhi v.1, n.1 Nov 18, 1950.",
    },
    {
        "id": 129,
        "clip_id": "danky-club-world",
        "src": SHOTS / "q7r-club-world-158.png",
        "dest": DANKY / "danky-1998-p158-club-world.png",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "158",
        "url": "https://archive.org/details/africanamericanne00dank/page/158/mode/1up",
        "caption": "Danky entry 1642 starts on p.158: Club World Newsmagazine, 1955?-?, East Orange.",
        "quote": "1642 Club World: Newsmagazine. 1955?-? Frequency: Bimonthly. East Orange, NJ. Published by Scott, Young.",
    },
    {
        "id": 21,
        "clip_id": "danky-nite-lite",
        "src": SHOTS / "q7q-nite-lite-427.png",
        "dest": DANKY / "danky-1998-p427-nite-lite.png",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "427",
        "url": "https://archive.org/details/africanamericanne00dank/page/427/mode/1up",
        "caption": "Danky entry 4440 leftover on p.427: Nite Lite motto and DHU microfilm 1975-1976.",
        "quote": "Be in the know, on where to go. Available in microform from: DHU (1975-1976).",
    },
    {
        "id": 109,
        "clip_id": "danky-liberator-edison",
        "src": SHOTS / "q7r-liberator-336.png",
        "dest": DANKY / "danky-1998-p336-liberator-edison.png",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "336",
        "url": "https://archive.org/details/africanamericanne00dank/page/336/mode/1up",
        "caption": "Danky entry 3526: The Liberator, 1970-?, Edison NJ, Middlesex County College Urban Journalism Workshop.",
        "quote": "3526 The Liberator. 1970-? Frequency: Unknown. Edison, NJ. Published by Middlesex County College, Central New Jersey...",
    },
]

NOTES = {
    67: (
        "Danky 1998 entry 1209: monthly, Dover NJ, Sepia Publishing Company, 1952?-1981?, "
        "superseded by Intimacy. Editors Adelle Jackson; Edna K. Turner Jan 1955; Eunice Wilson. "
        "ISSN 0277-8106; OCLC 7645384; confession stories. Asbury Park Press 20 May 1960 notes a "
        "life story set for the July issue."
    ),
    30: (
        "Danky 1998 entry 4470: 1950-?, Paterson, 4 pages, editor Albert E. Hart. "
        "Passaic County Historical Society (NjPatPhi) holds v.1 n.1 dated 18 Nov 1950."
    ),
    129: (
        "Danky 1998 entry 1642: bimonthly newsmagazine, East Orange, Scott Young, editor "
        "Sally Cooke Young. OCLC 36218068. WHi Winter 1960; DHU Winter 1956-Winter 1959."
    ),
    21: (
        "Danky 1998 entry 4440: weekly, Newark, Edna M. Strothers, 16 pages. Motto "
        "\"Be in the know, on where to go.\" DHU microfilm 1975-1976."
    ),
    11: (
        "Danky 1998 entry 4485: weekly, Paterson, 8 pages. NjPatPhi holds v.1, 1 Apr-17 June 1950. "
        "No New Jersey Newspapers.com card named the paper on this pass."
    ),
    18: (
        "Danky 1998 entry 3527: weekly, Paterson, 8 pages, editor Theodore Hinton. "
        "NjPatPhi holds v.1 n.1-4, 5-26 Aug 1950. Newspapers.com Hinton hits were an Englewood "
        "lawyer (1940) and a WWII Liberator bomber casualty list (1943), not this weekly."
    ),
    66: (
        "Danky 1998 entry 3284: monthly, Newark, Jersey Camera Publishing Co., 48 pages, "
        "OCLC 35047555. WHi holds v.1 n.6, Aug 1951. Profiles / fraternal organizations."
    ),
    72: (
        "Danky 1998 entry 2945: biweekly, Newark, B.K. & L. Printing Co., editor Tiny Prince, "
        "28 pages, OCLC 35268993. \"The picture guide to entertainment.\" WHi 4 Apr 1951."
    ),
    109: (
        "Danky 1998 entry 3526: The Liberator, 1970-?, Edison NJ, Middlesex County College "
        "Central New Jersey Urban Journalism Workshop."
    ),
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}
    clip_doc = json.loads(CLIP_CAT.read_text(encoding="utf-8"))
    seen = {c["id"] for c in clip_doc["clips"]}

    for item in KEEPERS:
        if not item["src"].exists():
            raise SystemExit(f"missing {item['src']}")
        item["dest"].write_bytes(item["src"].read_bytes())
        rel = str(item["dest"].relative_to(ROOT)).replace("\\", "/")
        hit = {
            "kind": item["kind"],
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
        bucket = row["sources"]["newspapers_com"] if item["kind"] == "clip" else row["sources"]["other"]
        bucket["searched"] = True
        if not any(h.get("url") == item["url"] for h in bucket.get("hits") or []):
            bucket.setdefault("hits", []).append(hit)
        if item["kind"] == "clip" and item["clip_id"] not in seen:
            clip_doc["clips"].append(
                {
                    "id": item["clip_id"],
                    "about": row["name"],
                    "aboutId": item["id"],
                    "sourcePaper": item["source"],
                    "sourceCity": item.get("sourceCity"),
                    "date": item["date"],
                    "page": item["page"],
                    "url": item["url"],
                    "localImage": item["dest"].name,
                    "quote": item["quote"],
                    "why": item["caption"],
                }
            )
            seen.add(item["clip_id"])

    for pid, note in NOTES.items():
        p = by_pub[pid]
        old = p.get("historicalNotes") or ""
        if "Danky 1998 entry" not in old:
            p["historicalNotes"] = (old + " " + note).strip()
        if pid == 67:
            p["frequency"] = "Monthly"
        if pid == 129:
            p["frequency"] = "Bimonthly"
        if pid == 72:
            p["frequency"] = "Biweekly"
        if pid == 21:
            p["frequency"] = "Weekly"
        if pid == 11:
            p["frequency"] = "Weekly"

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
