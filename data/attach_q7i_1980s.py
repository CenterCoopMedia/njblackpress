"""Attach 1980s civic Danky leaf keepers and honest Forum none notes."""

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
        "id": 5,
        "clip_id": "danky-1998-connection-teaneck",
        "src": "danky-leaf-p172-n215-connection-172.jpg",
        "dest": "danky-1998-p172-connection.jpg",
        "page": "172",
        "url": "https://archive.org/details/africanamericanne00dank/page/172/mode/1up",
        "caption": "Danky entry 1791: The Connection Newspaper, weekly, Teaneck, Ralph F. Johnson. Largest African-American weekly in New Jersey. WHi 5 June 1993-.",
        "quote": "The Connection Newspaper. 1982?-. Frequency: Weekly. Ralph F. Johnson, Editor, The Connection Newspaper, 362 Cedar Lane P.O. Box 2122, Teaneck, NJ 07666. Published by Ralph F. Johnson. Last issue 24 pages. OCLC no. 18514803. Largest African-American Weekly Newspaper in New Jersey. WHi v.11, n.20- Circulation Jun 5, 1993-.",
    },
    {
        "id": 13,
        "clip_id": "danky-1998-city-news",
        "src": "danky-leaf-p155-n198-city-news-155.jpg",
        "dest": "danky-1998-p155-city-news.jpg",
        "page": "155",
        "url": "https://archive.org/details/africanamericanne00dank/page/155/mode/1up",
        "caption": "Danky entry 1607: City News, weekly, Plainfield, Jan Edgenton Johnson / Henry O. Johnson. NN-Sc 21 Aug 1991-.",
        "quote": "City News. 1983-. Frequency: Weekly. Jan Edgenton Johnson, Editor, City News, P.O. Box 1774, Plainfield, NJ 07060. Published by Henry O. Johnson. Last issue 12 pages. NN-Sc [v.7, n.50- Newspapers [Aug 21, 1991-.",
    },
    {
        "id": 40,
        "clip_id": "danky-1998-nubian-news",
        "src": "danky-leaf-p435-n478-nubian-435.jpg",
        "dest": "danky-1998-p435-nubian-news.jpg",
        "page": "435",
        "url": "https://archive.org/details/africanamericanne00dank/page/435/mode/1up",
        "caption": "Danky entry 4532: The Nubian News, monthly, Trenton, Kamau Kujichagulia. New Jersey's only African-American/Hispanic news source. WHi May 1993-.",
        "quote": "The Nubian News. 1989?-. Frequency: Monthly. Kamau Kujichagulia, Editor, The Nubian News, 928 Edgewood Ave. Trenton, NJ 08618. Published by Kamau Kujichagulia. Last issue 24 pages. Previous editor(s): Pamela A. Sims. Two pages are in Spanish. OCLC no. 28588271. New Jersey's Only African-American/Hispanic News Source. WHi v.5, n.5- Microforms May, 1993-.",
    },
    {
        "id": 61,
        "clip_id": "danky-1998-npsr",
        "src": "danky-leaf-p393-n436-npsr-393.jpg",
        "dest": "danky-1998-p393-npsr.jpg",
        "page": "393",
        "url": "https://archive.org/details/africanamericanne00dank/page/393/mode/1up",
        "caption": "Danky entry 4098: The National Political Science Review, annual, Rutgers New Brunswick, Matthew Holden Jr. / National Conference of Black Political Scientists.",
        "quote": "The National Political Science Review. 1989-. Frequency: Annual. Matthew Holden Jr., Editor, National Political Science Review, Rutgers University, New Brunswick, NJ. Published by National Conference of Black Political Scientists. Last issue 347 pages. Previous editor(s): Lucius J. Barker. ISSN 0896-629x. OCLC no. 17223548. WU v.1- 1989-. WMM v.1- Periodicals 1989-.",
    },
    {
        "id": 74,
        "clip_id": "danky-1998-bootstrap",
        "src": "danky-leaf-p113-n156-bootstrap.jpg",
        "dest": "danky-1998-p113-bootstrap.jpg",
        "page": "113",
        "url": "https://archive.org/details/africanamericanne00dank/page/113/mode/1up",
        "caption": "Danky entry 1166: BootStrap, Newark, Interracial Council for Business Opportunity, Bernard H. Saperstein. NN-Sc Aug/Sept 1983.",
        "quote": "BootStrap. 1981?-? Frequency: Unknown. Newark, NJ. Published by Interracial Council for Business Opportunity. Last issue 8 pages. Previous editor(s): Bernard H. Saperstein. Subject focus: Money, Investments, Economics, Finance, Business. NN-Sc v.3, n.4 Newsletters Aug/Sept, 1983.",
    },
    {
        "id": 77,
        "clip_id": "danky-1998-black-nj-magazine",
        "src": "danky-leaf-p91-n134-black-nj-mag.jpg",
        "dest": "danky-1998-p91-black-nj-magazine.jpg",
        "page": "91",
        "url": "https://archive.org/details/africanamericanne00dank/page/91/mode/1up",
        "caption": "Danky entry 935: Black New Jersey Magazine, bimonthly, Atlantic City, Barbara Johnson. NN-Sc Mar/Apr 1988.",
        "quote": "Black New Jersey Magazine. 1988?-? Frequency: Bimonthly. Atlantic City, NJ. Last issue 6 pages. Previous editor(s): Barbara Johnson. Subject focus: Business, New Jersey media. NN-Sc Mar/Apr, 1988 Newsletters.",
    },
    {
        "id": 81,
        "clip_id": "danky-1998-oni",
        "src": "danky-leaf-p443-n486-oni-443.jpg",
        "dest": "danky-1998-p443-oni.jpg",
        "page": "443",
        "url": "https://archive.org/details/africanamericanne00dank/page/443/mode/1up",
        "caption": "Danky entry 4620: ONI, Newark, International Black Women's Congress, Rhashidah Elaine McNeill. NN-Sc Winter/Spring 1988.",
        "quote": "ONI. 1988-. Frequency: Unknown. Rhashidah Elaine McNeill, Editor, ONI, 1081 Bergen St., Newark, NJ 07112. Published by International Black Women's Congress (IBWC). Last issue 8 pages. Previous editor(s): Elaine McNeill Rhashidali. OCLC no. 37974207. WHi v.1[ns], n.2 Pam 01-5668 Spring, 1995. NN-Sc v.1, n.1-2 Newsletters Winter/Spring, 1988.",
    },
    {
        "id": 86,
        "clip_id": "danky-1998-starline",
        "src": "danky-leaf-p540-n583-starline-540.jpg",
        "dest": "danky-1998-p540-starline.jpg",
        "page": "540",
        "url": "https://archive.org/details/africanamericanne00dank/page/540/mode/1up",
        "caption": "Danky entry 5629: Starline, monthly, Paramus, Mary Anne Cassata / Starline Publications. WHi n.114- 1996-.",
        "quote": "Starline. 1987?-. Frequency: Monthly. Mary Anne Cassata, Editor, Starline, 210 Route 4 East, Paramus, NJ 07052. Published by Starline Publications, Inc. Last issue 58 pages. OCLC no. 36223142. Subject focus: Rap (Music), Rock music, Music. WHi n.114- Circulation 1996-.",
    },
    {
        "id": 91,
        "clip_id": "danky-1998-literary-griot",
        "src": "danky-leaf-p343-n386-literary-griot.jpg",
        "dest": "danky-1998-p343-literary-griot.jpg",
        "page": "343",
        "url": "https://archive.org/details/africanamericanne00dank/page/343/mode/1up",
        "caption": "Danky entry 3600: The Literary Griot, twice a year, Ousseynou B. Traore, 300 Pompton Road Wayne NJ. Place varies Indiana PA / Paterson NJ. WHi 1989-1992.",
        "quote": "The Literary Griot. 1988-. Frequency: Two times a year. Ousseynou B. Traore, Editor, Literary Griot, 300 Pompton Road, Fort Wayne, NJ 07470. Published by International Journal of Black Expressive Cultural Studies. Last issue 156 pages. Place of publication varies: Indiana, PA; Paterson, NJ. ISSN 0737-0873. OCLC no. 20441085. WHi v.1, n.2; v.3, n.1; v.4, n.1/2 Pam 01-4562 Spring, 1989; Spring, 1991; Spring/Fall, 1992.",
    },
    {
        "id": 104,
        "clip_id": "danky-1998-update-njbic",
        "src": "danky-leaf-p580-n623-update.jpg",
        "dest": "danky-1998-p580-update.jpg",
        "page": "580",
        "url": "https://archive.org/details/africanamericanne00dank/page/580/mode/1up",
        "caption": "Danky entry 6069: Update, Newark, New Jersey Black Issues Convention. Leftover on p.581. NN-Sc Aug 1984.",
        "quote": "Update. 1983?-? Frequency: Unknown. Newark, NJ. Published by New Jersey Black Issues Convention. Last issue 12 pages. A publication of the New Jersey Black Issues Convention. Politics, Race relations. NN-Sc v.2, n.4 Uncataloged serials Aug, 1984.",
    },
    {
        "id": 106,
        "clip_id": "danky-1998-nj-aahgs",
        "src": "danky-leaf-p427-n470-aahgs.jpg",
        "dest": "danky-1998-p427-nj-aahgs.jpg",
        "page": "427",
        "url": "https://archive.org/details/africanamericanne00dank/page/427/mode/1up",
        "caption": "Danky entry 4444: NJ-AAHGS Newsletter, monthly except July and August, Elizabeth Peale Johnson, Jersey City. WHi 1994-.",
        "quote": "NJ-AAHGS Newsletter. 1989-. Frequency: Monthly except July and August. Elizabeth Peale Johnson, Editor, NJ-AAHGS Newsletter, 22 Willow St. Jersey City, NJ 07305-2199. Published by New Jersey Chapter, Afro-American Genealogical Society, Inc. Last issue 8 pages. Variant title(s): AAHGS Newsletter. OCLC no. 28388925. WHi v.6, n.5-v.9, n.7 Microfilm May, 1994-Sept, 1996. WHi v.9, n.8- Circulation Oct, 1996-.",
    },
    {
        "id": 110,
        "clip_id": "danky-1998-perspectus",
        "src": "danky-leaf-p461-n504-perspectus-461.jpg",
        "dest": "danky-1998-p461-perspectus.jpg",
        "page": "461",
        "url": "https://archive.org/details/africanamericanne00dank/page/461/mode/1up",
        "caption": "Danky entry 4807: Perspectus News Magazine, monthly, East Orange, The Perspectus Group. NN-Sc Oct 1989.",
        "quote": "Perspectus News Magazine. 1989-? Frequency: Monthly. East Orange, NJ. Published by The Perspectus Group. Last issue 44 pages. ISSN 1048-3497. LC card no. sn90-2907. OCLC no. 20925105. Lifestyle. NN-Sc v.1, n.6 Uncataloged serials Oct, 1989.",
    },
    {
        "id": 118,
        "clip_id": "danky-1998-gospel-today",
        "src": "danky-leaf-p253-n296-gospel-253.jpg",
        "dest": "danky-1998-p253-gospel-today.jpg",
        "page": "253",
        "url": "https://archive.org/details/africanamericanne00dank/page/253/mode/1up",
        "caption": "Danky entry 2656: Gospel Today Magazine, bimonthly, Teresa E. Hairston. Place of publication Fort Lee NJ Dec 1990/Jan 1992.",
        "quote": "Gospel Today Magazine. 1990-. Frequency: Bimonthly. Kimberly Gilbert Crutcher, Editor. Published by Teresa E. Hairston. Last issue 46 pages. Place of publication varies: Fort Lee, NJ, Dec 1990/Jan 1992. OCLC no. 28825640. America's Leading Gospel Music Magazine. WHi v.6, n.1- Jan/Feb, 1995-. ICCBMR v.2, n.1- Periodicals Dec/Jan, 1991-.",
    },
    {
        "id": 120,
        "clip_id": "danky-1998-write-on",
        "src": "danky-leaf-p621-n664-write-on-621.jpg",
        "dest": "danky-1998-p621-write-on.jpg",
        "page": "621",
        "url": "https://archive.org/details/africanamericanne00dank/page/621/mode/1up",
        "caption": "Danky entry 6497: Write On Newsletter, quarterly, Saddle Brook, Rejoti Publishing, Veona Thomis. NN-Sc June 1985.",
        "quote": "Write On Newsletter. 1985-? Frequency: Quarterly. Saddle Brook, NJ. Published by Rejoti Publishing. Last issue 38 pages. Previous editor(s): Veona Thomis. Commemorative issue. Publishers and publishing, Authors, Poetry, Short stories. NN-Sc June, 1985 Newsletters.",
    },
    {
        "id": 121,
        "clip_id": "danky-1998-testimony",
        "src": "danky-leaf-p557-n600-testimony-557.jpg",
        "dest": "danky-1998-p557-testimony.jpg",
        "page": "557",
        "url": "https://archive.org/details/africanamericanne00dank/page/557/mode/1up",
        "caption": "Danky entry 5815: Testimony: A Journal of African-American Poetry, quarterly, Montclair, Sandra West. TNF Winter 1987.",
        "quote": "Testimony: A Journal of African-American Poetry. 1987-? Frequency: Quarterly. Montclair, NJ. Last issue 30 pages. Previous editor(s): Sandra West. OCLC no. 37883333. Poetry, Art, Photography. TNF v.1, n.1 Special Collections Winter, 1987.",
    },
    {
        "id": 124,
        "clip_id": "danky-1998-best-of-rap",
        "src": "danky-leaf-p67-n110-best-rap-67.jpg",
        "dest": "danky-1998-p67-best-of-rap.jpg",
        "page": "67",
        "url": "https://archive.org/details/africanamericanne00dank/page/67/mode/1up",
        "caption": "Danky entry 698: The Best of Rap & R & B, bimonthly, Nathasha Brooks-Everett, Word Up! Publications, Paramus. Leftover on p.68. NN-Sc July 1994.",
        "quote": "The Best of Rap & R & B. 1988-. Frequency: Bimonthly. Nathasha Brooks-Everett, Editor, Best of Rap & R & B, 210 Route 4 E, Suite 401, Paramus, NJ 07652-5116. Published by Word Up! Publications, Inc. Last issue 66 pages. Variant title(s): Rap Masters Present The Best of Rap & R & B. NN-SC v.7, n.4 Uncataloged serials July, 1994.",
    },
    {
        "id": 130,
        "clip_id": "danky-1998-communique",
        "src": "danky-leaf-p168-n211-communique-168.jpg",
        "dest": "danky-1998-p168-communique.jpg",
        "page": "168",
        "url": "https://archive.org/details/africanamericanne00dank/page/168/mode/1up",
        "caption": "Danky entry 1748: Communique, quarterly, East Orange, New Jersey Coalition of 100 Black Women, Pamela Miller. NN-Sc Spring 1983.",
        "quote": "Communique: Quarterly Newsletter of the New Jersey Coalition of 100 Black Women. 1983-? Frequency: Quarterly. East Orange, NJ. Published by New Jersey Coalition of 100 Black Women. Last issue 8 pages. Previous editor(s): Pamela Miller. Women, Art, Education, Profiles, Careers. NN-Sc v.1, n.1 Newsletters Spring, 1983.",
    },
    {
        "id": 131,
        "clip_id": "danky-1998-connection-131",
        "src": "danky-leaf-p172-n215-connection-172.jpg",
        "dest": "danky-1998-p172-connection-131.jpg",
        "page": "172",
        "url": "https://archive.org/details/africanamericanne00dank/page/172/mode/1up",
        "caption": "Danky entry 1791: The Connection Newspaper, weekly, Teaneck, Ralph F. Johnson. Same Teaneck weekly as id 5. WHi 5 June 1993-.",
        "quote": "The Connection Newspaper. 1982?-. Frequency: Weekly. Ralph F. Johnson, Editor, The Connection Newspaper, 362 Cedar Lane P.O. Box 2122, Teaneck, NJ 07666. Published by Ralph F. Johnson. Last issue 24 pages. OCLC no. 18514803. Largest African-American Weekly Newspaper in New Jersey. WHi v.11, n.20- Circulation Jun 5, 1993-.",
    },
    {
        "id": 132,
        "clip_id": "danky-1998-corporate-hq",
        "src": "danky-leaf-p176-n219-corporate-176.jpg",
        "dest": "danky-1998-p176-corporate-hq.jpg",
        "page": "176",
        "url": "https://archive.org/details/africanamericanne00dank/page/176/mode/1up",
        "caption": "Danky entry 1839: Corporate Headquarters, quarterly, Westfield, Harold E. Fisher / Terri Fisher, 1985?-1991?. Holdings leftover on p.177.",
        "quote": "Corporate Headquarters. 1985?-1991? Frequency: Quarterly. Westfield, NJ. Published by Harold E. Fisher. Last issue 31 pages. Previous editor(s): Terri Fisher. OCLC no. 16218293. Issue marked v.3, n.4 is actually v.2,n.4. Business, Education (Higher), Careers, Employment. WHi v.4, n.1 Pam 01-3081 Winter/Spring, 1991. DHU 4th Quarter, 1985-Winter/Spring, 1991. NN-Sc v.1, n.3-v.2, n.4 Serials 4th Quarter, 1985-Fall/Winter, 1987.",
    },
]

