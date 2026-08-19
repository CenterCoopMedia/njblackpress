"""Attach 1970s civic Danky leaf keepers."""

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
        "id": 46,
        "clip_id": "danky-1998-african-voice",
        "src": "danky-leaf-p18-n61-african-voice-18.jpg",
        "dest": "danky-1998-p18-african-voice.jpg",
        "page": "18",
        "url": "https://archive.org/details/africanamericanne00dank/page/18/mode/1up",
        "caption": "Danky entry 176: The African Voice, monthly, Camden, Black Cooperative Association. WHi June/July 1972.",
        "quote": "The African Voice. 1972-? Frequency: Monthly. Camden, NJ. Published by The Black Cooperative Association. Last issue 20 pages. OCLC no. 29338865. WHi v.1, n.2 Pam 01-3656 June/July, 1972.",
    },
    {
        "id": 107,
        "clip_id": "danky-1998-black-voice-newark",
        "src": "danky-leaf-p104-n147-black-voice.jpg",
        "dest": "danky-1998-p104-black-voice.jpg",
        "page": "104",
        "url": "https://archive.org/details/africanamericanne00dank/page/104/mode/1up",
        "caption": "Danky entry 1071: The Black Voice, monthly 1970-1975?, Newark, United Black Workers.",
        "quote": "The Black Voice. 1970-1975? Frequency: Monthly. Newark, NJ. Published by United Black Workers. Last issue 12 pages. LC card no. sn89-14075. OCLC no. 17008478. WHi v.1, n.3-4; v.2, n.5-v.5, n.2 Jan-Feb?, 1971; July, 1972-Mar, 1975.",
    },
    {
        "id": 98,
        "clip_id": "danky-1998-black-voice-carta",
        "src": "danky-leaf-p104-n147-black-voice.jpg",
        "dest": "danky-1998-p104-black-voice-carta.jpg",
        "page": "104",
        "url": "https://archive.org/details/africanamericanne00dank/page/104/mode/1up",
        "caption": "Danky entry 1076: Black Voice/Carta Boricua, Piscataway, Paul Robeson Cultural Center.",
        "quote": "Black Voice/Carta Boricua. 1970?-. Frequency: Weekly during school year. Kim Robinson, Editor. Published by Paul Robeson Cultural Center. Last issue 20 pages. NjR [v.3-v.24] Periodicals [1972-1993].",
    },
    {
        "id": 51,
        "clip_id": "danky-1998-cfun-news",
        "src": "danky-leaf-p142-n185-cfun-142.jpg",
        "dest": "danky-1998-p142-cfun-news.jpg",
        "page": "142",
        "url": "https://archive.org/details/africanamericanne00dank/page/142/mode/1up",
        "caption": "Danky entry 1477: CFUN News, Newark, editor Imamu Amiri Baraka. WHi n.7 May 1971.",
        "quote": "CFUN News. 1970?-? Frequency: Unknown. Newark, NJ. Last issue 8 pages. Height 21 cm. Previous editor(s): Imamu Amiri Baraka. OCLC no. 30752732. WHi n.7 Pam 01-4196 May, 1971?",
    },
    {
        "id": 59,
        "clip_id": "danky-1998-en-avant",
        "src": "danky-leaf-p211-n254-en-avant-211.jpg",
        "dest": "danky-1998-p211-en-avant.jpg",
        "page": "211",
        "url": "https://archive.org/details/africanamericanne00dank/page/211/mode/1up",
        "caption": "Danky entry 2199: En Avant, Newark, Haiti/politics. WHi Mar/Apr 1973.",
        "quote": "En Avant: Bulletin pour le development de la mobilisation patriotique. 1972?-? Frequency: Unknown. Newark, NJ. Last issue 20 pages. OCLC no. 30793980. WHi Special n.4 Pam 01-4242 Mar/Apr, 1973.",
    },
    {
        "id": 134,
        "clip_id": "danky-1998-en-avant-134",
        "src": "danky-leaf-p211-n254-en-avant-211.jpg",
        "dest": "danky-1998-p211-en-avant-134.jpg",
        "page": "211",
        "url": "https://archive.org/details/africanamericanne00dank/page/211/mode/1up",
        "caption": "Danky entry 2199: En Avant, Newark, Haiti/politics. WHi Mar/Apr 1973.",
        "quote": "En Avant: Bulletin pour le development de la mobilisation patriotique. 1972?-? Frequency: Unknown. Newark, NJ. Last issue 20 pages. OCLC no. 30793980. WHi Special n.4 Pam 01-4242 Mar/Apr, 1973.",
    },
    {
        "id": 27,
        "clip_id": "danky-1998-greater-news",
        "src": "danky-leaf-p257-n300-greater-news-257.jpg",
        "dest": "danky-1998-p257-greater-news.jpg",
        "page": "257",
        "url": "https://archive.org/details/africanamericanne00dank/page/257/mode/1up",
        "caption": "Danky entry 2694: Greater News, weekly, Newark, editor Jeanne Jason. Also National / New Jersey Greater News.",
        "quote": "Greater News. 1979?-. Frequency: Weekly. Jeanne Jason, Editor, Greater News, Suite 173, 1188 Raymond Blvd, Newark, NJ 07102. Variant title(s): National Greater News. New Jersey Greater News. OCLC no. 20252858. WHi v.9, n.121 [i.e. 12]- Microforms Jan 24, 1987-.",
    },
    {
        "id": 111,
        "clip_id": "danky-1998-ngoma",
        "src": "danky-leaf-p425-n468-ngoma.jpg",
        "dest": "danky-1998-p425-ngoma.jpg",
        "page": "425",
        "url": "https://archive.org/details/africanamericanne00dank/page/425/mode/1up",
        "caption": "Danky entry 4424: Ngoma, Newark, Harambee Organization. WHi 21 Jan 1972.",
        "quote": "Ngoma. 1971-? Frequency: Unknown. Newark, NJ. Published by Harambee Organization. Some Swahili. OCLC no. 30787115. WHi v.1, n.8 Pam 01-4226 Jan 21, 1972.",
    },
    {
        "id": 21,
        "clip_id": "danky-1998-nite-lite-full",
        "src": "danky-leaf-p426-n469-ngoma-426.jpg",
        "dest": "danky-1998-p426-nite-lite-full.jpg",
        "page": "426",
        "url": "https://archive.org/details/africanamericanne00dank/page/426/mode/1up",
        "caption": "Danky entry 4440: Nite Lite, weekly, Newark, publisher Edna M. Strothers.",
        "quote": "Nite Lite. 1959?-? Frequency: Weekly. Newark, NJ. Published by Edna M. Strothers. Last issue 16 pages. Line drawings; Photographs; Commercial advertising.",
    },
]


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
        if item["caption"][:40] not in (ia.get("notes") or ""):
            ia["notes"] = ((ia.get("notes") or "") + "; " + item["caption"]).strip("; ")
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

    extras = {
        46: " Danky 1998 entry 176: monthly, Camden, Black Cooperative Association, 20 pages, OCLC 29338865. WHi v.1 n.2 June/July 1972.",
        107: " Danky 1998 entry 1071: monthly 1970-1975?, United Black Workers, labor/trade unions. WHi 1971-1975. OCLC 17008478.",
        98: " Danky 1998 entry 1076: weekly during school year, Paul Robeson Cultural Center, Kim Robinson editor. Rutgers (NjR) holds 1972-1993.",
        51: " Danky 1998 entry 1477: editor Imamu Amiri Baraka, 8 pages, politics/education/spirituality. WHi n.7 May 1971. OCLC 30752732.",
        59: " Danky 1998 entry 2199: Newark bulletin on Haitian patriotic mobilization. WHi Mar/Apr 1973. OCLC 30793980.",
        134: " Danky 1998 entry 2199: same Newark En Avant bulletin as id 59. WHi Mar/Apr 1973.",
        27: " Danky 1998 entry 2694: weekly, editor Jeanne Jason, 1188 Raymond Blvd. Also called National Greater News / New Jersey Greater News. WHi from 24 Jan 1987; DHU 1985-1990.",
        111: " Danky 1998 entry 4424: Harambee Organization, some Swahili. WHi v.1 n.8 21 Jan 1972. OCLC 30787115.",
        21: " Danky 1998 entry 4440 on p.426: weekly, Newark, published by Edna M. Strothers, 16 pages.",
    }
    for pid, extra in extras.items():
        pub = by_pub[pid]
        if extra[12:40] not in (pub.get("historicalNotes") or ""):
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
