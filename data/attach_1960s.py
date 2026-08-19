"""Attach verified 1960s Danky pages and the Utimme Times clips."""

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
        "id": 62,
        "clip_id": "danky-festival-arts",
        "src": DANKY / "danky-1998-p24-festival.jpg",
        "dest": DANKY / "danky-1998-p24-festival-arts.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "24",
        "url": "https://archive.org/details/africanamericanne00dank/page/24/mode/1up",
        "caption": "Danky entry 243: Afro-American Festival of the Arts Magazine, Newark, 1966?-?, Yusef Iman. WHi Aug 1966 Pam 01-6116.",
        "quote": "243 Afro-American Festival of the Arts Magazine. 1966?-? Newark, NJ. Published by Yusef Iman. WHi Aug, 1966 Pam 01-6116.",
    },
    {
        "id": 28,
        "clip_id": "danky-black-new-ark",
        "src": DANKY / "danky-1998-p91-blacknewark.jpg",
        "dest": DANKY / "danky-1998-p91-black-new-ark.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "91",
        "url": "https://archive.org/details/africanamericanne00dank/page/91/mode/1up",
        "caption": "Danky entry 934: Black New Ark, monthly, Newark, 1968-?. Motto The Voice of New Ark's Inner City. WHi microfilm 1968-1974.",
        "quote": "934 Black New Ark. 1968-? Frequency: Monthly. Newark, NJ. Variant title(s): Black News.",
    },
    {
        "id": 69,
        "clip_id": "danky-cricket",
        "src": DANKY / "danky-1998-p179-cricket.jpg",
        "dest": DANKY / "danky-1998-p179-cricket.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "179",
        "url": "https://archive.org/details/africanamericanne00dank/page/179/mode/1up",
        "caption": "Danky entry 1867: The Cricket: Black Music in Evolution, Newark, 1969, Jihad Publications. Editors Le Roi Jones, Amamu Baraka, Larry Neal, A. B. Spellman. WHi n.1-3.",
        "quote": "1867 The Cricket: Black Music in Evolution. 1969-1969. Newark, NJ. Published by Jihad Publications.",
    },
    {
        "id": 70,
        "clip_id": "danky-deliverance-voice",
        "src": DANKY / "danky-leaf-p191-n233-deliverance-guess2.jpg",
        "dest": DANKY / "danky-1998-p190-deliverance-voice.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "190",
        "url": "https://archive.org/details/africanamericanne00dank/page/190/mode/1up",
        "caption": "Danky entry 1978: Deliverance Voice, Newark, 1967?-?, Deliverance Publishing House, editor Ralph Michel. IC-CW July/Aug 1978.",
        "quote": "1978 Deliverance Voice. 1967?-? Newark, NJ. Published by Deliverance Publishing House. Previous editor(s): Ralph Michel.",
    },
    {
        "id": 133,
        "clip_id": "danky-freedom-reports",
        "src": DANKY / "danky-1998-p240-freedom.jpg",
        "dest": DANKY / "danky-1998-p240-freedom-reports.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "240",
        "url": "https://archive.org/details/africanamericanne00dank/page/240/mode/1up",
        "caption": "Danky entry 2512: Freedom Reports, monthly, Newark, United Committee for Political Freedom. WHi Feb, Mar 1966 Pam 84-3848.",
        "quote": "2512 Freedom Reports. 1966?-? Frequency: Monthly. Newark, NJ. Published by United Committee for Political Freedom.",
    },
    {
        "id": 76,
        "clip_id": "danky-ncup",
        "src": DANKY / "danky-leaf-p418-n460-ncup-entry.jpg",
        "dest": DANKY / "danky-1998-p417-ncup.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "417",
        "url": "https://archive.org/details/africanamericanne00dank/page/417/mode/1up",
        "caption": "Danky entry 4335: Newark Community Union Project News, irregular, Newark, 1963?-1965?, housing. WHi 1962-1965 Pam 1719.",
        "quote": "4335 Newark Community Union Project News. 1963?-1965? Frequency: Irregular. Newark, NJ. Subject focus: Housing.",
    },
    {
        "id": 73,
        "clip_id": "danky-utimme",
        "src": DANKY / "danky-1998-p587-utimme.jpg",
        "dest": DANKY / "danky-1998-p587-utimme.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "587",
        "url": "https://archive.org/details/africanamericanne00dank/page/587/mode/1up",
        "caption": "Danky entry 6142: Utimme Umana/La Voz Oculta, six times a year, Trenton State College. NN-Sc Nov/Dec 1985-Nov 1993.",
        "quote": "6142 Utimme Umana/La Voz Oculta. 1968-? Frequency: Six times a year. Trenton, NJ. Published by Trenton State College.",
    },
    {
        "id": 41,
        "clip_id": "danky-voice-plainfield",
        "src": DANKY / "danky-1998-p594-voice.jpg",
        "dest": DANKY / "danky-1998-p594-voice-plainfield.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "594",
        "url": "https://archive.org/details/africanamericanne00dank/page/594/mode/1up",
        "caption": "Danky entry 6211: The Voice, weekly, Plainfield, Voice Associates. NjPla June 22-Nov 16 1968 and June 13 1970-Mar 20 1974.",
        "quote": "6211 The Voice. 1968-1974? Frequency: Weekly. Plainfield, NJ. Published by The Voice Associates, Inc.",
    },
    {
        "id": 113,
        "clip_id": "danky-wait",
        "src": DANKY / "danky-1998-p601-wait.jpg",
        "dest": DANKY / "danky-1998-p601-wait.jpg",
        "kind": "catalog_record",
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "page": "601",
        "url": "https://archive.org/details/africanamericanne00dank/page/601/mode/1up",
        "caption": "Danky entry 6279: Wait, monthly, Trenton, A and S Publishing, editor George S. Adams Jr. WHi v.2 n.2 Feb 1962.",
        "quote": "6279 Wait. 1961?-? Frequency: Monthly. Trenton, NJ. Previous editor(s): George S. Adams Jr.",
    },
    {
        "id": 73,
        "clip_id": "utimme-1976-times",
        "src": SHOTS / "q8open-utimme-1976.png",
        "dest": CLIPS / "utimme-1976-04-23-trenton-times.png",
        "kind": "clip",
        "source": "The Times",
        "sourceCity": "Trenton, New Jersey",
        "date": "1976-04-23",
        "page": "8",
        "url": "https://www.newspapers.com/image/1192937414/",
        "caption": "Trenton Times: Utimme Umana/La Voz Oculta named as the weekly minority publication on the Trenton State campus.",
        "quote": "supported by the Minority Executive Council and Utimme Umana/La Voz Oculta, the weekly minority publication on campus.",
    },
    {
        "id": 73,
        "clip_id": "utimme-1993-times",
        "src": SHOTS / "q8open-utimme-1993.png",
        "dest": CLIPS / "utimme-1993-09-27-trenton-times.png",
        "kind": "clip",
        "source": "The Times",
        "sourceCity": "Trenton, New Jersey",
        "date": "1993-09-27",
        "page": "32",
        "url": "https://www.newspapers.com/image/1197515771/",
        "caption": "Trenton Times campus guide lists Utimme Umana/La Voz Oculta as the minority magazine.",
        "quote": "20 minority organizations, including Utimme Umana/La Voz Oculta, the minority magazine.",
    },
]

