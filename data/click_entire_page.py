"""Click the left Entire Page card, then grab the next format step."""

from __future__ import annotations

import time
from pathlib import Path

from send_cmd import send

DEST = Path(__file__).resolve().parent / "research" / "newspapers-com" / "downloads"
DEST.mkdir(parents=True, exist_ok=True)
DOWNLOADS = Path.home() / "Downloads"


def newest(since: float):
    found = []
    for folder in (DOWNLOADS, DEST):
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.stat().st_mtime >= since - 1 and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}:
                found.append(p)
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def ev(js: str):
    return send({"action": "eval", "js": js}, timeout=30)


def main() -> None:
    send({"action": "goto", "url": "https://www.newspapers.com/image/497174278/", "wait_ms": 4000}, timeout=120)
    send({"action": "click", "selector": 'button:has-text("Print or Download")', "wait_ms": 2000}, timeout=60)
    send({"action": "screenshot", "name": "dl-panel-open.png"}, timeout=60)

    clicked = ev(
        """() => {
          const all = [...document.querySelectorAll('button, [role=button], div, span, a')];
          const leaf = all.find(e => (e.innerText || '').trim() === 'Entire Page');
          if (!leaf) return {ok:false, reason:'no leaf'};
          const card = leaf.closest('button, [role=button], a') || leaf.parentElement || leaf;
          card.click();
          return {ok:true, tag: card.tagName, className: card.className, text: (card.innerText||'').slice(0,80)};
        }"""
    )
    print("entire card", clicked.get("value"))
    time.sleep(2)
    send({"action": "screenshot", "name": "dl-after-entire-card.png"}, timeout=60)

    labels = ev(
        """() => [...document.querySelectorAll('button, a, [role=button], label, span, div')]
          .map(e => (e.innerText||'').replace(/\\s+/g,' ').trim())
          .filter(t => t && t.length < 40 && /pdf|jpe?g|png|download|print|image|high|quality/i.test(t))
          .slice(0, 20)"""
    )
    print("labels", labels.get("value"))

    before = time.time()
    for sel in (
        'button:has-text("Download")',
        'button:has-text("PDF")',
        'button:has-text("JPG")',
        'text=PDF',
        'text=JPG',
    ):
        r = send({"action": "click", "selector": sel, "wait_ms": 2000}, timeout=25)
        print("click", sel, r.get("ok"), r.get("error"))
        if r.get("ok"):
            break

    found = None
    for _ in range(24):
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
        send({"action": "screenshot", "name": "dl-no-file.png"}, timeout=60)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
