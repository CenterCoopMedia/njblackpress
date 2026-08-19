"""Attach verified 1990s Danky leaves."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DANKY = ROOT / "data" / "research" / "danky"
CAT = ROOT / "data" / "research" / "source-catalog.json"
PUBS = ROOT / "data" / "publications.json"

# pid, src, dest, page, caption
ROWS = [
    (1, "danky-1998-p1-hype.jpg", "danky-1998-p1-hype.jpg", 1,
     "Danky entry 1: 2 Hype, bimonthly, River Edge, 1990?-1993, Word Up! Video, editor Marica A. Cole. WHi Aug 1992 and Aug 1993."),
    (15, "danky-1998-p18-afrworld.jpg", "danky-1998-p18-african-world.jpg", 18,
     "Danky entry 181: African World, monthly, Hillside, editor Imafidou Olaye. Motto The people's link. WHi Oct 1994."),
    (26, "danky-1998-p266-harambee.jpg", "danky-1998-p266-harambee.jpg", 266,
     "Danky entry 2786: Harambee, Orange, Just Us Books, a newspaper for young readers on the African-American experience. WHi 1992-1993-."),
    (44, "danky-1998-p236-franklin.jpg", "danky-1998-p236-franklin-voice.jpg", 236,
     "Danky entry 2469: The Franklin Voice, monthly, Somerset, editor Paula McCoy-Pinderhughes. NN-Sc Feb 1996-."),
    (47, "danky-1998-p50-artz.jpg", "danky-1998-p50-artz.jpg", 50,
     "Danky entry 511: Artz, monthly, Plainfield, 1991-1993?, City News Publishing. Editors Lorraine Davis Hickman; Jan M. Edgerton-Johnson. NN-Sc Mar 1992-Summer 1993."),
    (49, "danky-1998-p51-artz2.jpg", "danky-1998-p51-at-the-crossroads.jpg", 51,
     "Danky entry 529: At the Crossroads, six times a year, New Brunswick, Crossroads Theatre Company, editor Ernie Johnston. WHi Winter 1997-."),
    (50, "danky-1998-p409-deadline.jpg", "danky-1998-p409-nj-deadline.jpg", 409,
     "Danky entry 4261: New Jersey Deadline, twice a month, Newark, Deadline Publishing, editor Harry B. Webber. WHi v.2 n.4 30 May 1960."),
    (53, "danky-1998-p356-mcsq.jpg", "danky-1998-p356-mc-squared.jpg", 356,
     "Danky entry 3726: MC Squared, Piscataway, POSRO Inc. Comic books. WHi v.1 n.1-3 July 1991-1994."),
    (54, "danky-1998-p316-jaam.jpg", "danky-1998-p316-jaam.jpg", 316,
     "Danky entry 3314: Journal of African American Men, quarterly, Transaction Publishers / Rutgers, New Brunswick. Editor Gary A. Sailes. WHi Summer 1995-."),
    (58, "danky-1998-p625-yes.jpg", "danky-1998-p625-yes.jpg", 625,
     "Danky entry 6536: Yes: Youth Excited About Success, nine times a year, Plainfield, editor Jan M. Edgenton Johnson. WHi 1994/5-."),
    (63, "danky-1998-p562-tbw.jpg", "danky-1998-p562-todays-black-woman.jpg", 562,
     "Danky entry 5866: Today's Black Woman, nine times a year, Paramus, editor Kate Ferguson, John Blassingame publisher. WHi Apr 1995-."),
    (138, "danky-1998-p562-tbw.jpg", "danky-1998-p562-todays-black-woman.jpg", 562,
     "Danky entry 5866: Today's Black Woman, nine times a year, Paramus, editor Kate Ferguson. Same Danky record as id 63."),
    (65, "danky-1998-p535-spirit.jpg", "danky-1998-p535-spirit.jpg", 535,
     "Danky entry 5578: Spirit: The Guide to the Soul, six times a year, Plainfield, editor Natasha Munson. NN-Sc July/Aug 1996."),
    (75, "danky-1998-p405-network2.jpg", "danky-1998-p405-network.jpg", 405,
     "Danky entry 4216: The Network, six times a year, Newark, African-American Institute of Islamic Research, editor Zain A. Abdullah. NN-Sc Jan 1991."),
    (78, "danky-1998-p235-fotorama.jpg", "danky-1998-p235-fotorama.jpg", 235,
     "Danky entry 2462: Fotorama, bimonthly, River Edge, Swank Publications. Premiere issue. WHi n.1 1993."),
    (82, "danky-1998-p287-hypehair.jpg", "danky-1998-p287-hype-hair.jpg", 287,
     "Danky entry 3020: Hype Hair, bimonthly, Paramus, Word Up! Video, editor Marcia A. Cole. WHi Sept 1993-."),
    (85, "danky-1998-p75-bbc.jpg", "danky-1998-p75-black-book-connection.jpg", 75,
     "Danky entry 776: Black Book Connection newsletter, bimonthly, West Orange. Motto Your link to Black authors. WHi Sept/Oct 1992."),
    (88, "danky-1998-p323-jfbm.jpg", "danky-1998-p323-just-for-black-men.jpg", 323,
     "Danky entry 3378: Just for Black Men, bimonthly, Paramus, editor Kate Ferguson, publisher John Blassingame. WHi Jan 1997."),
    (92, "danky-1998-p114-braids.jpg", "danky-1998-p114-braids-beauty.jpg", 114,
     "Danky entry 1180: Braids & Beauty, quarterly, Paramus, Word Up! Video Productions. WHi Summer 1994-Winter 1995."),
    (93, "danky-1998-p570-tryhair.jpg", "danky-1998-p570-try-it-yourself-hair.jpg", 570,
     "Danky entry 5954: Try It Yourself Hair!, bimonthly, Paramus, editor Adrienne Moore. WHi Feb 1994-."),
    (112, "danky-1998-p135-captain.jpg", "danky-1998-p135-captain-africa.jpg", 135,
     "Danky entry 1394: Captain Africa, Glen Ridge, 1992-1994, African Prince Productions. Comic books. WHi June 1992 and Feb 1994."),
    (114, "danky-1998-p620-wordup.jpg", "danky-1998-p620-word-up.jpg", 620,
     "Danky entry 6483: Word Up!, monthly, Paramus, editor Kate Ferguson, publisher Scott Mitchell Figman. WHi Nov 1991; May 1992-."),
    (117, "danky-1998-p298-icp.jpg", "danky-1998-p298-inner-city-products.jpg", 298,
     "Danky entry 3139: Inner City Products, quarterly, Piscataway, editor Donnette Bishop Johnson."),
    (125, "danky-1998-p84-hairdigest.jpg", "danky-1998-p84-black-hair-digest.jpg", 84,
     "Danky entry 866: Black Hair Digest, Paramus / River Edge, Word Up! Video, editor Natasha A. Brooks-Everett. WHi Nov 1993-."),
    (135, "danky-1998-p484-rapmasters.jpg", "danky-1998-p484-rap-masters.jpg", 484,
     "Danky entry 5049: Rap Masters: Reader's Choice, monthly, Paramus, editor Natasha Brooks-Everett. WHi Oct 1991; Mar 1992-July 1994."),
]

NOTES = {
    1: "Danky 1998 entry 1 prints the title as 2 Hype: bimonthly, River Edge, 1990?-1993, Word Up! Video, Inc., editor Marica A. Cole. ISSN 1056-4632; OCLC 23715422. WHi v.1 n.6 and v.2 n.5, Aug 1992 and Aug 1993.",
    15: "Danky 1998 entry 181: monthly, Hillside, editor Imafidou Olaye, 20 pages, OCLC 36178031. Motto \"The people's link.\" WHi Oct 1994 (Pam 96-1612).",
    26: "Danky 1998 entry 2786: three times during the school year (also bimonthly), Orange, Just Us Books, 8 pages, OCLC 25266785. \"A newspaper for young readers that focuses on the African-American experience.\" WHi 1992-1993-.",
    44: "Danky 1998 entry 2469: monthly, Somerset, editor Paula McCoy-Pinderhughes, 8 pages, OCLC 36814737. NN-Sc v.1 n.1- Feb 1996-.",
    47: "Danky 1998 entry 511: monthly, Plainfield, 1991-1993?, City News Publishing, 16 pages. Editors Lorraine Davis Hickman Mar-Sept 1992; Jan M. Edgerton-Johnson Oct 1992-Summer 1993. NN-Sc Mar 1992-Summer 1993.",
    49: "Danky 1998 entry 529: six times a year, New Brunswick, Crossroads Theatre Company, editor Ernie Johnston, 8 pages, drama. WHi v.1 n.3- Winter 1997-.",
    50: "Danky 1998 entry 4261: twice a month, Newark, Deadline Publishing Company, editor Harry B. Webber, entertainment and profiles, OCLC 35268934. WHi v.2 n.4, 30 May 1960 (Pam 96-535).",
    53: "Danky 1998 entry 3726: Piscataway, POSRO Inc., comic books, 28 pages. WHi v.1 n.1-3, July 1991-1994 (Pam 00-303).",
    54: "Danky 1998 entry 3314: quarterly, Transaction Publishers at Rutgers, New Brunswick, in collaboration with the David Walker Research Institute. Editor Gary A. Sailes; previous editor Courtland Lee. WHi Summer 1995-.",
    58: "Danky 1998 entry 6536: nine times a year, Plainfield, Yes Communications, editor Jan M. Edgenton Johnson. Motto \"The magazine of the new generation.\" WHi 1994/5-.",
    63: "Danky 1998 entry 5866: nine times a year (also bimonthly), Paramus, editor Kate Ferguson, published by John Blassingame, 98 pages, OCLC 32867618. WHi v.1 n.1- Apr 1995-.",
    138: "Danky 1998 entry 5866 is the same Paramus magazine as id 63.",
    65: "Danky 1998 entry 5578: six times a year, Plainfield, editor Natasha Munson, 16 pages, spirituality and lifestyle. NN-Sc v.1 n.2 July/Aug 1996.",
    75: "Danky 1998 entry 4216: six times a year, Newark, African-American Institute of Islamic Research, editor Zain A. Abdullah, ISSN 1054-3880. NN-Sc v.1 n.1- Jan 1991.",
    78: "Danky 1998 entry 2462: bimonthly, River Edge, Swank Publications, 82 pages. \"Premiere issue.\" WHi n.1 1993.",
    82: "Danky 1998 entry 3020: bimonthly, Paramus, Word Up! Video Productions, editor Marcia A. Cole, 66 pages, OCLC 29290682. Place also River Edge. WHi v.1 n.1- Sept 1993-.",
    85: "Danky 1998 entry 776: bimonthly, West Orange, 2 pages, OCLC 30786651. Motto \"Your link to Black authors, Black titles, and Black concerns.\" WHi v.1 n.2 Sept/Oct 1992.",
    88: "Danky 1998 entry 3378: bimonthly, Paramus, editor Kate Ferguson, publisher John Blassingame, 100 pages, ISSN 1090-3065. WHi v.1 n.2 Jan 1997.",
    92: "Danky 1998 entry 1180: quarterly, Paramus, Word Up! Video Productions, 66 pages, OCLC 30888338. WHi v.1 n.1, 3 and v.2 n.3, Summer 1994-Winter 1995.",
    93: "Danky 1998 entry 5954: bimonthly, Paramus, editor Adrienne Moore; previous editor Marcia Cole. Place also River Edge. WHi v.1 n.5- Feb 1994-.",
    112: "Danky 1998 entry 1394: Glen Ridge, 1992-1994, African Prince Productions, 32 pages, comic books, OCLC 29247918. WHi n.1, 3 June 1992 and Feb 1994.",
    114: "Danky 1998 entry 6483: monthly, Paramus, editor Kate Ferguson, publisher Scott Mitchell Figman, ISSN 1056-4691. Place also New York. WHi Nov 1991; May 1992-. NN-Sc July 1990-.",
    117: "Danky 1998 entry 3139: quarterly, Piscataway, editor Donnette Bishop Johnson, 1308 Centennial Ave.",
    125: "Danky 1998 entry 866: Paramus, Word Up! Video Productions, editor Natasha A. Brooks-Everett, 66 pages. Place also River Edge. WHi v.1 n.1- Nov 1993-.",
    135: "Danky 1998 entry 5049: monthly, Paramus, editor Natasha Brooks-Everett; previous editor Kate Ferguson. Place also River Edge. ISSN 1056-4705. WHi Oct 1991; Mar 1992-July 1994.",
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}

    for pid, src_name, dest_name, page, caption in ROWS:
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
