"""One page: open panel, click Entire Page card, click Save as JPG."""

from __future__ import annotations

import time
from pathlib import Path

from send_cmd import send

DEST = Path(__file__).resolve().parent / "research" / "newspapers-com" / "downloads"
DEST.mkdir(parents=True, exist_ok=True)
DOWNLOADS = Path.home() / "Downloads"

CLICK_EXACT = """() => {
  const want = %r;
  const all = [...document.querySelectorAll('button, [role=button], div, span, a, label')];
  const leaf = all.find(e => (e.innerText || '').trim() === want);
  if (!leaf) {
    const loose = all.filter(e => (e.innerText || '').includes(want)).slice(0, 5).map(e => (e.innerText||'').slice(0,60));
    return {ok:false, want, loose};
  }
  const card = leaf.closest('button, [role=button], a') || leaf;
  card.click();
  return {ok:true, want, tag: card.tagName, text: (card.innerText||'').slice(0,80)};
}"""


def newest(since: float):
    found = []
    for folder in (DOWNLOADS, DEST):
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.stat().st_mtime >= since - 1 and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}:
                found.append(p)
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def click_exact(want: str) -> dict:
    return send({"action": "eval", "js": CLICK_EXACT % want}, timeout=30)


def main() -> None:
    send({"action": "goto", "url": "https://www.newspapers.com/image/497174278/", "wait_ms": 4500}, timeout=120)
    r = send({"action": "click", "selector": 'button[title="Print or Download"]', "wait_ms": 2500}, timeout=60)
    print("panel", r.get("ok"), r.get("error"))
    print("entire", click_exact("Entire Page"))
    time.sleep(2)
    send({"action": "screenshot", "name": "dl-step2.png"}, timeout=60)
    before = time.time()
    print("jpg", click_exact("Save as JPG"))
    found = None
    for _ in range(30):
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
        send({"action": "screenshot", "name": "dl-step3.png"}, timeout=60)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
