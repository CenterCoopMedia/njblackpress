"""Retry a few titles with identity captures after visual reject of blank replays."""

from __future__ import annotations

import json
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
SHOT_DIR = ROOT / "research" / "wayback" / "snapshots"
CAT_PATH = ROOT / "research" / "source-catalog.json"
SHOT_SRC = ROOT / "research" / "newspapers-com" / "screenshots"
OFFLINE_SIZE = 59084

RETRY_URLS = {
    4: "https://web.archive.org/web/20170602215358id_/http://blackinjersey.com/",
    17: "https://web.archive.org/web/20241201002842id_/https://trentonjournal.com/",
    25: "https://web.archive.org/web/20240506145430id_/https://www.atlanticcityfocus.com/",
    36: "https://web.archive.org/web/20160910125257id_/http://www.morejersey.com:80/",
    43: "https://web.archive.org/web/20220125174438id_/https://www.publicsq.org/",
}


def slug(pid: int, name: str) -> str:
    raw = f"{pid:03d}-{name.lower()}"
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:50]


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    for pid, url in RETRY_URLS.items():
        dest = SHOT_DIR / f"{slug(pid, rows[pid]['name'])}.png"
        print("SHOT", pid, url, flush=True)
        goto = send({"action": "goto", "url": url, "wait_ms": 7000}, timeout=150)
        if not goto.get("ok"):
            print("  fail", goto.get("error"), flush=True)
            continue
        send({"action": "screenshot", "name": dest.name}, timeout=90)
        src = SHOT_SRC / dest.name
        if src.exists():
            dest.write_bytes(src.read_bytes())
        if not dest.exists():
            print("  no file", flush=True)
            continue
        size = dest.stat().st_size
        print("  saved", dest.name, size, flush=True)
        if size == OFFLINE_SIZE:
            dest.unlink()
            print("  still offline; deleted", flush=True)
            continue
        rel = str(dest.relative_to(ROOT.parent)).replace("\\", "/")
        ts = "".join(ch for ch in url.split("/web/", 1)[1][:14] if ch.isdigit())[:8]
        hit = {
            "kind": "wayback_snapshot",
            "title": f"Wayback screenshot {dest.name}",
            "url": url.replace("id_/", ""),
            "localFile": rel,
            "source": "Wayback Machine",
            "date": ts,
            "caption": f"Wayback capture for {rows[pid]['name']}",
        }
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
