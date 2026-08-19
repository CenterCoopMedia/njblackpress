"""Attach verified 1950s Danky/NP keepers and write honest none notes."""

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
        "id": 30,
        "clip_id": "danky-1998-north-jersey-independent",
        "src": "q7v-independent-430.png",
        "dest_dir": DANKY,
        "dest": "danky-1998-p430-north-jersey-independent.png",
        "page": "430",
        "url": "https://archive.org/details/africanamericanne00dank/page/430/mode/1up",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "caption": "Danky entry 4470: North Jersey Independent, Paterson, 1950-?, editor Albert E. Hart. NjPatPhi holds v.1 n.1, 18 Nov 1950.",
        "quote": "North Jersey Independent. 1950-? Frequency: Unknown. Paterson, NJ. Last issue 4 pages. Height 31 cm. Previous editor(s): Albert E. Hart. NjPatPhi v.1, n.1 Periodicals Nov 18, 1950.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 67,
        "clip_id": "danky-1998-bronze-thrills",
        "src": "q7p-danky-bronze-117.png",
        "dest_dir": DANKY,
        "dest": "danky-1998-p117-bronze-thrills.png",
        "page": "117",
        "url": "https://archive.org/details/africanamericanne00dank/page/117/mode/1up",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "caption": "Danky leftover on p.117: Bronze Thrills, confession stories, ISSN 0277-8106, OCLC 7645384, WHi holdings.",
        "quote": "ISSN 0277-8106. LC card no. sn81-3423. OCLC no. 7645384. Subject focus and/or Features: Confession stories. WHi v.17, n.1-v.18, n.12 AP/2/B7 Jan, 1968-Dec, 1969. WHi v.3, n.1; v.22, n.7 Pam 01-6104 Jan, 1955; July, 1973. DHU v.23, n.1- Periodicals Jan, 1974-.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 67,
        "clip_id": "bronze-thrills-1960-app",
        "src": "q7nopen-bronze-thrills-1960.png",
        "dest_dir": CLIPS,
        "dest": "bronze-thrills-1960-05-20-asbury-park-press.png",
        "page": "21",
        "url": "https://www.newspapers.com/image/143086953/",
        "source": "Asbury Park Press",
        "sourceCity": "Asbury Park, New Jersey",
        "date": "1960-05-20",
        "caption": "Asbury Park Press: Emily Rodriquez life story to appear in the July issue of Bronze Thrills.",
        "quote": "Miss Rodriquez, who converses in Spanish and Portuguese, recently wrote a book, based on her life entitled \"Out of Darkness to Light\" . . . It is to be published in the July issue of Bronze Thrills.",
        "kind": "clip",
        "bucket": "newspapers_com",
    },
    {
        "id": 21,
        "clip_id": "danky-1998-nite-lite",
        "src": "q7v-nite-427.png",
        "dest_dir": DANKY,
        "dest": "danky-1998-p427-nite-lite.png",
        "page": "427",
        "url": "https://archive.org/details/africanamericanne00dank/page/427/mode/1up",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "caption": "Danky leftover on p.427: Nite Lite motto \"Be in the know, on where to go.\" HU microfilm 1975-1976.",
        "quote": "Available in microform from: DHU (1975-1976). \"Be in the know, on where to go.\" Subject focus and/or Features: Newspaper. HU v.17, n.11-v.18, n.17 Microfilm Jan 23, 1975-Mar 4, 1976.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 129,
        "clip_id": "danky-1998-club-world",
        "src": "q7r-club-world-158.png",
        "dest_dir": DANKY,
        "dest": "danky-1998-p158-club-world.png",
        "page": "158",
        "url": "https://archive.org/details/africanamericanne00dank/page/158/mode/1up",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "caption": "Danky entry 1642 start: Club World: Newsmagazine, 1955?-?, frequency Bi-.",
        "quote": "1642 Club World: Newsmagazine. 1955?-? Frequency: Bi-",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 116,
        "clip_id": "danky-1998-jersey-heritage",
        "src": "q7r-jersey-camera-313.png",
        "dest_dir": DANKY,
        "dest": "danky-1998-p313-jersey-heritage.png",
        "page": "313",
        "url": "https://archive.org/details/africanamericanne00dank/page/313/mode/1up",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "caption": "Danky entry 3287: The Jersey Heritage, quarterly 1992-1996, Jersey City, editor Elizabeth Peale Johnson.",
        "quote": "The Jersey Heritage. 1992-1996. Frequency: Quarterly. Jersey City, NJ. Published by Afro-American Historical and Genealogical Society, Inc., New Jersey Chapter. Last issue 6 pages. Previous editor(s): Elizabeth Peale Johnson. OCLC no. 25846047. WHi v.2, n.1-v.9, n.7 In process May, 1994-Sept, 1996.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
]

