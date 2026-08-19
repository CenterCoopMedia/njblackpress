"""Attach verified 1970s Danky leaves. No NP clips this pass."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DANKY = ROOT / "data" / "research" / "danky"
CAT = ROOT / "data" / "research" / "source-catalog.json"
PUBS = ROOT / "data" / "publications.json"

# id, src page file, dest name, printed page, caption, quote
ROWS = [
    (119, "danky-1998-p74-atlantic.jpg", "danky-1998-p74-black-atlantic-city.jpg", 74,
     "Danky entry 765: Black Atlantic City Magazine, six times a year, BAC Publishing, editor J. H. Lyles-Belton. NN-Sc Mar/Apr 1986.",
     "765 Black Atlantic City Magazine. 1980?-? Atlantic City, NJ. Published by BAC Publishing, Inc."),
    (52, "danky-1998-p87-journal.jpg", "danky-1998-p87-black-journal.jpg", 87,
     "Danky entry 890: Black Journal, monthly, Jersey City State College African/Afro-American Studies Center, editor Bruce Mansa Terry. NN-Sc Mar 1980.",
     "890 Black Journal. 1979?-? Jersey City, NJ. Published by Jersey City State College."),
    (64, "danky-1998-p95-racers.jpg", "danky-1998-p95-black-racers.jpg", 95,
     "Danky entry 980: Black Racers Yearbook, annual, Trenton, Black American Racers Association. NN-Sc 1974.",
     "980 Black Racers Yearbook. 1974-? Annual. Trenton, NJ. Published by Black American Racers Association."),
    (123, "danky-1998-p98-sociologist.jpg", "danky-1998-p98-black-sociologist.jpg", 98,
     "Danky entry 1012: The Black Sociologist, quarterly, New Brunswick, Transaction Periodicals Consortium, 1972?-1982. ISSN 0160-3566.",
     "1012 The Black Sociologist. 1972?-1982. Quarterly. New Brunswick, NJ."),
    (127, "danky-1998-p102-truth.jpg", "danky-1998-p102-black-truth-bulletin.jpg", 102,
     "Danky entry 1057: Black Truth Bulletin, 1978?-?, NJ, history and Pan-Africanism. NN-Sc n.3 1978.",
     "1057 Black Truth Bulletin. 1978?-? Unknown. , NJ. Subject focus: History, Pan-Africanism."),
    (60, "danky-1998-p105-bwuf.jpg", "danky-1998-p105-bwuf.jpg", 105,
     "Danky entry 1085: Black Women's United Front Newsletter, Newark, 1976-?. Motto on abolition of oppression. WHi v.1 n.1 8 Mar 1976.",
     "1085 Black Women's United Front Newsletter. 1976-? Newark, NJ. WHi v.1, n.1 Mar 8, 1976."),
    (126, "danky-1998-p105-bwuf.jpg", "danky-1998-p105-bwuf.jpg", 105,
     "Danky entry 1085: Black Women's United Front Newsletter, Newark, 1976-?. Motto on abolition of oppression. WHi v.1 n.1 8 Mar 1976.",
     "1085 Black Women's United Front Newsletter. 1976-? Newark, NJ. WHi v.1, n.1 Mar 8, 1976."),
    (108, "danky-1998-p207-edperspectives.jpg", "danky-1998-p207-educational-perspectives.jpg", 207,
     "Danky entry 2163: Educational Perspectives, annual, Cherry Hill, Phi Delta Kappa Eastern Region, editor Rebecca Batts Butler. NN-Sc Dec 1984 and Dec 1985.",
     "2163 Educational Perspectives. 1978?-1985? Annual. Cherry Hill, NJ."),
    (80, "danky-1998-p224-fire2.jpg", "danky-1998-p224-fire-ii.jpg", 224,
     "Danky entry 2345: Fire II, annual, Trenton State College, editor Gabrielle Lynn McLemore. WHi v.9 Feb 1983.",
     "2345 Fire II. 1975?-? Annual. Trenton, NJ. Published by Trenton State College, Fire II Publications."),
    (122, "danky-1998-p270-hart.jpg", "danky-1998-p270-hart-fund.jpg", 270,
     "Danky entry 2832: The Hart Fund, Newark, 1972-?, The People with William S. Hart for Congressman. WHi v.1 n.1 June 1972.",
     "2832 The Hart Fund. 1972-? Newark, NJ. Published by The People with William S. Hart for Congressman."),
    (100, "danky-1998-p329-kuumba.jpg", "danky-1998-p329-kuumba.jpg", 329,
     "Danky entry 3449: Kuumba: The Black Voice Magazine, monthly, New Brunswick, 1974-1975, editor Inga Watkins. NjR Feb-Apr 1975.",
     "3449 Kuumba: The Black Voice Magazine. 1974-1975. Monthly. New Brunswick, NJ. Published by Black Voice."),
    (68, "danky-1998-p357-medic.jpg", "danky-1998-p357-medic-news.jpg", 357,
     "Danky entry 3735: MEDIC News, quarterly, Newark, Minority Economic Development Industrial and Cultural Enterprise, editor Carolyn Odom. DHU v.1 n.1-5 to Dec 1971.",
     "3735 MEDIC News. 1971-? Quarterly. Newark, NJ. Previous editor(s): Carolyn Odom."),
    (115, "danky-1998-p374-mbpsr.jpg", "danky-1998-p374-mbpsr.jpg", 374,
     "Danky entry 3900: Monthly Black Periodicals Selection Review, Newark, True Connection Subscription Agency. WHi Part 1, Section 1-4, 1973?",
     "3900 Monthly Black Periodicals Selection Review. 1973?-? Monthly. Newark, NJ."),
    (105, "danky-1998-p472-primer.jpg", "danky-1998-p472-primer.jpg", 472,
     "Danky entry 4920: Primer, bimonthly, East Orange, 1973-1978, National Conference of Black and Non-White YMCA Laymen, editor Everette T. Christmas. MnU-A 1973-1978.",
     "4920 Primer. 1973-1978. Bimonthly. East Orange, NJ."),
    (95, "danky-1998-p494-righton2.jpg", "danky-1998-p494-right-on.jpg", 494,
     "Danky entry 5151: Right On!, monthly. Place of publication Hollywood 1971-1982, Cresskill NJ Apr 1983-1989. Founding editor Judy Wieder.",
     "5151 Right On! 1971-. Monthly. Place of publication varies: Hollywood, CA, 1971-1982, Cresskill, NJ, Apr 1983-1989."),
    (83, "danky-1998-p494-righton2.jpg", "danky-1998-p494-right-on.jpg", 494,
     "Danky entry 5153: Right On! Focus, quarterly, Cresskill, DS Magazine, editor Cynthia M. Horner. NN-Sc Summer 1983.",
     "5153 Right On! Focus. 1982?-? Quarterly. Cresskill, NJ. Published by DS Magazine, Inc."),
    (96, "danky-1998-p494-righton2.jpg", "danky-1998-p494-right-on.jpg", 494,
     "Danky entry 5154: Right On! Presents Class, six times a year, Cresskill, DS Magazine, editor Cynthia M. Horner.",
     "5154 Right On! Presents Class. 1983-? Six times a year. Cresskill, NJ."),
    (103, "danky-1998-p575-ujamaa.jpg", "danky-1998-p575-ujamaa.jpg", 575,
     "Danky entry 6003: Ujamaa, quarterly irregular, Wayne, William Paterson College Black Studies. Editors Lester Forrester and Eva Byrd, Jan 1974. NN-Sc 1971-1974.",
     "6003 Ujamaa: Journal of the Black Students Union. 1971?-? Wayne, NJ. Published by William Paterson College."),
    (56, "danky-1998-p577-unionmsg2.jpg", "danky-1998-p577-union-messenger.jpg", 577,
     "Danky entry 6026: The Union Messenger, Camden, U.A.M.E. Church, 1979?-?. WHi 20 Oct 1979.",
     "6026 The Union Messenger. 1979?-? Camden, NJ. Published by U.A.M.E. Church. WHi Oct 20, 1979."),
]

NOTES = {
    119: "Danky 1998 entry 765: six times a year, Atlantic City, BAC Publishing, editor J. H. Lyles-Belton, 46 pages. Schomburg (NN-Sc) holds v.7 n.3, Mar/Apr 1986.",
    52: "Danky 1998 entry 890: monthly, Jersey City State College African/Afro-American Studies Center, 47 pages, editor Bruce Mansa Terry. NN-Sc v.1 n.16, Mar 1980.",
    64: "Danky 1998 entry 980: annual, Trenton, Black American Racers Association, 32 pages, automobile racing, OCLC 33901207. NN-Sc 1974.",
    123: "Danky 1998 entry 1012: quarterly, New Brunswick, Transaction Periodicals Consortium, 1972?-1982, 111 pages. ISSN 0160-3566; OCLC 17011265. UnM microform 1977-1979, 1982.",
    127: "Danky 1998 entry 1057: 1978?-?, New Jersey (city blank in Danky), 12 pages, history and Pan-Africanism. NN-Sc n.3, 1978.",
    60: "Danky 1998 entry 1085: Newark, 1976-?, 22 pages, OCLC 30791066. Motto: \"Abolition of every possibility of oppression and exploitation - that's our slogan!\" WHi v.1 n.1, 8 Mar 1976 (Pam 01-4237).",
    126: "Danky 1998 entry 1085: same Newark newsletter as id 60. WHi v.1 n.1, 8 Mar 1976.",
    108: "Danky 1998 entry 2163: annual, Cherry Hill, National Sorority of Phi Delta Kappa Eastern Region, editor Rebecca Batts Butler, OCLC 38192785. NN-Sc v.8 n.1 and v.9 n.1, Dec 1984 and Dec 1985.",
    80: "Danky 1998 entry 2345: annual, Trenton State College Fire II Publications, 33 pages, editor Gabrielle Lynn McLemore, OCLC 29551936. Poetry, short stories, essays, art. WHi v.9, Feb 1983.",
    122: "Danky 1998 entry 2832: Newark, 1972-?, The People with William S. Hart for Congressman, 4 pages, Democratic Party / William S. Hart. WHi v.1 n.1, June 1972. Star-Ledger 31 May 1972 names the Hart Fund as the citizens' committee for Mayor Hart, not the newsletter itself.",
    100: "Danky 1998 entry 3449: monthly, New Brunswick, 1974-1975, published by Black Voice, editor Inga Watkins, 16 pages. Poetry, short stories, photography. Rutgers (NjR) holds v.1 n.3-5, Feb-Apr 1975.",
    68: "Danky 1998 entry 3735: quarterly, Newark, MEDIC Inc., editor Carolyn Odom, 8 pages, business and economic development. Howard (DHU) holds v.1 n.1-5 through Dec 1971. Newspapers.com MEDIC hits were generic medical news and a Newark, Ohio paper.",
    115: "Danky 1998 entry 3900: monthly, Newark, True Connection Subscription Agency, 2 pages, bibliography of periodicals. WHi Part 1, Section 1-4, 1973? (Pam 76-1226).",
    105: "Danky 1998 entry 4920: bimonthly, East Orange, 1973-1978, National Conference of Black and Non-White YMCA Laymen, editor Everette T. Christmas. University of Minnesota YMCA archives hold 1973-1978.",
    95: "Danky 1998 entry 5151: monthly. Founding editor Judy Wieder (Oct 1971-Dec 1972). Publisher Laufer then WP then DS Magazine. Place of publication Hollywood 1971-1982, Cresskill NJ Apr 1983-1989. ISSN 0048-8305.",
    83: "Danky 1998 entry 5153: quarterly, Cresskill, DS Magazine, editor Cynthia M. Horner, television. ISSN 0737-2779. NN-Sc v.2 n.3, Summer 1983.",
    96: "Danky 1998 entry 5154: six times a year, Cresskill, DS Magazine. Editors Cynthia M. Horner Apr 1983-Mar 1985; Michael Edrei Aug/Sept 1985-Jan 1986.",
    103: "Danky 1998 entry 6003: quarterly irregular, Wayne, William Paterson College Department of Black Studies, 52 pages. Editors Lester Forrester and Eva Byrd, Jan 1974. NN-Sc v.1 n.1 Sept 1971; v.2 n.1 Spring 1973; v.3 Jan 1974.",
    56: "Danky 1998 entry 6026: Camden, U.A.M.E. Church, 1979?-?, 20 pages, African Methodist Episcopal Church. WHi 20 Oct 1979. Newspapers.com Union Messenger cards were 1951 Camden labor items, not this church paper.",
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}

    for pid, src_name, dest_name, page, caption, quote in ROWS:
        src = DANKY / src_name
        dest = DANKY / dest_name
        if not src.exists():
            raise SystemExit(f"missing {src}")
        if src != dest:
            dest.write_bytes(src.read_bytes())
        rel = str(dest.relative_to(ROOT)).replace("\\", "/")
        url = f"https://archive.org/details/africanamericanne00dank/page/{page}/mode/1up"
        hit = {
            "kind": "catalog_record",
            "title": caption,
            "url": url,
            "localFile": rel,
            "source": "Danky and Hady 1998 / Internet Archive",
            "date": "1998",
            "caption": caption,
        }
        row = rows[pid]
        if not any(h.get("url") == url for h in row["keepers"]):
            row["keepers"].append(hit)
        row["status"] = "has_keeper"
        other = row["sources"]["other"]
        other["searched"] = True
        if not any(h.get("url") == url for h in other.get("hits") or []):
            other.setdefault("hits", []).append(hit)
        note = other.get("notes") or ""
        if caption not in note:
            other["notes"] = (note + "; " + caption).strip("; ")

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
    shutil.copyfile(PUBS, ROOT / "docs" / "data" / "publications.json")
    print("counts", cat["counts"])


if __name__ == "__main__":
    main()
