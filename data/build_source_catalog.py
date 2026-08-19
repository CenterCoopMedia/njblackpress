"""Build data/research/source-catalog.json for every publication."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT / "research"
PUBS_PATH = ROOT / "publications.json"
OUT_PATH = RESEARCH / "source-catalog.json"
CLIPS = RESEARCH / "newspapers-com" / "clips"
WAYBACK_INDEX = RESEARCH / "wayback" / "wayback-index.json"
NP_CLIPS = RESEARCH / "newspapers-com" / "clips" / "catalog.json"

UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}


def http_json(url: str, timeout: int = 40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def empty_sources() -> dict:
    return {
        "newspapers_com": {"searched": False, "hits": [], "notes": None},
        "internet_archive": {"searched": False, "hits": [], "notes": None},
        "wayback": {"searched": False, "hits": [], "notes": None},
        "chronicling_america": {"searched": False, "hits": [], "notes": None},
        "other": {"searched": False, "hits": [], "notes": None},
    }


def lccn_from(pub: dict) -> str | None:
    blob = " ".join(
        str(pub.get(k) or "")
        for k in ("archiveUrl", "websiteUrl", "historicalNotes")
    )
    m = re.search(r"lccn[:\s/]*((?:sn|sh)?\s?\d{7,10})", blob, re.I)
    if not m:
        m = re.search(r"lccn/(sn?\d+)", blob, re.I)
    if not m:
        return None
    return re.sub(r"\s+", "", m.group(1).lower())


def load_pubs() -> list[dict]:
    return json.loads(PUBS_PATH.read_text(encoding="utf-8"))["publications"]


def merge_np_clips(rows: dict[int, dict]) -> None:
    if not NP_CLIPS.exists():
        return
    data = json.loads(NP_CLIPS.read_text(encoding="utf-8"))
    clip_dir = CLIPS
    for clip in data.get("clips", []):
        pid = clip.get("aboutId")
        if pid not in rows:
            continue
        local = clip_dir / clip["localImage"]
        hit = {
            "kind": "clipping",
            "title": f"{clip['sourcePaper']}, {clip['date']}",
            "url": clip["url"],
            "localFile": str(local.relative_to(ROOT.parent)) if local.exists() else None,
            "quote": clip.get("quote"),
            "source": clip.get("sourcePaper"),
            "date": clip.get("date"),
            "city": clip.get("sourceCity"),
        }
        src = rows[pid]["sources"]["newspapers_com"]
        src["searched"] = True
        src["hits"].append(hit)
        rows[pid]["keepers"].append(hit)
        rows[pid]["status"] = "has_keeper"


def merge_wayback(rows: dict[int, dict]) -> None:
    if not WAYBACK_INDEX.exists():
        return
    data = json.loads(WAYBACK_INDEX.read_text(encoding="utf-8"))
    for site in data.get("sites", []):
        pid = site.get("id")
        if pid not in rows:
            continue
        src = rows[pid]["sources"]["wayback"]
        src["searched"] = True
        if site.get("error"):
            src["notes"] = site["error"]
            continue
        for label, url in (
            ("earliest", site.get("wayback_first")),
            ("latest", site.get("wayback_last")),
        ):
            if not url:
                continue
            hit = {
                "kind": "wayback_snapshot",
                "title": f"{label} snapshot of {site.get('host')}",
                "url": url,
                "localFile": None,
                "timestamp": (site.get("first") if label == "earliest" else site.get("last") or {}).get("timestamp"),
            }
            src["hits"].append(hit)
            rows[pid]["keepers"].append(hit)
            if rows[pid]["status"] == "not_searched":
                rows[pid]["status"] = "has_keeper"
            elif rows[pid]["status"] == "searched_none":
                rows[pid]["status"] = "has_keeper"


def merge_existing_http_pointers(pub: dict, row: dict) -> None:
    for field, source_key, kind in (
        ("websiteUrl", "other", "website"),
        ("archiveUrl", "other", "catalog_or_archive"),
    ):
        url = pub.get(field)
        if not url or not str(url).startswith("http"):
            continue
        row["sources"][source_key]["searched"] = True
        row["sources"][source_key]["hits"].append(
            {"kind": kind, "title": field, "url": url, "localFile": None}
        )


def search_chronicling(pub: dict, row: dict) -> None:
    lccn = lccn_from(pub)
    src = row["sources"]["chronicling_america"]
    src["searched"] = True
    if not lccn:
        src["notes"] = "no LCCN in record"
        return
    url = f"https://chroniclingamerica.loc.gov/lccn/{lccn}.json"
    try:
        data = http_json(url)
    except Exception as exc:
        src["notes"] = f"lookup failed for {lccn}: {exc}"
        return
    issues = data.get("issues") or []
    hit = {
        "kind": "chronicling_america",
        "title": data.get("title") or lccn,
        "url": f"https://chroniclingamerica.loc.gov/lccn/{lccn}/",
        "localFile": None,
        "lccn": lccn,
        "issueCount": len(issues),
        "place": (data.get("place") or [None])[0] if isinstance(data.get("place"), list) else data.get("place"),
    }
    src["hits"].append(hit)
    if issues:
        row["keepers"].append(hit)
        row["status"] = "has_keeper"
    else:
        src["notes"] = "catalog record, no digitized issues on Chronicling America"


def search_ia_title(pub: dict, row: dict) -> None:
    src = row["sources"]["internet_archive"]
    src["searched"] = True
    name = pub["name"].split("/")[0].strip()
    q = f'title:("{name}") AND (collection:newarkafamnewspapers OR subject:Newspapers)'
    url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode({"q": q, "rows": 5, "output": "json"})
        + "&fl[]=identifier&fl[]=title&fl[]=date&fl[]=collection"
    )
    try:
        data = http_json(url)
    except Exception as exc:
        src["notes"] = str(exc)
        return
    docs = ((data.get("response") or {}).get("docs")) or []
    for d in docs:
        ident = d.get("identifier")
        hit = {
            "kind": "internet_archive_item",
            "title": d.get("title") or ident,
            "url": f"https://archive.org/details/{ident}" if ident else None,
            "localFile": None,
            "date": d.get("date"),
            "identifier": ident,
        }
        src["hits"].append(hit)
        # Only treat newarkafamnewspapers (or a tight title match) as a keeper.
        collections = d.get("collection") or []
        if isinstance(collections, str):
            collections = [collections]
        if "newarkafamnewspapers" in collections:
            row["keepers"].append(hit)
            row["status"] = "has_keeper"


def fetch_ia_collection_hits() -> list[dict]:
    url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode(
            {"q": "collection:newarkafamnewspapers", "rows": 200, "output": "json", "sort[]": "date asc"}
        )
        + "&fl[]=identifier&fl[]=title&fl[]=date"
    )
    data = http_json(url)
    return ((data.get("response") or {}).get("docs")) or []


def attach_herald_news(rows: dict[int, dict], docs: list[dict]) -> None:
    # New Jersey Herald News is id 16; Newark Herald 9 and 24 are related.
    targets = [16, 9, 24]
    for pid in targets:
        if pid not in rows:
            continue
        src = rows[pid]["sources"]["internet_archive"]
        src["searched"] = True
        src["notes"] = f"{len(docs)} items in collection newarkafamnewspapers"
        for d in docs[:8]:
            ident = d.get("identifier")
            hit = {
                "kind": "full_issue",
                "title": d.get("title") or ident,
                "url": f"https://archive.org/details/{ident}",
                "localFile": None,
                "date": d.get("date"),
                "identifier": ident,
                "embedUrl": f"https://archive.org/embed/{ident}",
            }
            src["hits"].append(hit)
            rows[pid]["keepers"].append(hit)
        rows[pid]["status"] = "has_keeper"


def mark_np_searched_none(row: dict) -> None:
    # Titles we already ran NJ newspapers.com queries for without a keeper.
    src = row["sources"]["newspapers_com"]
    if src["searched"]:
        return
    src["searched"] = True
    src["notes"] = "included in NJ-only Newspapers.com passes; no in-state keeper saved yet"


def build() -> dict:
    pubs = load_pubs()
    rows: dict[int, dict] = {}
    for pub in pubs:
        pid = pub["id"]
        row = {
            "id": pid,
            "name": pub["name"],
            "city": pub.get("city"),
            "yearFounded": pub.get("yearFounded"),
            "yearCeased": pub.get("yearCeased"),
            "status": "not_searched",
            "sources": empty_sources(),
            "keepers": [],
            "updated": date.today().isoformat(),
        }
        merge_existing_http_pointers(pub, row)
        rows[pid] = row

    merge_np_clips(rows)
    merge_wayback(rows)

    # Known NJ newspapers.com search pass titles even if no keeper file.
    searched_np = {10, 31, 38, 9, 16, 35, 37}
    for pid in searched_np:
        if pid in rows:
            mark_np_searched_none(rows[pid]) if not rows[pid]["sources"]["newspapers_com"]["hits"] else None
            rows[pid]["sources"]["newspapers_com"]["searched"] = True

    print("IA collection")
    try:
        docs = fetch_ia_collection_hits()
        print(" ", len(docs), "herald-news items")
        attach_herald_news(rows, docs)
    except Exception as exc:
        print("  IA collection failed", exc)

    # Chronicling America for records that have an LCCN-like string.
    for pub in pubs:
        blob = " ".join(str(pub.get(k) or "") for k in ("archiveUrl", "websiteUrl", "historicalNotes"))
        if "lccn" in blob.lower() or "chronicling" in blob.lower() or "loc.gov/item" in blob.lower():
            print("CA", pub["id"], pub["name"])
            search_chronicling(pub, rows[pub["id"]])
            time.sleep(0.35)

    # Targeted IA title search for oldest newspapers still without IA hits.
    oldest = sorted(
        [p for p in pubs if (p.get("yearFounded") or 9999) <= 1950],
        key=lambda p: p.get("yearFounded") or 9999,
    )
    for pub in oldest[:25]:
        row = rows[pub["id"]]
        if row["sources"]["internet_archive"]["hits"]:
            continue
        print("IA title", pub["name"])
        search_ia_title(pub, row)
        time.sleep(0.6)

    # Status cleanup.
    for row in rows.values():
        searched_any = any(s["searched"] for s in row["sources"].values())
        if row["keepers"]:
            row["status"] = "has_keeper"
        elif searched_any:
            row["status"] = "searched_none"
        else:
            row["status"] = "not_searched"

    catalog = {
        "generated": date.today().isoformat(),
        "goal": "Archival record for every NJ Black press title",
        "publicationCount": len(rows),
        "counts": {
            "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
            "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
            "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
        },
        "publications": [rows[i] for i in sorted(rows)],
    }
    OUT_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT_PATH)
    print("counts", catalog["counts"])
    return catalog


if __name__ == "__main__":
    build()
