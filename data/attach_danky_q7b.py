"""Attach Danky 1998 and HSP keepers for Citizen, Camden News, Apex News, Hiram Star-News."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "data" / "research" / "newspapers-com" / "screenshots"
DANKY = ROOT / "data" / "research" / "danky"
CAT = ROOT / "data" / "research" / "source-catalog.json"
PUBS = ROOT / "data" / "publications.json"
CLIP_CAT = ROOT / "data" / "research" / "newspapers-com" / "clips" / "catalog.json"

DANKY.mkdir(parents=True, exist_ok=True)

KEEPERS = [
    {
        "id": 45,
        "clip_id": "danky-1998-apex-news",
        "src": "q7j-danky-p46.png",
        "dest": "danky-1998-p46-apex-news.png",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "page": "46",
        "url": "https://archive.org/details/africanamericanne00dank/page/46/mode/1up",
        "caption": "Danky entry 467: Apex News, quarterly, Atlantic City, Apex Publishing Co., editor Archie J. Morgan.",
        "quote": "Apex News. 1929-? Frequency: Quarterly. Atlantic City, NJ. Published by Apex Publishing Co. Last issue 45 pages. Height 28 cm. Previous editor(s): Archie J. Morgan. DHU holdings include Aug/Sept and Nov 1929 through Jan 1940. TNF holds Sept 1937, Jan-June 1938, June 1939.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 3,
        "clip_id": "danky-1998-camden-news",
        "src": "q7m-danky-camden-131.png",
        "dest": "danky-1998-p131-camden-news.png",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "page": "131",
        "url": "https://archive.org/details/africanamericanne00dank/page/131/mode/1up",
        "caption": "Danky entry 1354: The Camden News, weekly, Camden News Publishing Co., editor C. N. Green.",
        "quote": "The Camden News. 1915-? Frequency: Weekly. Camden, NJ. Published by Camden News Publishing Co. Previous editor(s): C. N. Green. NjCaHi v.1, n.3, 8, 28; v.2, n.50 Periodicals May 22, June 26, Dec 11, 1915; Mar 9, 1918.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 79,
        "clip_id": "danky-1998-hiram-star-news",
        "src": "q7m-danky-hiram-277.png",
        "dest": "danky-1998-p277-hiram-star-news.png",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "page": "277",
        "url": "https://archive.org/details/africanamericanne00dank/page/277/mode/1up",
        "caption": "Danky entry 2907: The Hiram Star-News, biweekly, Vauxhall, editor Ada Smith. Howard holds 1951 issues.",
        "quote": "The Hiram Star-News. 1947?-? Frequency: Biweekly. Vauxhall, NJ. Published by Hiram Star-News Publishing Co. Last issue 4 pages. Previous editor(s): Ada Smith. Subject focus: Community newsletter, King Hiram's Craftsmen Center (Vauxhall, NJ). DHU v.5, n.11-13, 15-16, 18 Periodicals July 12-36; Aug 16-23, Oct 18, 1951.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 7,
        "clip_id": "danky-1998-citizen",
        "src": "q7m-danky-citizen-154.png",
        "dest": "danky-1998-p154-the-citizen.png",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "sourceCity": "Cambridge, Massachusetts",
        "date": "1998",
        "page": "154",
        "url": "https://archive.org/details/africanamericanne00dank/page/154/mode/1up",
        "caption": "Danky entry that ends on p.154: editor Henry J. Auston, OCLC 38227497; WHi holds v.1 n.16, 12 Mar 1909.",
        "quote": "Previous editor(s): Henry J. Auston. OCLC no. 38227497. Subject focus and/or Features: Newspaper. WHi v.1, n.16 Pam 01-6658 Mar 12, 1909.",
        "kind": "catalog_record",
        "bucket": "internet_archive",
    },
    {
        "id": 7,
        "clip_id": "hsp-citizen-9-witherspoon",
        "src": "q7n-hsp-citizen-tour.png",
        "dest": "hsp-citizen-9-witherspoon.png",
        "source": "Historical Society of Princeton",
        "sourceCity": "Princeton, New Jersey",
        "date": None,
        "page": "40",
        "url": "https://www.princetonhistory.org/tour/40.html",
        "caption": "HSP walking tour stop 40: The Citizen published at 9 Witherspoon by W.H. de Paur, Henry J. Auston editor.",
        "quote": "9 Witherspoon is the address of the publisher of The Citizen, a newspaper dedicated to the moral, intellectual, and industrial improvement of the Negro race. W.H. de Paur published the paper, with Henry J. Auston as editor.",
        "kind": "library_page",
        "bucket": "other",
    },
]

LIB_NOTE = (
    "NPL newarkafamnewspapers, Rutgers Newark Black Newspapers, and NJ State Library "
    "Ironsides page do not list this title. Red Bank Echo page returned 404. "
    "Danky and Hady 1998 does list it."
)
CA_NOTE = (
    "No LCCN in the publication record. Chronicling America title JSON returned HTTP 403."
)
IA_NOTE = {
    7: "Danky and Hady 1998, printed p.154: Henry J. Auston, OCLC 38227497; Wisconsin Historical Society holds v.1 n.16 dated 12 Mar 1909.",
    3: "Danky and Hady 1998, printed p.131 entry 1354. Camden County Historical Society (NjCaHi) holds 22 May, 26 June, 11 Dec 1915 and 9 Mar 1918.",
    45: "Danky and Hady 1998, printed p.46 entry 467. Howard (DHU) holds 1929-1940 issues; Fisk (TNF) holds 1937-1939.",
    79: "Danky and Hady 1998, printed p.277 entry 2907. Howard (DHU) holds v.5 numbers from July-Oct 1951. Editor Ada Smith.",
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}
    clip_doc = json.loads(CLIP_CAT.read_text(encoding="utf-8"))
    existing_clip_ids = {c["id"] for c in clip_doc["clips"]}

    for item in KEEPERS:
        src = SHOTS / item["src"]
        dest = DANKY / item["dest"]
        if not src.exists():
            raise SystemExit(f"missing screenshot {src}")
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
        if item["clip_id"] not in existing_clip_ids:
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
            existing_clip_ids.add(item["clip_id"])

    for pid, note in IA_NOTE.items():
        row = rows[pid]
        ia = row["sources"]["internet_archive"]
        ia["searched"] = True
        old = ia.get("notes") or ""
        if "Danky and Hady 1998" not in old:
            ia["notes"] = (old + "; " + note).strip("; ")
        other = row["sources"]["other"]
        other["searched"] = True
        oold = other.get("notes") or ""
        if "Danky and Hady 1998" not in oold:
            other["notes"] = (oold + "; " + LIB_NOTE).strip("; ")
        ca = row["sources"]["chronicling_america"]
        ca["searched"] = True
        if "HTTP 403" not in (ca.get("notes") or ""):
            ca["notes"] = ((ca.get("notes") or "") + "; " + CA_NOTE).strip("; ")

    cit = by_pub[7]
    cit["publishers"] = "W.H. de Paur"
    cit["archiveUrl"] = "OCLC no. 38227497; WHi v.1 n.16 (12 Mar 1909)"
    extra = (
        " Historical Society of Princeton walking tour (stop 40) places the publisher "
        "at 9 Witherspoon and spells the name W.H. de Paur, with Henry J. Auston as editor. "
        "Danky and Hady 1998 records OCLC 38227497 and a Wisconsin Historical Society holding "
        "of v.1, n.16 dated 12 March 1909 (Pam 01-6658)."
    )
    if "9 Witherspoon" not in (cit.get("historicalNotes") or ""):
        cit["historicalNotes"] = (cit.get("historicalNotes") or "") + extra

    cam = by_pub[3]
    extra = (
        " Danky and Hady 1998 entry 1354: weekly published by Camden News Publishing Co.; "
        "editor C. N. Green. Camden County Historical Society (NjCaHi) holds v.1 n.3, 8, 28 "
        "and v.2 n.50: 22 May, 26 June, 11 Dec 1915 and 9 Mar 1918."
    )
    if "NjCaHi" not in (cam.get("historicalNotes") or ""):
        cam["historicalNotes"] = (cam.get("historicalNotes") or "") + extra
    cam["archiveUrl"] = "Camden County Historical Society (NjCaHi): May 22, June 26, Dec 11, 1915; Mar 9, 1918"

    apex = by_pub[45]
    extra = (
        " Danky and Hady 1998 entry 467: quarterly, 45-page last issue examined, editor Archie J. Morgan. "
        "Howard University (DHU) holds v.1 n.1 and 11 (Aug/Sept and Nov 1929) through Jan 1940. "
        "Fisk (TNF) holds Sept 1937, Jan-June 1938, and June 1939."
    )
    if "entry 467" not in (apex.get("historicalNotes") or ""):
        apex["historicalNotes"] = (apex.get("historicalNotes") or "") + extra

    hir = by_pub[79]
    hir["keyStaff"] = "Previous editor(s): Ada Smith."
    extra = (
        " Danky and Hady 1998 entry 2907: biweekly, 4 pages, King Hiram's Craftsmen Center. "
        "Editor Ada Smith. Howard University (DHU) holds v.5 n.11-13, 15-16, 18: "
        "12-36 July, 16-23 Aug, and 18 Oct 1951."
    )
    if "Ada Smith" not in (hir.get("historicalNotes") or ""):
        hir["historicalNotes"] = (hir.get("historicalNotes") or "") + extra

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
