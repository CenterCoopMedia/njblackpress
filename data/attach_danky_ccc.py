"""Attach Danky 1998 keepers for remaining NJ CCC camp papers."""

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
        "id": 48,
        "clip_id": "danky-1998-ash-can",
        "src": "q7t-ash-51.png",
        "dest": "danky-1998-p51-ash-can.png",
        "page": "51",
        "url": "https://archive.org/details/africanamericanne00dank/page/51/mode/1up",
        "caption": "Danky entry 517 leftover: Ash Can editor Bertram Totten, superseded by Penn Crusader; WHi May-June 1935.",
        "quote": "Previous editor(s): Bertram Totten. Superseded by: Penn Crusader. Available in microform from: CRL (1935). OCLC no. 29252904. Subject focus: Civilian Conservation Corps. WHi v.1, n.24-25 Microforms May 16-June, 1935.",
    },
    {
        "id": 136,
        "clip_id": "danky-1998-penn-crusader",
        "src": "q7t-penn-457.png",
        "dest": "danky-1998-p457-penn-crusader.png",
        "page": "457",
        "url": "https://archive.org/details/africanamericanne00dank/page/457/mode/1up",
        "caption": "Danky entry 4764: Penn Crusader, monthly 1936-1940, Chatsworth, Company 1284-C, supersedes Ash Can.",
        "quote": "Penn Crusader. 1936-1940. Frequency: Monthly. Chatsworth, NJ. Published by Civilian Conservation Corps, Company 1284-C. Last issue 13 pages. Previous editor(s): R. Johnson, Nov-Dec 1936; Martin Murray, Feb-Apr 1937; R. Lowe, June 1937; Sylvester Moore, July & Nov 1937; J. W. Brown, Sept-Oct 1937 & Feb-Mar 1938; R. Davis, Apr 1938; James W. Richardson, May 1938-Feb 1939. Supersedes: Ash Can. CRL (1936-1940). OCLC no. 29252764.",
    },
    {
        "id": 97,
        "clip_id": "danky-1998-rifle-ranger",
        "src": "q7q-rifle-search.png",
        "dest": "danky-1998-p493-rifle-ranger.png",
        "page": "493",
        "url": "https://archive.org/details/africanamericanne00dank/page/493/mode/1up",
        "caption": "Danky entry 5148: Rifle Ranger, Fort Dix, Company 3263-C, 8 pages, superseded by Star-gazer.",
        "quote": "Rifle Ranger. 1938-1938. Frequency: Unknown. Fort Dix, NJ. Published by Civilian Conservation Corps, Company 3263-C. Last issue 8 pages. Line drawings. Superseded by: Star-gazer. Available in microform from: CRL (1938). WHi v.1, n.2 Microforms Jan 31, 1938.",
    },
    {
        "id": 94,
        "clip_id": "danky-1998-dias-creek",
        "src": "q7p-dias-creek.png",
        "dest": "danky-1998-p194-dias-creek-echo.png",
        "page": "194-195",
        "url": "https://archive.org/details/africanamericanne00dank/page/194/mode/1up",
        "caption": "Danky entry 2023: Dias Creek Echo, monthly 1938, Cape May Courthouse, Company 1275-C, editor Robert Toomer.",
        "quote": "Dias Creek Echo. 1938-1938. Frequency: Monthly. Cape May Courthouse, NJ. Published by Civilian Conservation Corps, Company 1275-C. Last issue 15 pages. Previous editor(s): Robert Toomer. Supersedes: Point Breeze Rugcuttings. Superseded by: Little Ease Echo. CRL (1938). OCLC no. 29355552. WHi v.1, n.1-4 Microforms June-Sept, 1938.",
    },
    {
        "id": 90,
        "clip_id": "danky-1998-little-ease",
        "src": "q7s-ease-sidebar.png",
        "dest": "danky-1998-p344-little-ease-echo.png",
        "page": "344",
        "url": "https://archive.org/details/africanamericanne00dank/page/344/mode/1up",
        "caption": "Danky entry 3604: The Little Ease Echo, monthly 1938-1939, Glassboro, Company 1275-C.",
        "quote": "The Little Ease Echo. 1938-1939. Frequency: Monthly. Glassboro, NJ. Published by Civilian Conservation Corps, Company 1275-C. Last issue 7 pages. Previous editor(s): Robert Toomer, Dec 1938-June 1939; Joseph Moore, July 1939; Timothy Fenner, Aug-Sept 1939. Supersedes: Dias Creek Echo. CRL (1938-1939). OCLC no. 29355449.",
    },
    {
        "id": 55,
        "clip_id": "danky-1998-rugcuttings",
        "src": "q7s-rug-sidebar.png",
        "dest": "danky-1998-p467-point-breeze-rugcuttings.png",
        "page": "467",
        "url": "https://archive.org/details/africanamericanne00dank/page/467/mode/1up",
        "caption": "Danky entry 4862: Point Breeze Rugcuttings, monthly 1938, Cape May Courthouse, editor George Butler.",
        "quote": "Point Breeze Rugcuttings. 1938-1938. Frequency: Monthly. Cape May Courthouse, NJ. Published by Civilian Conservation Corps, Company 1275-C. Last issue 17 pages. Previous editor(s): George Butler. Superseded by: Dias Creek Echo. CRL (1938).",
    },
    {
        "id": 89,
        "clip_id": "danky-1998-sixty-niner",
        "src": "q7s-sixty-sidebar.png",
        "dest": "danky-1998-p518-sixty-niner.png",
        "page": "518",
        "url": "https://archive.org/details/africanamericanne00dank/page/518/mode/1up",
        "caption": "Danky entry 5411: Sixty Niner, monthly 1936-1941?, New Lisbon, Company 235.",
        "quote": "Sixty Niner. 1936-1941? Frequency: Monthly. New Lisbon, NJ. Published by Civilian Conservation Corps, Company 235. Last issue 10 pages. Previous editor(s): Philip Brown, Oct 1936; Roy Calloway, May 1937; Carl Boyd, Dec 1938; James Roberson, Nov 1940-Feb 1941. Variant title(s): Fighting 35 News, Flash. CRL (1936-1937). OCLC no. 30066660.",
    },
    {
        "id": 137,
        "clip_id": "danky-1998-pine-needle",
        "src": "q7r-pine-lisbon.png",
        "dest": "danky-1998-p464-pine-needle.png",
        "page": "464",
        "url": "https://archive.org/details/africanamericanne00dank/page/464/mode/1up",
        "caption": "Danky entry 4839: Pine Needle, monthly 1936-1940?, New Lisbon, Company 0237-C.",
        "quote": "Pine Needle. 1936-1940? Frequency: Monthly. New Lisbon, NJ. Published by Civilian Conservation Corps, Company 0237-C. Last issue 12 pages. Previous editor(s): Charles E. Browne, Oct 31-Dec 15 1935; Arvin Cooper, Jan 20 1936; Theodore Greene, Feb 26-June 30 1936; Milledge Cato, Feb-Aug 1937; Marvello Gilbert, Jan-Apr 1938, May-Aug 1939, Jan 1940.",
    },
]

