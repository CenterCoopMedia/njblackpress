"""Click Print or Download -> Entire Page and save the file."""

from __future__ import annotations

import json
import time
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "research" / "newspapers-com" / "downloads"
DEST.mkdir(parents=True, exist_ok=True)
DOWNLOADS = Path.home() / "Downloads"


def newest(since: float) -> Path | None:
    found = []
    for folder in (DOWNLOADS, DEST):
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.stat().st_mtime >= since - 1 and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}:
                found.append(p)
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def inspect() -> dict:
    return send(
        {
            "action": "eval",
            "js": """() => [...document.querySelectorAll('button, a, [role=button], label, div')].map(el => ({
                text: (el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,90)
            })).filter(x => x.text && /entire page|portion|pdf|jpe?g|download|print|png/i.test(x.text)).slice(0,25)""",
        },
        timeout=60,
    )


def main() -> None:
    url = "https://www.newspapers.com/image/497174278/"
    send({"action": "goto", "url": url, "wait_ms": 4000}, timeout=120)
    send(
        {"action": "click", "selector": 'button:has-text("Print or Download")', "wait_ms": 2000},
        timeout=60,
    )
    print("after open", inspect().get("value"))
    send({"action": "click", "selector": 'text=Entire Page', "wait_ms": 2500}, timeout=60)
    print("after entire", inspect().get("value"))
    send({"action": "screenshot", "name": "download-after-entire.png"}, timeout=60)
    before = time.time()
    for sel in (
        'button:has-text("PDF")',
        'button:has-text("JPG")',
        'button:has-text("JPEG")',
        'button:has-text("Download")',
        'a:has-text("PDF")',
        'a:has-text("JPG")',
    ):
        r = send({"action": "click", "selector": sel, "wait_ms": 2000}, timeout=30)
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
        send({"action": "screenshot", "name": "download-after-format.png"}, timeout=60)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
