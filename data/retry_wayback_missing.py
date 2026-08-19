"""Capture the four Wayback titles that still have no real local preview."""

from __future__ import annotations

import json
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
SHOT_DIR = ROOT / "research" / "wayback" / "snapshots"
CAT_PATH = ROOT / "research" / "source-catalog.json"
SHOT_SRC = ROOT / "research" / "newspapers-com" / "screenshots"
OFFLINE_SIZE = 59084

# Later identity captures. Earliest replay was blank or Temporarily Offline.
RETRY = {
    4: [
        "https://web.archive.org/web/20140904121434id_/http://blackinjersey.com:80/",
        "https://web.archive.org/web/20211218184219id_/https://www.blackinjersey.com/",
    ],
    17: [
        "https://web.archive.org/web/20220310152024id_/https://trentonjournal.com/",
        "https://web.archive.org/web/20210111152414id_/http://www.trentonjournal.com/",
    ],
    36: [
        "https://web.archive.org/web/20220311212943id_/https://morejersey.com/",
        "https://web.archive.org/web/20161114083457id_/http://www.morejersey.com:80/",
    ],
    43: [
        "https://web.archive.org/web/20211118213347id_/https://www.publicsq.org/",
        "https://web.archive.org/web/20220502164047id_/https://www.publicsq.org/",
    ],
}


def slug(pid: int, name: str) -> str:
    raw = f"{pid:03d}-{name.lower()}"
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:50]


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    for pid, urls in RETRY.items():
        dest = SHOT_DIR / f"{slug(pid, rows[pid]['name'])}.png"
        saved = None
        used = None
        for url in urls:
            print("SHOT", pid, url, flush=True)
            goto = send({"action": "goto", "url": url, "wait_ms": 7000}, timeout=150)
            if not goto.get("ok"):
                print("  fail", goto.get("error"), flush=True)
                continue
            send({"action": "screenshot", "name": dest.name}, timeout=90)
            src = SHOT_SRC / dest.name
            if src.exists():
                dest.write_bytes(src.read_bytes())
            if dest.exists() and dest.stat().st_size != OFFLINE_SIZE:
                saved = dest
                used = url
                print("  saved", dest.name, dest.stat().st_size, flush=True)
                break
            if dest.exists():
                dest.unlink()
                print("  offline interstitial", flush=True)
        if not saved:
            print("  no real preview", pid, flush=True)
            continue
        rel = str(saved.relative_to(ROOT.parent)).replace("\\", "/")
        ts = "".join(ch for ch in used.split("/web/", 1)[1][:14] if ch.isdigit())[:8]
        share = used.replace("id_/", "")
        hit = {
            "kind": "wayback_snapshot",
            "title": f"Wayback screenshot {saved.name}",
            "url": share,
            "localFile": rel,
            "source": "Wayback Machine",
            "date": ts,
            "caption": f"Wayback capture for {rows[pid]['name']}",
        }
        wb = rows[pid]["sources"]["wayback"]
        wb["searched"] = True
        if wb.get("hits"):
            if not wb["hits"][0].get("localFile"):
                wb["hits"][0]["localFile"] = rel
        if not any(h.get("localFile") == rel for h in rows[pid]["keepers"]):
            rows[pid]["keepers"].append(hit)
        rows[pid]["status"] = "has_keeper"
    cat["publications"] = [rows[i] for i in sorted(rows)]
    cat["counts"] = {
        "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
    }
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("counts", cat["counts"], flush=True)
    print("done; chrome left open", flush=True)


if __name__ == "__main__":
    main()