FACTS = {
    48: (
        " Danky and Hady 1998 entry 517: monthly, Chatsworth NJ, Company 1284-C, last issue 2 pages; "
        "editor Bertram Totten; superseded by Penn Crusader; CRL 1935; OCLC 29252904; "
        "WHi v.1 n.24-25 (16 May-June 1935)."
    ),
    136: (
        " Danky and Hady 1998 entry 4764: monthly 1936-1940, Chatsworth, Company 1284-C, 13 pages; "
        "supersedes Ash Can; CRL 1936-1940; OCLC 29252764; WHi holdings Nov 1936-July 1940."
    ),
    97: (
        " Danky and Hady 1998 entry 5148: Fort Dix, Company 3263-C, 8 pages; superseded by Star-gazer; "
        "CRL 1938; WHi v.1 n.2 (31 Jan 1938)."
    ),
    94: (
        " Danky and Hady 1998 entry 2023: monthly 1938, Cape May Courthouse, Company 1275-C, 15 pages; "
        "editor Robert Toomer; supersedes Point Breeze Rugcuttings; superseded by Little Ease Echo; "
        "CRL 1938; OCLC 29355552; WHi v.1 n.1-4 June-Sept 1938."
    ),
    90: (
        " Danky and Hady 1998 entry 3604: monthly 1938-1939, Glassboro, Company 1275-C, 7 pages; "
        "editors Robert Toomer, Joseph Moore, Timothy Fenner; supersedes Dias Creek Echo; "
        "CRL 1938-1939; OCLC 29355449."
    ),
    55: (
        " Danky and Hady 1998 entry 4862: monthly 1938, Cape May Courthouse, Company 1275-C, 17 pages; "
        "editor George Butler; superseded by Dias Creek Echo; CRL 1938."
    ),
    89: (
        " Danky and Hady 1998 entry 5411: monthly 1936-1941?, New Lisbon, Company 235, 10 pages; "
        "variant titles Fighting 35 News and Flash; CRL 1936-1937; OCLC 30066660."
    ),
    137: (
        " Danky and Hady 1998 entry 4839: monthly 1936-1940?, New Lisbon, Company 0237-C, 12 pages."
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
        note = ia.get("notes") or ""
        if "Danky and Hady 1998" not in note:
            ia["notes"] = (note + "; " + item["caption"]).strip("; ")
        other = row["sources"]["other"]
        other["searched"] = True
        onote = other.get("notes") or ""
        if "Danky and Hady 1998" not in onote:
            other["notes"] = (
                onote
                + "; NPL/Rutgers/NJSL/Red Bank pages do not list this CCC title. Danky and Hady 1998 does."
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
        if f"entry {extra.split('entry ')[1][:4]}" not in (pub.get("historicalNotes") or ""):
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
