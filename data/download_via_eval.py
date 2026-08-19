"""Open Print or Download and click Entire Page by exact text."""

from __future__ import annotations

import time
from pathlib import Path

from send_cmd import send

DEST = Path(__file__).resolve().parent / "research" / "newspapers-com" / "downloads"
DEST.mkdir(parents=True, exist_ok=True)
DOWNLOADS = Path.home() / "Downloads"

def click_js(label: str) -> str:
    return f"""() => {{
      const want = {label!r};
      const nodes = [...document.querySelectorAll('button, a, [role=button], div, span, label')];
      const el = nodes.find(e => (e.innerText || '').replace(/\\s+/g, ' ').trim().includes(want) && (e.innerText || '').trim().length < 80);
      if (!el) return {{ok:false, want}};
      el.click();
      return {{ok:true, want, tag: el.tagName}};
    }}"""


def newest(since: float):
    found = []
    for folder in (DOWNLOADS, DEST):
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.stat().st_mtime >= since - 1 and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}:
                found.append(p)
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def click_text(label: str) -> dict:
    return send({"action": "eval", "js": click_js(label)}, timeout=30)


def main() -> None:
    send({"action": "goto", "url": "https://www.newspapers.com/image/497174278/", "wait_ms": 4000}, timeout=120)
    print("open", click_text("Print or Download"))
    time.sleep(1.5)
    print("entire", click_text("Entire Page"))
    time.sleep(2)
    send({"action": "screenshot", "name": "download-entire-clicked.png"}, timeout=60)
    before = time.time()
    for label in ("Download", "PDF", "JPG", "JPEG", "Image", "Print"):
        r = click_text(label)
        print("try", label, r.get("value"))
        if r.get("value", {}).get("ok"):
            time.sleep(2)
    found = None
    for _ in range(20):
        time.sleep(0.5)
        found = newest(before)
        if found:
            break
    if found:
        dest = DEST / f"echo-1904-entire{found.suffix.lower()}"
        dest.write_bytes(found.read_bytes())
        print("SAVED", dest, dest.stat().st_size)
    else:
        print("NO FILE")
        send({"action": "screenshot", "name": "download-final.png"}, timeout=60)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
