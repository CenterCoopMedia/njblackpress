"""Download a Newspapers.com page as PDF/JPG via the open Chrome session."""

from __future__ import annotations

import json
import time
from pathlib import Path

from send_cmd import send

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "research" / "newspapers-com" / "downloads"
DEST.mkdir(parents=True, exist_ok=True)
DOWNLOADS = Path.home() / "Downloads"

INSPECT = """() => {
  const nodes = [...document.querySelectorAll('button, a, [role=button], input')];
  return nodes.map(el => ({
    tag: el.tagName,
    text: (el.innerText || el.value || el.getAttribute('aria-label') || el.title || '').trim().slice(0, 80),
    aria: el.getAttribute('aria-label'),
    href: el.href || null
  })).filter(x => /download|print|pdf|jpg|jpeg|image|save|export/i.test(JSON.stringify(x))).slice(0, 30);
}"""


def newest_download(since: float) -> Path | None:
    files = []
    for folder in (DOWNLOADS, DEST):
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if p.is_file() and p.stat().st_mtime >= since - 1 and p.suffix.lower() in {".pdf", ".jpg", ".jpeg", ".png"}:
                files.append(p)
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def download_page(url: str, slug: str) -> dict:
    print("OPEN", slug, url)
    goto = send({"action": "goto", "url": url, "wait_ms": 4500}, timeout=120)
    if not goto.get("ok"):
        return {"ok": False, "error": goto, "slug": slug}
    info = send({"action": "eval", "js": INSPECT}, timeout=60)
    print("  controls", info.get("value"))
    before = time.time()
    clicked = send(
        {
            "action": "click",
            "selector": 'button:has-text("Print/Download"), [aria-label*="Download" i], [title*="Download" i], button:has-text("Download")',
            "wait_ms": 2500,
        },
        timeout=60,
    )
    print("  click download", clicked.get("ok"), clicked.get("error"))
    time.sleep(1)
    # Try common second-step buttons.
    for sel in (
        'button:has-text("Download")',
        'button:has-text("PDF")',
        'button:has-text("JPG")',
        'button:has-text("JPEG")',
        'a:has-text("Download")',
        '[data-testid*="download" i]',
    ):
        step = send({"action": "click", "selector": sel, "wait_ms": 2000}, timeout=30)
        if step.get("ok"):
            print("  step", sel)
            break
    found = None
    for _ in range(20):
        time.sleep(0.5)
        found = newest_download(before)
        if found:
            break
    result = {
        "ok": bool(found),
        "slug": slug,
        "url": goto.get("url") or url,
        "controls": info.get("value"),
        "click": clicked,
        "file": str(found) if found else None,
    }
    if found:
        dest = DEST / f"{slug}{found.suffix.lower()}"
        dest.write_bytes(found.read_bytes())
        result["saved"] = str(dest)
        print("  saved", dest, dest.stat().st_size)
    else:
        shot = send({"action": "screenshot", "name": f"download-ui-{slug}.png"}, timeout=60)
        result["uiShot"] = shot.get("path")
        print("  no file; ui shot", shot.get("path"))
    return result


def main() -> None:
    pages = [
        ("echo-1904-fire", "https://www.newspapers.com/image/497174278/"),
        ("herbert-1893-bradley", "https://www.newspapers.com/image/1194114727/"),
        ("trumpet-1893-asbury", "https://www.newspapers.com/image/436807841/"),
        ("echo-1909-move", "https://www.newspapers.com/image/143869436/"),
        ("herbert-1895-gop", "https://www.newspapers.com/image/1194116748/"),
    ]
    out = [download_page(url, slug) for slug, url in pages]
    dest = ROOT / "research" / "newspapers-com" / "downloads" / "download-log.json"
    dest.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("wrote", dest)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
