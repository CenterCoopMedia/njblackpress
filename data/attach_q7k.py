"""Attach q7k keepers: BCALA Danky, Forum/Essex LOC, South Jersey Journal site."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DANKY = DATA / "research" / "danky"
LOC = DATA / "research" / "loc"
SITES = DATA / "research" / "sites"
SHOTS = DATA / "research" / "newspapers-com" / "screenshots"
CAT = DATA / "research" / "source-catalog.json"
PUBS = DATA / "publications.json"
CLIP_CAT = DATA / "research" / "newspapers-com" / "clips" / "catalog.json"

LOC.mkdir(parents=True, exist_ok=True)
SITES.mkdir(parents=True, exist_ok=True)

KEEPERS = [
    {
        "id": 99,
        "clip_id": "danky-1998-bcala",
        "src": DANKY / "danky-leaf-p77-n120-bcala-77.jpg",
        "dest": DANKY / "danky-1998-p77-bcala.jpg",
        "page": "77",
        "url": "https://archive.org/details/africanamericanne00dank/page/77/mode/1up",
        "source": "Danky and Hady, African-American Newspapers and Periodicals",
        "date": "1998",
        "kind": "catalog_record",
        "source_paper": "Danky and Hady 1998",
        "source_city": "Cambridge, Massachusetts",
        "caption": "Danky entry 795: Black Caucus of ALA Newsletter, bimonthly 1971-. Place of publication Pomona, NJ, Sept 1983-Apr 1986. WHi Sept 1983-.",
        "quote": "Black Caucus of ALA Newsletter. 1971-. Frequency: Bimonthly. George C. Grant, Editor. Published by American Library Association Black Caucus. Variant title(s): Black Caucus Newsletter, BCALA News. Place of publication varies: Baltimore, MD, 1978-1983; Pomona, NJ, [Sept 1983]-Apr 1986. ISSN 8755-9277. OCLC no. 8092782, 23133363. WHi v.9, n.1- Microforms Sept, 1983-. DHU [v.2, n.1-] Periodicals [Dec 1973- ]. NN-Sc [v.8, n.4- ] Newsletters Feb, 1986.",
    },
    {
        "id": 39,
        "clip_id": "loc-forum-sn88071371",
        "src": SHOTS / "forum-loc-sn88071371.png",
        "dest": LOC / "forum-loc-sn88071371.png",
        "page": None,
        "url": "https://www.loc.gov/item/sn88071371/",
        "source": "Library of Congress Directory of U.S. Newspapers",
        "date": "1974-01-04",
        "kind": "catalog_record",
        "source_paper": "Library of Congress",
        "source_city": "Washington, D.C.",
        "caption": "LOC directory: The Forum (Newark, N.J.) 197?-????. Forum Publications. Serving the New Jersey black community. Description based on Vol. 2, no. 47 (Jan. 4, 1974). LCCN sn88071371. OCLC 18514783.",
        "quote": "The Forum (Newark, N.J.) 197?-????. Created/Published Newark, N.J.: Forum Publications. Notes: Biweekly. Serving the New Jersey black community. Description based on: Vol. 2, no. 47 (Jan. 4, 1974). LCCN sn88071371. OCLC 18514783.",
    },
    {
        "id": 42,
        "clip_id": "loc-essex-forum-sn88071370",
        "src": SHOTS / "essex-forum-loc-sn88071370.png",
        "dest": LOC / "essex-forum-loc-sn88071370.png",
        "page": None,
        "url": "https://www.loc.gov/item/sn88071370/",
        "source": "Library of Congress Directory of U.S. Newspapers",
        "date": "1972-06-29",
        "kind": "catalog_record",
        "source_paper": "Library of Congress",
        "source_city": "Washington, D.C.",
        "caption": "LOC directory: Essex Forum (East Orange, N.J.) 1972-????. Multi-Linear Publications. Vol. 1, no. 1 (June 29, 1972). Weekly serving Orange, Montclair and E. Orange; later biweekly Metropolitan Essex County. LCCN sn88071370. OCLC 18514779.",
        "quote": "Essex Forum (East Orange, N.J.) 1972-????. Created/Published East Orange, N.J.: Multi-Linear Publications, 1972-. Notes: Biweekly. Vol. 1, no. 1 (June 29, 1972). A weekly newspaper serving Orange, Montclair and E. Orange. A biweekly newspaper serving Metropolitan Essex County. Black newspaper. LCCN sn88071370. OCLC 18514779.",
    },
    {
        "id": 8,
        "clip_id": "sjj-wordpress-about",
        "src": SHOTS / "south-jersey-journal-about.png",
        "dest": SITES / "south-jersey-journal-about.png",
        "page": None,
        "url": "https://southjerseyjournal.wordpress.com/south-jersey-journal/",
        "source": "South Jersey Journal WordPress",
        "date": "2026-08-17",
        "kind": "website_screenshot",
        "source_paper": "South Jersey Journal",
        "source_city": "Mullica Hill, New Jersey",
        "caption": "South Jersey Journal about page: monthly, South Jersey Communications LLC, 157 Bridgeton Pike, Mullica Hill. Publisher Al Thomas. Editor Clyde Hughes.",
        "quote": "South Jersey Journal is a monthly publication dedicated to covering news and information relevant to the African-American communities of Southern New Jersey. Owned by South Jersey Communications, LLC. Mail Letters to: 157 Bridgeton Pike, Suite 200-345, Mullica Hill, NJ 08062. President & Publisher Al Thomas. Editor-in-Chief Clyde Hughes.",
    },
]

EXTRAS = {
    99: " Danky 1998 entry 795: bimonthly 1971-, American Library Association Black Caucus, editor George C. Grant. Place of publication Pomona, NJ, Sept 1983-Apr 1986 (also Baltimore 1978-1983). ISSN 8755-9277. OCLC 8092782, 23133363. WHi from Sept 1983. DHU from Dec 1973. NN-Sc from Feb 1986.",
    39: " LOC Directory of U.S. Newspapers: The Forum (Newark, N.J.) 197?-????, Forum Publications. Motto Serving the New Jersey black community. Description based on Vol. 2, no. 47 (Jan. 4, 1974). LCCN sn88071371. OCLC 18514783. Danky 1998 has no Forum Newark entry.",
    42: " LOC Directory of U.S. Newspapers: Essex Forum (East Orange, N.J.) 1972-????, Multi-Linear Publications. Vol. 1, no. 1 (June 29, 1972). First described as a weekly serving Orange, Montclair and E. Orange; later a biweekly serving Metropolitan Essex County. LCCN sn88071370. OCLC 18514779. Danky 1998 has no Essex Forum entry.",
    8: " Publisher site 2026: monthly, South Jersey Communications LLC, 157 Bridgeton Pike Suite 200-345, Mullica Hill, NJ 08062. President and publisher Al Thomas. Editor-in-chief Clyde Hughes. General manager Katanya Simmons.",
}

NONE_NOTES = {
    14: "Danky 1998 African-American Newspapers and Periodicals has no Newark title New Jersey Record. The Record entries are Birmingham and other out-of-state papers. No digitized issue or library catalog record for a Newark African American newspaper under this name.",
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}
    clip_doc = json.loads(CLIP_CAT.read_text(encoding="utf-8"))
    existing = {c["id"] for c in clip_doc["clips"]}

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
        if item["id"] == 99:
            src_key = "internet_archive"
        elif item["id"] == 8:
            src_key = "other"
        else:
            src_key = "other"
        src = row["sources"][src_key]
        src["searched"] = True
        if not any(h.get("url") == item["url"] for h in src.get("hits") or []):
            src.setdefault("hits", []).append(hit)
        if item["caption"][:40] not in (src.get("notes") or ""):
            src["notes"] = ((src.get("notes") or "") + "; " + item["caption"]).strip("; ")
        if item["clip_id"] not in existing:
            clip_doc["clips"].append(
                {
                    "id": item["clip_id"],
                    "about": row["name"],
                    "aboutId": item["id"],
                    "sourcePaper": item["source_paper"],
                    "sourceCity": item["source_city"],
                    "date": item["date"],
                    "page": item["page"],
                    "url": item["url"],
                    "localImage": item["dest"].name,
                    "quote": item["quote"],
                    "why": item["caption"],
                }
            )
            existing.add(item["clip_id"])

    for pid, extra in EXTRAS.items():
        pub = by_pub[pid]
        if extra[12:40] not in (pub.get("historicalNotes") or ""):
            pub["historicalNotes"] = (pub.get("historicalNotes") or "") + extra

    for pid, note in NONE_NOTES.items():
        row = rows[pid]
        other = row["sources"]["other"]
        other["searched"] = True
        if note[:40] not in (other.get("notes") or ""):
            other["notes"] = ((other.get("notes") or "") + " " + note).strip()
        ia = row["sources"]["internet_archive"]
        if note[:40] not in (ia.get("notes") or ""):
            ia["notes"] = ((ia.get("notes") or "") + "; " + note).strip("; ")

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
    print("attached", [item["id"] for item in KEEPERS])
    none = [r["id"] for r in rows.values() if r["status"] == "searched_none"]
    print("still_none", none)


if __name__ == "__main__":
    main()
