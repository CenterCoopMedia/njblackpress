"""Second pass: mid-period or identity Wayback captures still missing a real PNG."""

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
    23: "https://web.archive.org/web/20141018093931id_/http://thenewarktimes.com:80/",
    25: "https://web.archive.org/web/20230517160636id_/https://www.atlanticcityfocus.com/",
    29: "https://web.archive.org/web/20151025031224id_/http://www.faithfullymagazine.com:80/",
    36: "https://web.archive.org/web/20160910125257/http://www.morejersey.com:80/",
    84: "https://web.archive.org/web/20200118211629id_/https://www.marxists.org/history/erol/periodicals/unity-struggle/index.htm",
    128: "https://web.archive.org/web/20190419185835id_/https://collections.libraries.rutgers.edu/",
}


def slug(pid: int, name: str) -> str:
    raw = f"{pid:03d}-{name.lower()}"
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:50]


def main() -> None:
    for p in SHOT_DIR.glob("*.png"):
        if p.stat().st_size == OFFLINE_SIZE:
            print("remove offline", p.name)
            p.unlink()

    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}

    for pid, url in RETRY_URLS.items():
        name = rows[pid]["name"]
        dest = SHOT_DIR / f"{slug(pid, name)}.png"
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
        ts = None
        if "/web/" in url:
            ts = "".join(ch for ch in url.split("/web/", 1)[1][:14] if ch.isdigit())[:8]
        hit = {
            "kind": "wayback_snapshot",
            "title": f"Wayback screenshot {dest.name}",
            "url": url.replace("id_/", ""),
            "localFile": rel,
            "source": "Wayback Machine",
            "date": ts,
            "caption": f"Wayback capture for {name}",
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
