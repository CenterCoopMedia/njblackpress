"""Screenshot earliest Wayback captures still missing a local PNG."""

from __future__ import annotations

import json
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "research" / "wayback" / "wayback-index.json"
SHOT_DIR = ROOT / "research" / "wayback" / "snapshots"
CAT_PATH = ROOT / "research" / "source-catalog.json"
SHOT_DIR.mkdir(parents=True, exist_ok=True)


def slug(pid: int, name: str) -> str:
    raw = f"{pid:03d}-{name.lower()}"
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw)[:50]


def main() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    existing = {p.stem.split("-", 1)[0] for p in SHOT_DIR.glob("*.png")}

    for site in index.get("sites", []):
        pid = site.get("id")
        url = site.get("wayback_first")
        if not pid or not url:
            continue
        key = f"{pid:03d}"
        dest = SHOT_DIR / f"{slug(pid, site.get('name') or 'site')}.png"
        if key in existing or dest.exists():
            print("skip existing", pid)
            continue
        print("SHOT", pid, url)
        goto = send({"action": "goto", "url": url, "wait_ms": 5500}, timeout=120)
        if not goto.get("ok"):
            print("  fail", goto.get("error"))
            continue
        name = dest.name
        send({"action": "screenshot", "name": name}, timeout=90)
        src = ROOT / "research" / "newspapers-com" / "screenshots" / name
        if src.exists():
            dest.write_bytes(src.read_bytes())
        if dest.exists() and pid in rows:
            rel = str(dest.relative_to(ROOT.parent)).replace("\\", "/")
            # attach to earliest wayback hit and keeper
            hit = {
                "kind": "wayback_snapshot",
                "title": f"earliest Wayback screenshot {dest.name}",
                "url": url,
                "localFile": rel,
                "source": "Wayback Machine",
                "date": (site.get("first") or {}).get("timestamp", "")[:8] or None,
                "caption": f"Earliest Wayback capture of {site.get('host')}",
            }
            rows[pid]["sources"]["wayback"]["searched"] = True
            # replace earliest hit localFile if present
            for h in rows[pid]["sources"]["wayback"]["hits"]:
                if (h.get("title") or "").startswith("earliest"):
                    h["localFile"] = rel
            if not any(h.get("localFile") == rel for h in rows[pid]["keepers"]):
                rows[pid]["keepers"].append(hit)
            rows[pid]["status"] = "has_keeper"
            print("  saved", dest, dest.stat().st_size)

    cat["publications"] = [rows[i] for i in sorted(rows)]
    cat["counts"] = {
        "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
    }
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("done; chrome left open")


if __name__ == "__main__":
    main()