NOTES = {
    62: (
        "Danky 1998 entry 243: unknown frequency, Newark, Yusef Iman, 26 pages, OCLC 37049846. "
        "Poetry, short stories, essays. WHi holds Aug 1966 (Pam 01-6116). Newspapers.com Festival "
        "of the Arts cards were later generic festivals, not this magazine."
    ),
    28: (
        "Danky 1998 entry 934 spells the title Black New Ark; monthly; motto \"The Voice of New "
        "Ark's Inner City\"; variant Black News; WHi microfilm Apr-Nov 1968, Jan 1970, Apr 1972-"
        "Jan/Feb 1974. Newspapers.com \"Black Newark\" cards on this pass were Newark civic news, "
        "not the paper."
    ),
    69: (
        "Danky 1998 entry 1867: 1969 only, Newark, Jihad Publications, 65 pages. Editors Le Roi "
        "Jones, Amamu Baraka, Larry Neal, A. B. Spellman. ISSN 0011-1244; OCLC 2259919. WHi n.1-3; "
        "also DHU, MoK, WU. Newspapers.com Cricket/Jihad cards were 1987 arts listings, not this magazine."
    ),
    70: (
        "Danky 1998 entry 1978: Newark, Deliverance Publishing House, editor Ralph Michel, 8 pages, "
        "religion. Chicago Public Library Vivian Harsh Collection (IC-CW) holds v.12 n.4, July/Aug 1978. "
        "No New Jersey Newspapers.com card named the paper."
    ),
    133: (
        "Danky 1998 entry 2512: monthly, Newark, United Committee for Political Freedom, 2 pages, "
        "politics and civil rights, OCLC 11733840. WHi Feb and Mar 1966 (Pam 84-3848). Newspapers.com "
        "Freedom Reports cards were 1918-1948 uses of the phrase, not this newsletter."
    ),
    76: (
        "Danky 1998 entry 4335: irregular, Newark Community Union Project, 1963?-1965?, 4 pages, "
        "housing. Variant title Newsletter. WHi Nov and Dec 11/18 1962 through Apr, July, Sept 28, "
        "Oct 12 1965 (Pam 1719). Newspapers.com Newark Community Union cards were union/county false hits."
    ),
    73: (
        "Danky 1998 entry 6142: six times a year, Trenton State College, 28 pages. Editors listed "
        "from Kingsley Ugorji (1985) through Anthony Maddot (1993). Schomburg (NN-Sc) holds Nov/Dec "
        "1985-Nov 1993. Trenton Times 23 Apr 1976 calls it the weekly minority publication on campus; "
        "Times 27 Sept 1993 calls it the minority magazine."
    ),
    41: (
        "Danky 1998 entry 6211: weekly, Plainfield, The Voice Associates, Inc., 43 cm; biweekly in "
        "[1968]. Plainfield Free Public Library (NjPla) holds v.1 n.1-11 (22 June-16 Nov 1968) and "
        "v.2 n.32-v.6 n.24 (13 June 1970-20 Mar 1974). Newspapers.com \"The Voice\" Plainfield cards "
        "opened on this pass were 1937 and 1946, before this weekly."
    ),
    113: (
        "Danky 1998 entry 6279: monthly, Trenton, A and S Publishing Company, editor George S. Adams "
        "Jr., 26 pages, beauty/fashion/entertainment, OCLC 36179394. WHi v.2 n.2 Feb 1962 (Pam 01-6260). "
        "Newspapers.com George S. Adams hits were a 1948 Freehold item and a 1961 North Plainfield widow, "
        "not this editor."
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
        if item["src"] != item["dest"]:
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
        extra_note = item["caption"]
        old_note = bucket.get("notes") or ""
        if extra_note not in old_note:
            bucket["notes"] = (old_note + "; " + extra_note).strip("; ")
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
