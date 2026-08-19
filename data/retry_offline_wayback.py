"""Retry Wayback titles whose earliest replay was offline or timed out."""

from __future__ import annotations

import json
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "research" / "wayback" / "wayback-index.json"
SHOT_DIR = ROOT / "research" / "wayback" / "snapshots"
CAT_PATH = ROOT / "research" / "source-catalog.json"
SHOT_SRC = ROOT / "research" / "newspapers-com" / "screenshots"
OFFLINE_SIZE = 59084

# Prefer a later, larger HTML capture. For two titles the live path is
# more specific than the host homepage CDX used on the first pass.
RETRY_URLS = {
    23: "https://web.archive.org/web/20180128223053/http://thenewarktimes.com:80/",
    25: "https://web.archive.org/web/20240506145430/https://www.atlanticcityfocus.com/",
    29: "https://web.archive.org/web/20200820225347/https://faithfullymagazine.com/",
    32: "https://web.archive.org/web/20211208013612/https://jacque-howard.com/",
    33: "https://web.archive.org/web/20210120065101/https://scarletandblack.rutgers.edu/",
    36: "https://web.archive.org/web/20250206201427/https://morejersey.com/",
    43: "https://web.archive.org/web/20241102180148/https://www.publicsq.org/",
    84: "https://web.archive.org/web/20200118211629/https://www.marxists.org/history/erol/periodicals/unity-struggle/index.htm",
    128: "https://web.archive.org/web/20220520145710/https://collections.libraries.rutgers.edu/newark-black-newspapers",
}


def slug(pid: int, name: str) -> str:
    raw = f"{pid:03d}-{name.lower()}"
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:50]


def main() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    sites = {s["id"]: s for s in index.get("sites", []) if s.get("id") is not None}
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}

    for pid, url in RETRY_URLS.items():
        site = sites.get(pid) or {}
        name = (rows.get(pid) or {}).get("name") or site.get("name") or "site"
        dest = SHOT_DIR / f"{slug(pid, name)}.png"
        if dest.exists() and dest.stat().st_size == OFFLINE_SIZE:
            dest.unlink()
            print("removed offline", dest.name)
        print("SHOT", pid, url)
        goto = send({"action": "goto", "url": url, "wait_ms": 8000}, timeout=150)
        if not goto.get("ok"):
            print("  fail", goto.get("error"))
            continue
        send({"action": "screenshot", "name": dest.name}, timeout=90)
        src = SHOT_SRC / dest.name
        if src.exists():
            dest.write_bytes(src.read_bytes())
        if not dest.exists():
            print("  no file")
            continue
        size = dest.stat().st_size
        print("  saved", dest.name, size)
        if size == OFFLINE_SIZE:
            print("  still offline interstitial; not a keeper")
            continue
        if pid not in rows:
            continue
        rel = str(dest.relative_to(ROOT.parent)).replace("\\", "/")
        ts = None
        if "/web/" in url:
            ts = url.split("/web/", 1)[1][:8]
        hit = {
            "kind": "wayback_snapshot",
            "title": f"Wayback screenshot {dest.name}",
            "url": url,
            "localFile": rel,
            "source": "Wayback Machine",
            "date": ts,
            "caption": f"Wayback capture of {site.get('host') or name}",
        }
        wb = rows[pid]["sources"]["wayback"]
        wb["searched"] = True
        if not any(h.get("localFile") == rel for h in wb.get("hits", [])):
            wb.setdefault("hits", []).append(hit)
        if not any(h.get("localFile") == rel for h in rows[pid]["keepers"]):
            rows[pid]["keepers"].append(hit)
        rows[pid]["status"] = "has_keeper" if rows[pid]["keepers"] else rows[pid]["status"]

    cat["publications"] = [rows[i] for i in sorted(rows)]
    cat["counts"] = {
        "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
    }
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("counts", cat["counts"])
    print("done; chrome left open")


if __name__ == "__main__":
    main()
