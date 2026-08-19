"""Export the two late-added Utimme Umana keepers and probe the 4 stuck PDFs."""

from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pw_cdp import connect, disconnect_keep_browser, page  # noqa: E402
from clean_np_download import CLICK_TEXT, DL, LOG, RAW, Downloads, verify  # noqa: E402

EXTRA = [
    ("trenton-times", "1976-04-23", "utimme-umana", "1192937414"),
    ("trenton-times", "1993-09-27", "utimme-umana", "1197515771"),
]
STUCK = [
    ("sunday-news-ridgewood_1993-06-27_p2_smallest-newspaper", "634766635"),
    ("new-york-tribune_1895-12-08_p14_herbert-profile", "78953914"),
    ("new-york-age_1921-04-09_p4_red-bank-echo-cited", "39621583"),
    ("afro-american_1932-07-09_p7_newark-herald-folded", "1134167020"),
]


def open_panel(pg):
    pg.locator('button[title="Print or Download"]').click(timeout=25000)
    pg.wait_for_timeout(2000)
    pg.get_by_text("Entire Page", exact=True).last.click(timeout=20000)
    pg.wait_for_timeout(3500)


def main() -> None:
    log = json.loads(LOG.read_text(encoding="utf-8"))
    browser = connect()
    pg = page()
    bsess = browser.new_browser_cdp_session()
    bsess.send(
        "Browser.setDownloadBehavior",
        {"behavior": "allowAndName", "downloadPath": str(RAW), "eventsEnabled": True},
    )
    dls = Downloads(bsess)

    for paper, date, clip, image_id in EXTRA:
        url = f"https://www.newspapers.com/image/{image_id}/"
        pg.goto(url, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(6000)
        m = re.search(r"page (\S+?) -", pg.title())
        pageno = m.group(1) if m else "0"
        slug = f"{paper}_{date}_p{pageno}_{clip}"
        print("EXTRA", slug, pg.title()[:60], flush=True)
        entry = {"slug": slug, "url": url, "image_id": image_id, "nj_printed": True}
        open_panel(pg)
        for label, ext in (("Save as JPG", ".jpg"), ("Save as PDF*", ".pdf")):
            dest = DL / (slug + ext)
            if dest.exists():
                continue
            known = set(dls.done) | set(dls.failed)
            res = pg.evaluate(CLICK_TEXT, label)
            if not res.get("ok"):
                entry[ext.lstrip(".")] = {"ok": False, "error": "button not found"}
                continue
            _g, src = dls.wait_new(known, pg, timeout_s=240)
            if src and src.exists():
                shutil.move(str(src), str(dest))
                info = verify(dest)
                info["file"] = str(dest)
                info["method"] = f'native "{label}" export'
                entry[ext.lstrip(".")] = info
                print("  ", label, info.get("ok"), info.get("width"), info.get("height"), info["bytes"], flush=True)
            else:
                entry[ext.lstrip(".")] = {"ok": False, "error": f"no file after {label}"}
                print("  ", label, "FAIL", flush=True)
            pg.wait_for_timeout(2500)
        log[slug] = entry
        LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
        time.sleep(7)

    # probe the stuck PDFs: is the pill disabled / is there a note?
    for slug, image_id in STUCK:
        pg.goto(f"https://www.newspapers.com/image/{image_id}/", wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(6000)
        open_panel(pg)
        state = pg.evaluate(
            """() => {
          const els = [...document.querySelectorAll('a,button')].filter(e => /save as pdf/i.test(e.innerText||''));
          const e = els[els.length-1];
          const panel = document.querySelector('.shadow.open');
          return {
            found: !!e,
            cls: e ? (e.className||'').toString() : null,
            disabled: e ? (e.getAttribute('aria-disabled') || e.disabled || null) : null,
            href: e ? (e.href||null) : null,
            note: panel ? (panel.innerText||'').replace(/\\s+/g,' ').slice(0,400) : null
          };
        }"""
        )
        print("STUCK", slug, json.dumps(state)[:500], flush=True)
        log.setdefault(slug, {}).setdefault("pdf", {})["probe"] = state
        LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
        time.sleep(5)

    disconnect_keep_browser()
    print("extra done", flush=True)


if __name__ == "__main__":
    main()
