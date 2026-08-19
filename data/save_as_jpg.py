"""On an open Newspapers.com page: Print or Download -> Entire Page -> Save as JPG."""

from __future__ import annotations

import json
import time
from pathlib import Path

from send_cmd import send

DEST = Path(__file__).resolve().parent / "research" / "newspapers-com" / "downloads"
DEST.mkdir(parents=True, exist_ok=True)
DOWNLOADS = Path.home() / "Downloads"

PAGES = [
    ("echo-1904-fire", "https://www.newspapers.com/image/497174278/"),
    ("herbert-1893-bradley", "https://www.newspapers.com/image/1194114727/"),
    ("trumpet-1893-asbury", "https://www.newspapers.com/image/436807841/"),
    ("echo-1909-move", "https://www.newspapers.com/image/143869436/"),
    ("herbert-1895-gop", "https://www.newspapers.com/image/1194116748/"),
]


def newest(since: float):
    found = []
    for folder in (DOWNLOADS, DEST):
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.stat().st_mtime >= since - 1 and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}:
                found.append(p)
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def click_text(want: str) -> dict:
    js = f"""() => {{
      const want = {want!r};
      const nodes = [...document.querySelectorAll('button, a, [role=button], span, div')];
      const el = nodes.find(e => (e.innerText || '').replace(/\\s+/g,' ').trim() === want);
      if (!el) return {{ok:false, want}};
      const target = el.closest('button, a, [role=button]') || el;
      target.click();
      return {{ok:true, want, tag: target.tagName}};
    }}"""
    return send({"action": "eval", "js": js}, timeout=30)


def download_one(slug: str, url: str) -> dict:
    print("PAGE", slug)
    send({"action": "goto", "url": url, "wait_ms": 4000}, timeout=120)
    send({"action": "click", "selector": 'button:has-text("Print or Download")', "wait_ms": 1800}, timeout=60)
    print("  entire", click_text("Entire Page").get("value"))
    time.sleep(1.5)
    before = time.time()
    print("  jpg", click_text("Save as JPG").get("value"))
    found = None
    for _ in range(30):
        time.sleep(0.5)
        found = newest(before)
        if found:
            break
    rec = {"slug": slug, "url": url, "file": str(found) if found else None}
    if found:
        dest = DEST / f"{slug}{found.suffix.lower()}"
        dest.write_bytes(found.read_bytes())
        rec["saved"] = str(dest)
        rec["bytes"] = dest.stat().st_size
        print("  SAVED", dest, rec["bytes"])
    else:
        send({"action": "screenshot", "name": f"dl-fail-{slug}.png"}, timeout=60)
        print("  NO FILE")
    return rec


def main() -> None:
    out = [download_one(slug, url) for slug, url in PAGES]
    log = DEST / "jpg-log.json"
    log.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", log)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
