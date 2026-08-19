"""Attach verified q7 NJ keepers and write new facts into publication notes."""

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
        "id": 34,
        "clip_id": "landscape-1987-ridgewood-news",
        "src": "q7bopen-smith-newspaper.png",
        "dest": "landscape-1987-11-26-ridgewood-news-ap-smith.png",
        "source": "The Ridgewood News",
        "sourceCity": "Ridgewood, New Jersey",
        "date": "1987-11-26",
        "page": "14",
        "url": "https://www.newspapers.com/image/1122504536/",
        "caption": "Tom Brady on Alfred P. Smith: The Landscape, first as A.P. Smith's Paper, printed at East Allendale Road from May 1881 until July 1901.",
        "quote": "Alfred P. Smith served as The Landscape's editor, reporter, publisher, printer, translator, circulation and advertising managers. Originally distributed under the banner of A.P. Smith's Paper... from May of 1881 until July of 1901.",
        "kind": "clip",
    },
    {
        "id": 34,
        "clip_id": "landscape-1991-record",
        "src": "q7more-landscape-1991-record.png",
        "dest": "landscape-1991-02-09-the-record-civil-rights.png",
        "source": "The Record",
        "sourceCity": "Hackensack, New Jersey",
        "date": "1991-02-09",
        "page": "2",
        "url": "https://www.newspapers.com/image/496517756/",
        "caption": "Second Look: Writer shaped civil-rights Landscape. Alfred P. Smith started A. P. Smith's Paper in 1881, then renamed it The Landscape.",
        "quote": "In 1881, Smith, a former reporter who owned a job-printing business, started a monthly newspaper first called \"A. P. Smith's Paper\" and then renamed \"The Landscape.\" Most of Smith's subscribers were white.",
        "kind": "clip",
    },
    {
        "id": 34,
        "clip_id": "landscape-1993-sunday-news",
        "src": "q7more-landscape-1993-sunday-news.png",
        "dest": "landscape-1993-06-27-sunday-news-smallest.png",
        "source": "The Sunday News",
        "sourceCity": "Ridgewood, New Jersey",
        "date": "1993-06-27",
        "page": "2",
        "url": "https://www.newspapers.com/image/634766635/",
        "caption": "Nancy R. Peck: Alfred P. Smith printed what was called the nation's smallest newspaper from an old house overlooking the Saddle River valley.",
        "quote": "By himself and out of an old house overlooking the Saddle River valley, Alfred P. Smith edited and printed what was purportedly the nation's smallest newspaper. Its four pages of newsprint paper measured 6 x 8 inches.",
        "kind": "clip",
    },
    {
        "id": 37,
        "clip_id": "guardian-1939-paterson-news",
        "src": "q7open-guardian-1939.png",
        "dest": "guardian-1939-09-09-paterson-news-journal.png",
        "source": "The News",
        "sourceCity": "Paterson, New Jersey",
        "date": "1939-09-09",
        "page": "9",
        "url": "https://www.newspapers.com/image/525697398/",
        "caption": "Paterson News cites The New Jersey Guardian as a journal for colored readers with state-wide circulation.",
        "quote": "in an article just published in The New Jersey Guardian, a journal for colored readers which has state-wide circulation.",
        "kind": "clip",
    },
    {
        "id": 2,
        "clip_id": "jersey-express-1949-star-ledger",
        "src": "q7more-johnson-1949-ledger.png",
        "dest": "jersey-express-1949-01-19-star-ledger-johnson.png",
        "source": "The Star-Ledger",
        "sourceCity": "Newark, New Jersey",
        "date": "1949-01-19",
        "page": "14",
        "url": "https://www.newspapers.com/image/1108232407/",
        "caption": "Melvin B. Johnson named as former Negro newspaper publisher and editor, in the field until 1946.",
        "quote": "Another prospective commission candidate is Melvin B. Johnson of 55 Somerset st., former Negro newspaper publisher and editor. Johnson was in the newspaper field until 1946, when he left to work among Negro voters in Gov. Driscoll's gubernatorial campaign.",
        "kind": "clip",
    },
    {
        "id": 2,
        "clip_id": "jersey-express-1949-app",
        "src": "q7more-johnson-1949-app.png",
        "dest": "jersey-express-1949-11-06-asbury-park-press-johnson.png",
        "source": "Asbury Park Press",
        "sourceCity": "Asbury Park, New Jersey",
        "date": "1949-11-06",
        "page": "2",
        "url": "https://www.newspapers.com/image/143065742/",
        "caption": "Photo cutline: Melvin B. Johnson, former editor and publisher of weekly newspapers at Montclair and Newark.",
        "quote": "Johnson, a former editor and publisher of weekly newspapers at Montclair and Newark, is employed by the migrant labor division of the New Jersey Department of labor and industry.",
        "kind": "clip",
    },
]

