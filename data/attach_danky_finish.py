"""Finish Danky attach: Berlin from p.131, clean Hiram notes, add Cooper city fact."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DANKY = ROOT / "data" / "research" / "danky"
CAT = ROOT / "data" / "research" / "source-catalog.json"
PUBS = ROOT / "data" / "publications.json"
CLIP_CAT = ROOT / "data" / "research" / "newspapers-com" / "clips" / "catalog.json"


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    by_pub = {p["id"]: p for p in pubs["publications"]}

    src = DANKY / "danky-1998-p131-camden-news.png"
    dest = DANKY / "danky-1998-p131-camp-berlin-broadcast.png"
    if not src.exists():
        raise SystemExit(f"missing {src}")
    dest.write_bytes(src.read_bytes())
    rel = str(dest.relative_to(ROOT)).replace("\\", "/")
    url = "https://archive.org/details/africanamericanne00dank/page/131/mode/1up"
    hit = {
        "kind": "catalog_record",
        "title": "Danky and Hady 1998 entry 1356, Camp Berlin Broadcast",
        "url": url,
        "localFile": rel,
        "source": "Danky and Hady 1998 / Internet Archive",
        "date": "1998",
        "caption": "Danky p.131: Camp Berlin Broadcast, 1934?-1935, irregular, Berlin NJ, Company 1275-C, last issue 8 pages.",
    }
    row = rows[102]
    if not any(h.get("localFile") == rel for h in row["keepers"]):
        row["keepers"].append(hit)
    row["status"] = "has_keeper"
    other = row["sources"]["other"]
    other["searched"] = True
    if not any(h.get("url") == url and "1356" in (h.get("title") or "") for h in other.get("hits") or []):
        other.setdefault("hits", []).append(hit)
    note = other.get("notes") or ""
    extra = "Danky 1998 entry 1356 on p.131"
    if extra not in note:
        other["notes"] = (note + "; " + extra).strip("; ")

    berlin = by_pub[102]
    add = (
        " Danky and Hady 1998 entry 1356: irregular, 1934?-1935, Berlin NJ, Company 1275-C, "
        "last issue examined 8 pages. Same Danky page as Camden News and Camp Cooper Chats."
    )
    if "entry 1356" not in (berlin.get("historicalNotes") or ""):
        berlin["historicalNotes"] = (berlin.get("historicalNotes") or "") + add

    hiram = by_pub[79]
    hiram["historicalNotes"] = (
        "Danky and Hady 1998 entry 2907: biweekly community newsletter of King Hiram's "
        "Craftsmen Center, Vauxhall, NJ; 4 pages; editor Ada Smith. Howard University (DHU) "
        "holds v.5 n.11-13, 15-16, 18 (12-36 July, 16-23 Aug, and 18 Oct 1951). Vauxhall is "
        "in Union Township, Union County. The name points to Prince Hall / Hiram lodge life."
    )
    hiram["isActive"] = False

    cooper = by_pub[87]
    add_c = (
        " Danky 1998 entry 1359 places the paper in Haddonfield, NJ (Company 1275-C), last issue "
        "15 pages, CRL microform 1935-1937, WHi holdings Dec 1935-Dec 1936."
    )
    if "entry 1359" not in (cooper.get("historicalNotes") or ""):
        cooper["historicalNotes"] = (cooper.get("historicalNotes") or "") + add_c

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
