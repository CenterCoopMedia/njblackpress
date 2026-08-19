"""Attempt the official Entire Page -> Save as JPG export on one page.

Registers browser-level CDP download behavior and logs every request while
clicking. Does not close Chrome.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pw_cdp import connect, disconnect_keep_browser, page  # noqa: E402

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com" / "downloads"
DEST = OUT / "raw"
DEST.mkdir(parents=True, exist_ok=True)
USER_DL = Path.home() / "Downloads"
URL = "https://www.newspapers.com/image/497174278/"


def click_text(pg, want: str) -> dict:
    return pg.evaluate(
        """(want) => {
      const all = [...document.querySelectorAll('button,[role=button],a,div,span,label')];
      const hit = all.filter(e => (e.innerText||'').trim().toLowerCase() === want.toLowerCase());
      const leaf = hit[hit.length - 1];
      if (!leaf) return {ok:false, want};
      const card = leaf.closest('button,[role=button],a') || leaf;
      card.click();
      return {ok:true, want, tag: card.tagName, cls: (card.className||'').toString().slice(0,80)};
    }""",
        want,
    )


def snapshot(pg):
    return pg.evaluate(
        """() => [...document.querySelectorAll('button,[role=button],a')]
        .map(e => ({t:(e.innerText||'').trim().slice(0,50), tag:e.tagName, cls:(e.className||'').toString().slice(0,50), href:e.href||null}))
        .filter(x => x.t && x.t.length < 50)
        .slice(0, 60)"""
    )


def main() -> None:
    browser = connect()
    pg = page()
    reqs: list[str] = []
    downloads: list = []

    pg.context.on("download", lambda d: downloads.append(d))
    pg.on("request", lambda r: reqs.append(f"{r.method} {r.url[:600]}"))

    events: list[dict] = []

    # browser-level download behavior + events
    try:
        bsess = browser.new_browser_cdp_session()
        bsess.on("Browser.downloadWillBegin", lambda e: events.append({"ev": "b.willBegin", **e}))
        bsess.on("Browser.downloadProgress", lambda e: events.append({"ev": "b.progress", **e}))
        bsess.send(
            "Browser.setDownloadBehavior",
            {"behavior": "allowAndName", "downloadPath": str(DEST), "eventsEnabled": True},
        )
        print("browser-level setDownloadBehavior(allowAndName) ok ->", DEST)
    except Exception as exc:
        print("browser-level fail", exc)
    try:
        psess = pg.context.new_cdp_session(pg)
        psess.send("Page.enable", {})
        psess.on("Page.downloadWillBegin", lambda e: events.append({"ev": "p.willBegin", **e}))
        psess.on("Page.downloadProgress", lambda e: events.append({"ev": "p.progress", **e}))
        psess.send(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(DEST)},
        )
        print("page-level setDownloadBehavior ok")
    except Exception as exc:
        print("page-level fail", exc)

    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(6000)
    before = set(p.name for p in DEST.iterdir())
    before_dl = set(p.name for p in USER_DL.iterdir()) if USER_DL.exists() else set()

    pg.locator('button[title="Print or Download"]').click(timeout=20000)
    pg.wait_for_timeout(2000)
    print("entire ->", click_text(pg, "Entire Page"))
    pg.wait_for_timeout(3000)
    print("STEP2", json.dumps(snapshot(pg), indent=1)[:3000])

    mark = len(reqs)
    print("jpg ->", click_text(pg, "Save as JPG"))

    found = None
    for _ in range(60):
        pg.wait_for_timeout(1000)
        now = [p for p in DEST.iterdir() if p.name not in before and not p.name.endswith(".crdownload")]
        if USER_DL.exists():
            now += [
                p
                for p in USER_DL.iterdir()
                if p.name not in before_dl and not p.name.endswith(".crdownload")
            ]
        if now:
            found = max(now, key=lambda p: p.stat().st_mtime)
            break
        if downloads:
            print("playwright download event fired")
            break
    print("CDP EVENTS", json.dumps(events, indent=1)[:2000])
    print("DOWNLOADS EVENTS", len(downloads))
    if downloads:
        try:
            p = downloads[0].path()
            print("dl path", p, downloads[0].suggested_filename)
            found = Path(p)
        except Exception as exc:
            print("dl path fail", exc)
    print("FILE", found, found.stat().st_size if found else None)

    new_reqs = reqs[mark:]
    (OUT / "export-clicks-requests.json").write_text(json.dumps(new_reqs, indent=2), encoding="utf-8")
    print("--- requests after Save as JPG click ---")
    for r in new_reqs:
        if "doubleclick" in r or "google" in r or "bing" in r or "facebook" in r:
            continue
        print(" ", r[:300])

    pg.screenshot(path=str(OUT / "export-probe-state.png"))
    disconnect_keep_browser()


if __name__ == "__main__":
    main()
