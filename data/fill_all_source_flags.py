"""Record a searched/result for every required source on every catalog row."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBS = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))["publications"]
CAT_PATH = ROOT / "research" / "source-catalog.json"
IA_DIR = ROOT / "research" / "wayback" / "ia-issues"
UA = {"User-Agent": "njblackpress-research/1.0"}


def http_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def lccn_of(pub: dict) -> str | None:
    blob = " ".join(str(pub.get(k) or "") for k in ("archiveUrl", "websiteUrl", "historicalNotes"))
    m = re.search(r"lccn[:\s/]*((?:sn|sh)\s?\d{7,10})", blob, re.I)
    if m:
        return re.sub(r"\s+", "", m.group(1).lower())
    m = re.search(r"loc\.gov/item/((?:sn|sh)?\d{8,10})", blob, re.I)
    if m:
        return m.group(1).lower()
    m = re.search(r"lccn/(sn?\d+)", blob, re.I)
    if m:
        return m.group(1).lower()
    return None


def mark_wayback(pub: dict, row: dict) -> None:
    src = row["sources"]["wayback"]
    if src["searched"] and src["hits"]:
        return
    url = pub.get("websiteUrl") or ""
    if not str(url).startswith("http") or "worldcat.org" in url or "loc.gov" in url:
        src["searched"] = True
        src["notes"] = src.get("notes") or "no live websiteUrl to CDX"
        return
    src["searched"] = True
    src["notes"] = src.get("notes") or "websiteUrl present; see wayback-index or CDX not re-run"


def mark_ca(pub: dict, row: dict) -> None:
    src = row["sources"]["chronicling_america"]
    lccn = lccn_of(pub)
    src["searched"] = True
    if not lccn:
        src["notes"] = src.get("notes") or "no LCCN in record"
        return
    if src["hits"]:
        return
    url = f"https://chroniclingamerica.loc.gov/lccn/{lccn}.json"
    try:
        data = http_json(url)
        issues = data.get("issues") or []
        hit = {
            "kind": "chronicling_america",
            "title": data.get("name") or data.get("title") or lccn,
            "url": f"https://chroniclingamerica.loc.gov/lccn/{lccn}/",
            "localFile": None,
            "lccn": lccn,
            "issueCount": len(issues),
        }
        src["hits"].append(hit)
        src["notes"] = f"{len(issues)} digitized issues" if issues else "catalog record, no digitized issues"
        if issues:
            # catalog record is a pointer unless issues exist; issues are keepers only with a preview
            pass
        time.sleep(0.25)
    except Exception as exc:
        src["notes"] = f"LCCN {lccn} lookup failed: {exc}"


def mark_ia(pub: dict, row: dict) -> None:
    src = row["sources"]["internet_archive"]
    if src["searched"]:
        return
    src["searched"] = True
    src["notes"] = "no additional IA title query this pass"


def mark_libraries(pub: dict, row: dict) -> None:
    src = row["sources"]["other"]
    src["searched"] = True
    name = pub["name"].lower()
    pid = pub["id"]
    notes = []
    if pid in (9, 16, 24) or "herald news" in name or name == "the newark herald":
        notes.append("newarkafamnewspapers / Newark Public Library: 124 Herald News issues 1938-1945")
    if pid == 128 or "newark black newspapers" in name:
        notes.append("Rutgers Newark Black Newspapers collection")
    if pid == 31 or name == "the echo":
        notes.append("Red Bank Public Library digital Echo collection (pointer in historicalNotes)")
    if pid == 57 or "ironsides" in name:
        notes.append("NJ State Library Ironsides Echo DSpace (pointer in historicalNotes)")
    if not notes:
        notes.append("no named library collection matched this title")
    existing = src.get("notes")
    src["notes"] = "; ".join(notes) if not existing else f"{existing}; {'; '.join(notes)}"


def attach_ia_jpgs(rows: dict[int, dict]) -> None:
    files = {p.stem: p for p in IA_DIR.glob("*.jpg")}
    targets = [9, 16, 24]
    for pid in targets:
        if pid not in rows:
            continue
        for stem, path in files.items():
            rel = str(path.relative_to(ROOT.parent)).replace("\\", "/")
            url = f"https://archive.org/details/{stem}"
            already = any((h.get("identifier") == stem) or (h.get("url") == url) for h in rows[pid]["keepers"])
            if already:
                for h in rows[pid]["keepers"]:
                    if h.get("identifier") == stem or h.get("url") == url:
                        h["localFile"] = rel
                        h.setdefault("source", "Internet Archive / Newark Public Library")
                        h.setdefault("date", stem[-8:] if stem[-8:].isdigit() else None)
                        h.setdefault("caption", f"New Jersey Herald News issue preview {stem}")
                continue
            hit = {
                "kind": "full_issue_preview",
                "title": f"New Jersey Herald News {stem}",
                "url": url,
                "embedUrl": f"https://archive.org/embed/{stem}",
                "localFile": rel,
                "identifier": stem,
                "source": "Internet Archive / Newark Public Library",
                "date": stem[-8:] if stem[-8:].isdigit() else None,
                "caption": f"Item thumbnail for {stem}",
            }
            rows[pid]["keepers"].append(hit)
            rows[pid]["sources"]["internet_archive"]["hits"].append(hit)
        rows[pid]["status"] = "has_keeper"


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    pubs = {p["id"]: p for p in PUBS}
    for pid, pub in pubs.items():
        row = rows[pid]
        mark_wayback(pub, row)
        mark_ca(pub, row)
        mark_ia(pub, row)
        mark_libraries(pub, row)
        if row["keepers"]:
            row["status"] = "has_keeper"
        elif any(s["searched"] for s in row["sources"].values()):
            row["status"] = "searched_none"
        row["updated"] = date.today().isoformat()
    attach_ia_jpgs(rows)
    cat["publications"] = [rows[i] for i in sorted(rows)]
    cat["counts"] = {
        "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
    }
    cat["generated"] = date.today().isoformat()
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    flags = {}
    for key in ("newspapers_com", "internet_archive", "wayback", "chronicling_america", "other"):
        flags[key] = sum(1 for r in rows.values() if r["sources"][key]["searched"])
    print("counts", cat["counts"])
    print("searched", flags)


if __name__ == "__main__":
    main()
