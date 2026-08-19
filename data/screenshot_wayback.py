"""Screenshot earliest Wayback snapshots through the open Chrome daemon."""

from __future__ import annotations

import json
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
CAT_PATH = ROOT / "research" / "source-catalog.json"
SHOT_DIR = ROOT / "research" / "wayback" / "snapshots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    seen = set()
    for row in cat["publications"]:
        earliest = None
        for hit in row.get("keepers", []):
            if hit.get("kind") != "wayback_snapshot":
                continue
            if hit.get("localFile") and Path(hit["localFile"]).exists():
                continue
            title = hit.get("title") or ""
            if title.startswith("earliest"):
                earliest = hit
                break
            if earliest is None:
                earliest = hit
        if not earliest or not earliest.get("url"):
            continue
        url = earliest["url"]
        if url in seen:
            continue
        seen.add(url)
        slug = f"{row['id']:03d}-{row['name'].lower().replace(' ', '-')[:40]}"
        slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in slug)
        print("SHOT", row["id"], url)
        goto = send({"action": "goto", "url": url, "wait_ms": 5000}, timeout=120)
        if not goto.get("ok"):
            print("  goto fail", goto)
            continue
        name = f"{slug}.png"
        shot = send({"action": "screenshot", "name": name}, timeout=90)
        # send_cmd screenshot writes to newspapers-com/screenshots; move/copy
        src = ROOT / "research" / "newspapers-com" / "screenshots" / name
        dest = SHOT_DIR / name
        if src.exists():
            dest.write_bytes(src.read_bytes())
        elif shot.get("path") and Path(shot["path"]).exists():
            dest.write_bytes(Path(shot["path"]).read_bytes())
        if dest.exists():
            rel = str(dest.relative_to(ROOT.parent)).replace("\\", "/")
            earliest["localFile"] = rel
            print("  saved", dest, dest.stat().st_size)
        else:
            print("  no file", shot)

    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("done; chrome left open")


if __name__ == "__main__":
    main()
