"""Live-site screenshots when Wayback replay will not load the page."""

from __future__ import annotations

import json
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
SHOT_DIR = ROOT / "research" / "wayback" / "snapshots"
CAT_PATH = ROOT / "research" / "source-catalog.json"
SHOT_SRC = ROOT / "research" / "newspapers-com" / "screenshots"
OFFLINE_SIZE = 59084

LIVE = {
    4: "https://www.blackinjersey.com/",
    17: "https://trentonjournal.com/",
    36: "https://morejersey.com/",
    43: "https://www.publicsq.org/",
}


def slug(pid: int, name: str) -> str:
    raw = f"{pid:03d}-{name.lower()}"
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:50]


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    for pid, url in LIVE.items():
        dest = SHOT_DIR / f"{slug(pid, rows[pid]['name'])}.png"
        print("LIVE", pid, url, flush=True)
        goto = send({"action": "goto", "url": url, "wait_ms": 6000}, timeout=120)
        if not goto.get("ok"):
            print("  fail", goto.get("error"), flush=True)
            continue
        send({"action": "screenshot", "name": dest.name}, timeout=90)
        src = SHOT_SRC / dest.name
        if src.exists():
            dest.write_bytes(src.read_bytes())
        if not dest.exists() or dest.stat().st_size in (OFFLINE_SIZE, 7758):
            print("  bad file", dest.exists() and dest.stat().st_size, flush=True)
            if dest.exists() and dest.stat().st_size in (OFFLINE_SIZE, 7758):
                dest.unlink()
            continue
        print("  saved", dest.name, dest.stat().st_size, flush=True)
        rel = str(dest.relative_to(ROOT.parent)).replace("\\", "/")
        hit = {
            "kind": "website_screenshot",
            "title": f"live site screenshot {dest.name}",
            "url": url,
            "localFile": rel,
            "source": "live website",
            "date": "2026-08-17",
            "caption": f"Live site screenshot of {rows[pid]['name']} after Wayback replay failed",
        }
        if not any(h.get("localFile") == rel for h in rows[pid]["keepers"]):
            rows[pid]["keepers"].append(hit)
        rows[pid]["status"] = "has_keeper"
        rows[pid]["sources"]["wayback"]["searched"] = True
        note = rows[pid]["sources"]["wayback"].get("notes") or ""
        extra = "Wayback replay failed; live site screenshot saved 2026-08-17"
        if extra not in note:
            rows[pid]["sources"]["wayback"]["notes"] = (note + "; " + extra).strip("; ")
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
