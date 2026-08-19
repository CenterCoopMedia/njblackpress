"""Save Entire Page as JPG via CDP expect_download. Do not close Chrome."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pw_cdp import disconnect_keep_browser, page

DEST = Path(__file__).resolve().parent / "research" / "newspapers-com" / "downloads"
DEST.mkdir(parents=True, exist_ok=True)


def click_exact(pg, want: str) -> dict:
    return pg.evaluate(
        """(want) => {
          const all = [...document.querySelectorAll('button, [role=button], div, span, a, label')];
          const leaf = all.find(e => (e.innerText || '').trim() === want);
          if (!leaf) return {ok:false, want};
          const card = leaf.closest('button, [role=button], a') || leaf;
          card.click();
          return {ok:true, want, tag: card.tagName};
        }""",
        want,
    )


def main() -> None:
    pg = page()
    pg.goto("https://www.newspapers.com/image/497174278/", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(2500)
    pg.locator('button[title="Print or Download"]').click(timeout=15000)
    pg.wait_for_timeout(1500)
    print("entire", click_exact(pg, "Entire Page"))
    pg.wait_for_timeout(1800)
    dest = DEST / "echo-1904-entire.jpg"
    try:
        session = pg.context.new_cdp_session(pg)
        session.send(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(DEST), "eventsEnabled": True},
        )
        print("downloadPath", DEST)
        loc = pg.get_by_text("Save as JPG", exact=True)
        if loc.count() == 0:
            loc = pg.locator("text=/Save as JPE?G/i")
        loc.first.click(timeout=15000)
        for i in range(40):
            pg.wait_for_timeout(500)
            files = [p for p in DEST.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".pdf", ".png"} and p.stat().st_mtime > (dest.stat().st_mtime if dest.exists() else 0)]
            # any new jpg in DEST
            newest = None
            cands = [p for p in DEST.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".pdf"}]
            if cands:
                newest = max(cands, key=lambda p: p.stat().st_mtime)
            if newest and newest.stat().st_mtime > (time.time() - 30) and newest.name != "cdp-fail.png":
                if newest != dest:
                    dest.write_bytes(newest.read_bytes())
                print("SAVED", dest if dest.exists() else newest, (dest if dest.exists() else newest).stat().st_size)
                break
        else:
            print("NO FILE IN DEST")
            pg.screenshot(path=str(DEST / "cdp-fail.png"))
    except Exception as exc:
        print("DOWNLOAD FAIL", exc)
        pg.screenshot(path=str(DEST / "cdp-fail.png"))
    disconnect_keep_browser()
    print("disconnected; chrome left open")


if __name__ == "__main__":
    main()