NONE_NOTES = {
    39: "Danky 1998 African-American Newspapers and Periodicals has no entry for The Forum, Newark, Forum Publications, LCCN sn88071371. Nearby Forum titles are out of state.",
    42: "Danky 1998 African-American Newspapers and Periodicals has no entry for Essex Forum, East Orange, Multi-Linear Publications, LCCN sn88071370. Newspapers.com Essex Forum 1980 was a Maplewood restaurant want ad.",
}

EXTRAS = {
    5: " Danky 1998 entry 1791: weekly, Teaneck, Ralph F. Johnson, 362 Cedar Lane. OCLC 18514803. Called the largest African-American weekly in New Jersey. WHi from 5 June 1993.",
    13: " Danky 1998 entry 1607: weekly, Plainfield, editor Jan Edgenton Johnson, publisher Henry O. Johnson, P.O. Box 1774. NN-Sc from 21 Aug 1991.",
    40: " Danky 1998 entry 4532: monthly, 928 Edgewood Ave Trenton, Kamau Kujichagulia, previous editor Pamela A. Sims. Two pages in Spanish. OCLC 28588271. WHi from May 1993.",
    61: " Danky 1998 entry 4098: annual, Rutgers New Brunswick, editor Matthew Holden Jr., National Conference of Black Political Scientists. Previous editor Lucius J. Barker. ISSN 0896-629x. OCLC 17223548. WU and WMM hold from 1989.",
    74: " Danky 1998 entry 1166: BootStrap, Newark, Interracial Council for Business Opportunity, previous editor Bernard H. Saperstein, 8 pages. NN-Sc v.3 n.4 Aug/Sept 1983.",
    77: " Danky 1998 entry 935: bimonthly, Atlantic City, previous editor Barbara Johnson, 6 pages, business and New Jersey media. NN-Sc Mar/Apr 1988.",
    81: " Danky 1998 entry 4620: Newark, International Black Women's Congress, 1081 Bergen St, editor Rhashidah Elaine McNeill. OCLC 37974207. NN-Sc Winter/Spring 1988. WHi Spring 1995.",
    86: " Danky 1998 entry 5629: monthly, 210 Route 4 East Paramus, Mary Anne Cassata / Starline Publications. OCLC 36223142. Rap and rock music. WHi n.114- 1996-.",
    91: " Danky 1998 entry 3600: twice a year, editor Ousseynou B. Traore, 300 Pompton Road (Wayne zip 07470). Place varies Indiana PA and Paterson NJ. ISSN 0737-0873. OCLC 20441085. WHi 1989-1992.",
    104: " Danky 1998 entry 6069: Newark, published by New Jersey Black Issues Convention, 12 pages. NN-Sc v.2 n.4 Aug 1984.",
    106: " Danky 1998 entry 4444: monthly except July and August, Elizabeth Peale Johnson, 22 Willow St Jersey City. New Jersey Chapter, Afro-American Genealogical Society. OCLC 28388925. WHi from May 1994.",
    110: " Danky 1998 entry 4807: monthly, East Orange, The Perspectus Group, 44 pages. ISSN 1048-3497. OCLC 20925105. NN-Sc v.1 n.6 Oct 1989.",
    118: " Danky 1998 entry 2656: bimonthly, published by Teresa E. Hairston, editor Kimberly Gilbert Crutcher. Place of publication Fort Lee NJ Dec 1990/Jan 1992, later Nashville. OCLC 28825640. WHi from Jan/Feb 1995.",
    120: " Danky 1998 entry 6497: quarterly, Saddle Brook, Rejoti Publishing, previous editor Veona Thomis, 38 pages. NN-Sc June 1985.",
    121: " Danky 1998 entry 5815: quarterly, Montclair, editor Sandra West, 30 pages. OCLC 37883333. TNF v.1 n.1 Winter 1987.",
    124: " Danky 1998 entry 698: bimonthly, Nathasha Brooks-Everett, Word Up! Publications, 210 Route 4 E Suite 401 Paramus. Variant Rap Masters Present The Best of Rap & R & B. NN-Sc v.7 n.4 July 1994.",
    130: " Danky 1998 entry 1748: quarterly, East Orange, New Jersey Coalition of 100 Black Women, previous editor Pamela Miller, 8 pages. NN-Sc Spring 1983.",
    131: " Danky 1998 entry 1791: same Teaneck weekly as The Connection / North Jersey Connection (id 5). Ralph F. Johnson. OCLC 18514803. WHi from 5 June 1993.",
    132: " Danky 1998 entry 1839: quarterly 1985?-1991?, Westfield, Harold E. Fisher, previous editor Terri Fisher. OCLC 16218293. WHi Winter/Spring 1991. DHU 1985-1991. NN-Sc 1985-1987.",
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


if __name__ == "__main__":
    main()
