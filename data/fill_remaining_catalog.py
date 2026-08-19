"""Search remaining catalog rows and download IA Herald News previews."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAT_PATH = ROOT / "research" / "source-catalog.json"
IA_DIR = ROOT / "research" / "wayback" / "ia-issues"
IA_DIR.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}


def http_json(url: str, timeout: int = 40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def http_bytes(url: str, timeout: int = 40) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def ia_search(name: str) -> list[dict]:
    q = f'("{name}") AND (mediatype:texts)'
    url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode({"q": q, "rows": 3, "output": "json"})
        + "&fl[]=identifier&fl[]=title&fl[]=date"
    )
    data = http_json(url)
    return ((data.get("response") or {}).get("docs")) or []


def download_ia_thumbs(idents: list[str]) -> list[dict]:
    saved = []
    for ident in idents:
        dest = IA_DIR / f"{ident}.jpg"
        url = f"https://archive.org/services/img/{ident}"
        try:
            dest.write_bytes(http_bytes(url))
            saved.append(
                {
                    "kind": "full_issue_preview",
                    "title": ident,
                    "url": f"https://archive.org/details/{ident}",
                    "localFile": str(dest.relative_to(ROOT.parent)).replace("\\", "/"),
                    "embedUrl": f"https://archive.org/embed/{ident}",
                    "identifier": ident,
                }
            )
            print("saved", dest, dest.stat().st_size)
        except Exception as exc:
            print("thumb fail", ident, exc)
        time.sleep(0.4)
    return saved


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}

    # Download first and a mid-run Herald News preview.
    thumbs = download_ia_thumbs(
        [
            "NewJerseyHeraldNews19380521a",
            "NewarkHerald19380611a",
            "NewJerseyHeraldNews19390311",
            "NewJerseyHeraldNews19420704",
        ]
    )
    for pid in (16, 9, 24):
        if pid not in rows:
            continue
        for hit in thumbs:
            if hit["url"] not in {h.get("url") for h in rows[pid]["keepers"]}:
                rows[pid]["keepers"].append(hit)
            rows[pid]["sources"]["internet_archive"]["hits"].append(hit)
        rows[pid]["status"] = "has_keeper"
        rows[pid]["updated"] = date.today().isoformat()

    remaining = [r for r in rows.values() if r["status"] == "not_searched"]
    print("remaining", len(remaining))
    for row in remaining:
        name = row["name"].split("|")[0].strip()
        if len(name) < 4:
            row["sources"]["internet_archive"]["searched"] = True
            row["sources"]["internet_archive"]["notes"] = "name too short for IA query"
            row["status"] = "searched_none"
            continue
        print("IA", row["id"], name)
        try:
            docs = ia_search(name)
            row["sources"]["internet_archive"]["searched"] = True
            for d in docs:
                ident = d.get("identifier")
                row["sources"]["internet_archive"]["hits"].append(
                    {
                        "kind": "internet_archive_candidate",
                        "title": d.get("title") or ident,
                        "url": f"https://archive.org/details/{ident}" if ident else None,
                        "localFile": None,
                        "date": d.get("date"),
                        "identifier": ident,
                    }
                )
            if not docs:
                row["sources"]["internet_archive"]["notes"] = "no IA texts match"
            row["status"] = "searched_none"
        except Exception as exc:
            row["sources"]["internet_archive"]["searched"] = True
            row["sources"]["internet_archive"]["notes"] = str(exc)
            row["status"] = "searched_none"
        row["updated"] = date.today().isoformat()
        time.sleep(0.45)

    cat["publications"] = [rows[i] for i in sorted(rows)]
    cat["counts"] = {
        "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
    }
    cat["generated"] = date.today().isoformat()
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("counts", cat["counts"])


if __name__ == "__main__":
    main()
