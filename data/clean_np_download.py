"""Download full-resolution Entire Page JPG + PDF for every verified keeper.

Uses the native Newspapers.com "Print or Download" -> "Entire Page" ->
"Save as JPG" / "Save as PDF*" controls, driven over CDP against Joe's
already-logged-in Chrome. Browser.setDownloadBehavior(allowAndName) plus the
Browser.downloadWillBegin / downloadProgress events give us the real file path.

Never closes Chrome. Run: python clean_np_download.py [--only slug]
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pw_cdp import connect, disconnect_keep_browser, page  # noqa: E402

ROOT = Path(__file__).resolve().parent / "research" / "newspapers-com"
DL = ROOT / "downloads"
RAW = DL / "raw"
LOG = DL / "clean-download-log.json"
RAW.mkdir(parents=True, exist_ok=True)

# paper-slug, date, page, clip-slug, newspapers.com image id, NJ-printed?
KEEPERS = [
    ("trenton-sunday-advertiser", "1893-11-05", "1", "herbert-vs-bradley", "1194114727", True),
    ("asbury-park-press", "1893-07-22", "1", "murrell-speaking", "436760060", True),
    ("shore-press", "1893-07-28", "6", "murrell-asbury-meeting", "436807841", True),
    ("trenton-sunday-advertiser", "1895-10-20", "1", "herbert-gop-committee", "1194116748", True),
    ("monmouth-democrat", "1904-09-08", "4", "echo-burned-out", "497174278", True),
    ("asbury-park-press", "1909-03-05", "2", "echo-moves-red-bank", "143869436", True),
    ("courier-post", "1932-03-22", "14", "ironsides-echo-award", "446292432", True),
    ("courier-post", "1936-01-06", "3", "camp-cooper-paper", "447571125", True),
    ("the-news-paterson", "1939-09-09", "9", "nj-guardian-cited", "525697398", True),
    ("trenton-times", "1940-05-07", "13", "ironsides-echo-awards", "1191434889", True),
    ("star-ledger", "1949-01-19", "14", "melvin-johnson-left-papers", "1108232407", True),
    ("asbury-park-press", "1949-11-06", "2", "johnson-montclair-newark", "143065742", True),
    ("asbury-park-press", "1960-05-20", "21", "bronze-thrills-july", "143086953", True),
    ("ridgewood-news", "1987-11-26", "14", "landscape-ap-smith", "1122504536", True),
    ("courier-news", "1991-06-24", "8", "webber-after-hours", "223216862", True),
    ("the-record-hackensack", "1991-02-09", "2", "landscape-renamed", "496517756", True),
    ("sunday-news-ridgewood", "1993-06-27", "2", "smallest-newspaper", "634766635", True),
    ("daily-record-morristown", "2023-05-21", "D2", "nj-afro-american-described", "962761544", True),
    # out-of-state context pages, kept last
    ("evening-world", "1888-12-11", "2", "trumpet-negro-organ", "50663302", False),
    ("washington-bee", "1889-05-18", "2", "murrell-trumpet-editor", "46319440", False),
    ("new-york-tribune", "1895-12-08", "14", "herbert-profile", "78953914", False),
    ("new-york-age", "1909-10-21", "1", "herbert-obituary", "33451515", False),
    ("new-york-age", "1921-04-09", "4", "red-bank-echo-cited", "39621583", False),
    ("afro-american", "1932-07-09", "7", "newark-herald-folded", "1134167020", False),
]

CLICK_TEXT = """(want) => {
  const all = [...document.querySelectorAll('button,[role=button],a,div,span,label')];
  const hit = all.filter(e => (e.innerText||'').trim().toLowerCase() === want.toLowerCase());
  const leaf = hit[hit.length - 1];
  if (!leaf) return {ok:false, want};
  const card = leaf.closest('button,[role=button],a') || leaf;
  card.click();
  return {ok:true, want, href: card.href || null};
}"""


class Downloads:
    """Tracks Browser.download* CDP events by guid."""

    def __init__(self, bsess):
        self.done: dict[str, str] = {}
        self.begun: dict[str, str] = {}
        self.failed: set[str] = set()
        bsess.on("Browser.downloadWillBegin", self._begin)
        bsess.on("Browser.downloadProgress", self._progress)

    def _begin(self, e):
        self.begun[e["guid"]] = e.get("suggestedFilename", "")

    def _progress(self, e):
        if e.get("state") == "completed":
            self.done[e["guid"]] = e.get("filePath", "")
        elif e.get("state") == "canceled":
            self.failed.add(e["guid"])

    def wait_new(self, known: set[str], pg, timeout_s: int = 120):
        """Wait for a completed download whose guid is not in `known`."""
        end = time.time() + timeout_s
        while time.time() < end:
            for guid, path in self.done.items():
                if guid not in known and path:
                    return guid, Path(path)
            for guid in self.failed:
                if guid not in known:
                    return guid, None
            pg.wait_for_timeout(500)
        return None, None


def verify(path: Path) -> dict:
    info: dict = {"bytes": path.stat().st_size}
    if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        try:
            from PIL import Image

            Image.MAX_IMAGE_PIXELS = None
            with Image.open(path) as im:
                info["width"], info["height"] = im.size
                hist = im.convert("L").histogram()
                total = sum(hist) or 1
                info["mean_lum"] = round(sum(i * c for i, c in enumerate(hist)) / total, 1)
            info["ok"] = info["width"] > 1500 and info["height"] > 2000 and info["mean_lum"] < 250
        except Exception as exc:
            info["ok"] = False
            info["error"] = str(exc)
    else:
        head = path.read_bytes()[:5]
        info["ok"] = head == b"%PDF-" and info["bytes"] > 20000
    return info


def open_entire_page_panel(pg) -> None:
    pg.locator('button[title="Print or Download"]').click(timeout=25000)
    pg.wait_for_timeout(1800)
    res = pg.evaluate(CLICK_TEXT, "Entire Page")
    if not res.get("ok"):
        raise RuntimeError("Entire Page card not found")
    pg.wait_for_timeout(2500)


def grab(pg, dls: Downloads, label: str, dest: Path, results: dict) -> None:
    known = set(dls.done) | set(dls.failed)
    res = pg.evaluate(CLICK_TEXT, label)
    if not res.get("ok"):
        results[dest.suffix.lstrip(".")] = {"ok": False, "error": f"{label} button not found"}
        return
    guid, src = dls.wait_new(known, pg, timeout_s=150)
    if src is None or not src.exists():
        results[dest.suffix.lstrip(".")] = {"ok": False, "error": f"no file after {label}"}
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    info = verify(dest)
    info["file"] = str(dest)
    info["method"] = f'native "{label}" export via CDP allowAndName'
    info["source_name"] = src.name
    results[dest.suffix.lstrip(".")] = info
    print(f"    {label}: {dest.name} {info}")


def main() -> None:
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    browser = connect()
    pg = page()
    bsess = browser.new_browser_cdp_session()
    bsess.send(
        "Browser.setDownloadBehavior",
        {"behavior": "allowAndName", "downloadPath": str(RAW), "eventsEnabled": True},
    )
    dls = Downloads(bsess)

    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}

    for paper, date, pageno, clip, image_id, nj in KEEPERS:
        slug = f"{paper}_{date}_p{pageno}_{clip}"
        if only and only not in slug:
            continue
        jpg = DL / f"{slug}.jpg"
        pdf = DL / f"{slug}.pdf"
        if jpg.exists() and pdf.exists() and log.get(slug, {}).get("jpg", {}).get("ok"):
            print("skip (done)", slug)
            continue
        url = f"https://www.newspapers.com/image/{image_id}/"
        print("PAGE", slug, url)
        entry = {
            "slug": slug,
            "url": url,
            "image_id": image_id,
            "nj_printed": nj,
            "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=90000)
            pg.wait_for_timeout(5000)
            open_entire_page_panel(pg)
            if not jpg.exists():
                grab(pg, dls, "Save as JPG", jpg, entry)
            else:
                entry["jpg"] = {"ok": True, "file": str(jpg), "note": "already present", **verify(jpg)}
            pg.wait_for_timeout(2500)
            if not pdf.exists():
                grab(pg, dls, "Save as PDF*", pdf, entry)
            else:
                entry["pdf"] = {"ok": True, "file": str(pdf), "note": "already present", **verify(pdf)}
        except Exception as exc:
            entry["error"] = str(exc)
            print("  FAIL", exc)
        log[slug] = entry
        LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
        time.sleep(7)

    disconnect_keep_browser()
    ok_jpg = sum(1 for v in log.values() if v.get("jpg", {}).get("ok"))
    ok_pdf = sum(1 for v in log.values() if v.get("pdf", {}).get("ok"))
    print(f"DONE jpg_ok={ok_jpg} pdf_ok={ok_pdf} of {len(log)}")


if __name__ == "__main__":
    main()