NONE_NP = {
    18: "Theodore Hinton plus Liberator/editor/newspaper, 1948-1965. Opened Morning Call 30 Dec 1940 (Englewood bar admission list) and Record 29 July 1943 (casualty list plus a B-24 Liberator bomber). Neither names The Liberator of Paterson.",
    11: "Informer plus Paterson/Negro/colored/North Jersey returned no New Jersey cards on the first page.",
    72: "Tiny Prince plus editor/newspaper/magazine returned 0 New Jersey cards on the first page.",
    66: "Jersey Camera first-page NJ cards were 1927 Jersey Journal camera/news-photo uses and later camera-shop ads, not the 1951 Newark magazine.",
    21: "Nite Lite Newark opened Jersey Journal 6 Aug 1930; highlight was not the 1959 Newark weekly.",
    129: "Club World plus East Orange/newsmagazine opened Star-Ledger 9 Jan 1954 (Rotary Club / World War) and 17 Oct 1957 (Hiram Blauvelt / World War). Neither names the East Orange newsmagazine.",
}

FACTS = {
    30: (
        " Danky and Hady 1998 entry 4470: unknown frequency, 4 pages, editor Albert E. Hart. "
        "Passaic County Historical Society (NjPatPhi) holds v.1 n.1 dated 18 Nov 1950."
    ),
    67: (
        " Danky leftover on p.117 matches OCLC 7645384 and LC sn81-3423; subject is confession stories. "
        "WHi holds Jan 1955 and 1968-1969; DHU from Jan 1974. Asbury Park Press 20 May 1960 says "
        "Emily Rodriquez's \"Out of Darkness to Light\" was set for the July issue."
    ),
    21: (
        " Danky leftover on p.427 quotes the motto \"Be in the know, on where to go\" and records "
        "University of Hawaii microfilm v.17 n.11-v.18 n.17 (23 Jan 1975-4 Mar 1976)."
    ),
    129: (
        " Danky and Hady 1998 entry 1642 begins on p.158: Club World: Newsmagazine, 1955?-?, bi-."
    ),
    116: (
        " Danky and Hady 1998 entry 3287: quarterly 1992-1996, Jersey City, Afro-American Historical "
        "and Genealogical Society NJ Chapter; editor Elizabeth Peale Johnson; OCLC 25846047; "
        "WHi v.2 n.1-v.9 n.7 May 1994-Sept 1996."
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
        src = SHOTS / item["src"]
        dest = item["dest_dir"] / item["dest"]
        if not src.exists():
            raise SystemExit(f"missing {src}")
        dest.write_bytes(src.read_bytes())
        rel = str(dest.relative_to(ROOT)).replace("\\", "/")
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
        bucket = row["sources"][item["bucket"]]
        bucket["searched"] = True
        if not any(h.get("url") == item["url"] for h in bucket.get("hits") or []):
            bucket.setdefault("hits", []).append(hit)
        note = bucket.get("notes") or ""
        if item["caption"][:40] not in note:
            bucket["notes"] = (note + "; " + item["caption"]).strip("; ")
        if item["clip_id"] not in existing:
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
            existing.add(item["clip_id"])

    for pid, note in NONE_NP.items():
        np = rows[pid]["sources"]["newspapers_com"]
        np["searched"] = True
        old = np.get("notes") or ""
        if "q7e" not in old and note[:40] not in old:
            np["notes"] = (old + "; q7e 1950s search: " + note).strip("; ")

    for pid, extra in FACTS.items():
        pub = by_pub[pid]
        if extra[:40].strip() not in (pub.get("historicalNotes") or ""):
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
    print("clips", len(clip_doc["clips"]))


if __name__ == "__main__":
    main()
