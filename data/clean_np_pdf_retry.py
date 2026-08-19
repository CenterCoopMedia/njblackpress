"""Retry the missing "Save as PDF*" exports.

The PDF pill has no href (unlike the JPG pill), so it is JS-driven and needs a
real trusted mouse click. This pass clicks the PDF first, with a longer wait.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pw_cdp import connect, disconnect_keep_browser, page  # noqa: E402
from clean_np_download import DL, KEEPERS, LOG, RAW, Downloads, verify  # noqa: E402


def main() -> None:
    log = json.loads(LOG.read_text(encoding="utf-8"))
    todo = [
        (slug, entry["image_id"])
        for slug, entry in log.items()
        if entry.get("image_id") and not (DL / f"{slug}.pdf").exists()
    ]
    print("missing pdfs:", len(todo), [t[0] for t in todo], flush=True)

    browser = connect()
    pg = page()
    bsess = browser.new_browser_cdp_session()
    bsess.send(
        "Browser.setDownloadBehavior",
        {"behavior": "allowAndName", "downloadPath": str(RAW), "eventsEnabled": True},
    )
    dls = Downloads(bsess)

    for slug, image_id in todo:
        pdf = DL / f"{slug}.pdf"
        print("PDF", slug, flush=True)
        try:
            pg.goto(f"https://www.newspapers.com/image/{image_id}/", wait_until="domcontentloaded", timeout=90000)
            pg.wait_for_timeout(6000)
            pg.locator('button[title="Print or Download"]').click(timeout=25000)
            pg.wait_for_timeout(2000)
            pg.get_by_text("Entire Page", exact=True).last.click(timeout=20000)
            pg.wait_for_timeout(3500)
            src = None
            for attempt in range(3):
                known = set(dls.done) | set(dls.failed)
                pg.get_by_text("Save as PDF*", exact=True).last.click(timeout=20000)
                _guid, src = dls.wait_new(known, pg, timeout_s=90)
                if src and src.exists():
                    break
                print(f"  attempt {attempt + 1} no file, re-clicking", flush=True)
                pg.wait_for_timeout(3000)
            if src and src.exists():
                shutil.move(str(src), str(pdf))
                info = verify(pdf)
                info["file"] = str(pdf)
                info["method"] = 'native "Save as PDF*" trusted click, retry pass'
                log.setdefault(slug, {})["pdf"] = info
                print("  ok", info)
            else:
                log.setdefault(slug, {}).setdefault("pdf", {})["retry_error"] = "no file after 300s"
                print("  still no pdf")
        except Exception as exc:
            log.setdefault(slug, {}).setdefault("pdf", {})["retry_error"] = str(exc)
            print("  FAIL", exc)
        LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
        time.sleep(7)

    disconnect_keep_browser()
    print("retry done")


if __name__ == "__main__":
    main()