NONE_NOTES = {
    7: "Founder searches (Du Paur / Henry J. Auston) with 1905-1925 dates produced no New Jersey card that names The Citizen of Princeton. Opened Auston hits were 1942-1946 and a different person.",
    3: "Quoted Camden News plus colored/negro/C. N. Green, 1914-1922. Opened Courier-Post 1907 and 1917 pages were generic Camden/News word hits, not the Black weekly.",
    57: '"Ironsides Echo" returned 138 matches and 0 New Jersey cards on the first page.',
    45: "Apex News plus Atlantic City/Morgan/colored, 1928-1942 and a later exact search. Opened Press of Atlantic City pages were radio listings or 1958 Apex beauty ads, not the 1929-1940 newspaper.",
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
        dest = CLIPS / item["dest"]
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
        np = row["sources"]["newspapers_com"]
        np["searched"] = True
        if not any(h.get("url") == item["url"] for h in np.get("hits") or []):
            np.setdefault("hits", []).append(hit)
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

    for pid, note in NONE_NOTES.items():
        np = rows[pid]["sources"]["newspapers_com"]
        np["searched"] = True
        old = np.get("notes") or ""
        if "q7 founder" not in old and note[:40] not in old:
            np["notes"] = (old + "; q7 founder-name search: " + note).strip("; ")

    # Publication facts
    land = by_pub[34]
    land["yearFounded"] = 1881
    land["alternateName"] = "A. P. Smith's Paper"
    land["publishers"] = "Alfred P. Smith"
    land["keyStaff"] = "Editor, printer, publisher: Alfred P. Smith (1832–1901)"
    extra = (
        " Ridgewood News 26 Nov 1987 (Tom Brady) and The Record 9 Feb 1991 confirm "
        "the first title was A. P. Smith's Paper, renamed The Landscape; printed May 1881–July 1901 "
        "at East Allendale Road; most subscribers were white; Smith was a former Paterson Guardian "
        "reporter who in 1862 wrote Lincoln against colonizing freed people. Sunday News 27 June 1993 "
        "called it the nation's smallest newspaper (four pages, 6 x 8 inches)."
    )
    if "Ridgewood News 26 Nov 1987" not in (land.get("historicalNotes") or ""):
        land["historicalNotes"] = (land.get("historicalNotes") or "") + extra

    je = by_pub[2]
    je["historicalNotes"] = (
        "Montclair weekly edited and published by Melvin B. Johnson (Rumble Printing Service). "
        "Asbury Park Press 6 Nov 1949 calls him a former editor and publisher of weekly newspapers "
        "at Montclair and Newark. Star-Ledger 19 Jan 1949 says the former Negro newspaper publisher "
        "and editor left the newspaper field in 1946 for Gov. Driscoll's campaign, then the N.J. "
        "Department of Labor. Montclair Times 20 Oct 1931 prints a letter from Johnson as publicity "
        "chairman of the Citizens' Union of Montclair, one year before the paper's listed founding."
    )

    g = by_pub[37]
    add = (
        " Paterson News 9 Sept 1939 cites The New Jersey Guardian as \"a journal for colored readers "
        "which has state-wide circulation.\""
    )
    if "Paterson News 9 Sept 1939" not in (g.get("historicalNotes") or ""):
        g["historicalNotes"] = (g.get("historicalNotes") or "") + add

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
