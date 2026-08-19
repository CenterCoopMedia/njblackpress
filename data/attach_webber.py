"""Attach Harry B. Webber After Hours obit and write staff facts."""

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

KEEPER = {
    "id": 101,
    "clip_id": "after-hours-1991-courier-news-webber",
    "src": "q7f-webber-1991-06-24-courier.png",
    "dest": "after-hours-1991-06-24-courier-news-webber-obit.png",
    "source": "The Courier-News",
    "sourceCity": "Bridgewater, New Jersey",
    "date": "1991-06-24",
    "page": "8",
    "url": "https://www.newspapers.com/image/223216862/",
    "caption": "AP obit: Harry B. Webber, city editor of the New Jersey Herald News, then editor and publisher of After Hours, a Newark magazine, in the 1940s.",
    "quote": "Webber, a longtime Newark resident, served as city editor of the New Jersey Herald News for several years before becoming editor and publisher of \"After Hours,\" a Newark magazine, in the 1940s. He wrote the social and political column \"Jersey Happenings,\" which appeared in the Afro American.",
}

NONE_NOTES = {
    7: "Henry J. Auston quoted search: only NJ card was 1991 Star-Ledger health-center funding, not the 1909 Citizen editor.",
    45: '"Apex News" 1929-1941 first page had 0 NJ cards. Apex Publishing hits were 1997 Courier-Post, not the 1929-1940 paper.',
    79: '"Star-News" Vauxhall 1945-1965: 0 NJ cards on first page.',
    136: '"Penn Crusader" 1935-1941: 0 NJ cards.',
    102: "Camp Berlin plus Broadcast/newspaper/CCC opened 1935 Evening Courier; highlight was a Berlin Bears baseball item, not the camp paper.",
    90: '"Little Ease Echo" returned 1 match and 0 NJ cards.',
    94: '"Dias Creek Echo" returned no result cards.',
    48: '"Ash Can" plus CCC/Chatsworth opened 1934 Courier-Post; the hit was a ballot coupon found in an ash can, not the camp paper.',
}


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}
    clip_doc = json.loads(CLIP_CAT.read_text(encoding="utf-8"))
    seen = {c["id"] for c in clip_doc["clips"]}

    src = SHOTS / KEEPER["src"]
    dest = CLIPS / KEEPER["dest"]
    if not src.exists():
        raise SystemExit(f"missing {src}")
    dest.write_bytes(src.read_bytes())
    rel = str(dest.relative_to(ROOT)).replace("\\", "/")
    hit = {
        "kind": "clip",
        "title": KEEPER["caption"],
        "url": KEEPER["url"],
        "localFile": rel,
        "source": KEEPER["source"],
        "date": KEEPER["date"],
        "caption": KEEPER["caption"],
    }
    row = rows[KEEPER["id"]]
    if not any(h.get("url") == KEEPER["url"] for h in row["keepers"]):
        row["keepers"].append(hit)
    row["status"] = "has_keeper"
    np = row["sources"]["newspapers_com"]
    np["searched"] = True
    if not any(h.get("url") == KEEPER["url"] for h in np.get("hits") or []):
        np.setdefault("hits", []).append(hit)
    if KEEPER["clip_id"] not in seen:
        clip_doc["clips"].append(
            {
                "id": KEEPER["clip_id"],
                "about": row["name"],
                "aboutId": KEEPER["id"],
                "sourcePaper": KEEPER["source"],
                "sourceCity": KEEPER["sourceCity"],
                "date": KEEPER["date"],
                "page": KEEPER["page"],
                "url": KEEPER["url"],
                "localImage": KEEPER["dest"],
                "quote": KEEPER["quote"],
                "why": KEEPER["caption"],
            }
        )

    for pid, note in NONE_NOTES.items():
        np = rows[pid]["sources"]["newspapers_com"]
        np["searched"] = True
        old = np.get("notes") or ""
        if note[:28] not in old:
            np["notes"] = (old + "; " + note).strip("; ")

    ah = by_pub[101]
    ah["historicalNotes"] = (
        "Courier-News 24 June 1991 (AP): Harry B. Webber, 90, died Friday at St. Michael's "
        "Medical Center in Newark. He was city editor of the New Jersey Herald News for several "
        "years, then editor and publisher of After Hours, a Newark magazine, in the 1940s. He "
        "wrote the column Jersey Happenings in the Afro-American. He started in circulation at "
        "the Pittsburgh Courier and the Afro American of Newark, graduated from the University "
        "of Pittsburgh, and moved to Newark in 1928. Born Williamsport, Pa."
    )
    ah["keyStaff"] = "Editor and publisher (1940s): Harry B. Webber"

    hn = by_pub[16]
    extra_hn = (
        " Courier-News 24 June 1991: Harry B. Webber served as city editor of the New Jersey "
        "Herald News for several years before launching After Hours."
    )
    if "Harry B. Webber" not in (hn.get("historicalNotes") or ""):
        hn["historicalNotes"] = (hn.get("historicalNotes") or "") + extra_hn
    if "Harry B. Webber" not in (hn.get("keyStaff") or ""):
        hn["keyStaff"] = (hn.get("keyStaff") or "") + " City editor: Harry B. Webber."

    af = by_pub[35]
    extra_af = (
        " Courier-News 24 June 1991: Harry B. Webber started in the circulation department of "
        "the Afro American of Newark and later wrote the column Jersey Happenings for the Afro-American."
    )
    if "Jersey Happenings" not in (af.get("historicalNotes") or ""):
        af["historicalNotes"] = (af.get("historicalNotes") or "") + extra_af

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
