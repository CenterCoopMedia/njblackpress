"""Capture clean full-page PNGs for NJ Black Press wayback/website keepers.

Launches its own headless chromium. Does not touch the CDP Chrome on port 9222.
Reads data/research/source-catalog.json (read-only) and writes PNGs to
data/research/wayback/clean/ plus a log at clean-capture-log.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterator

from PIL import Image, ImageStat
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "research" / "source-catalog.json"
OUT_DIR = ROOT / "data" / "research" / "wayback" / "clean"
LOG_PATH = ROOT / "data" / "research" / "wayback" / "clean-capture-log.json"

TARGET_KINDS = {"wayback_snapshot", "website_screenshot"}
VIEWPORT_WIDTH = 1440
MAX_HEIGHT = 8000
MIN_STDDEV = 6.0
MIN_HEIGHT = 400

DOC_HEIGHT_JS = """
() => Math.max(
  document.body ? document.body.scrollHeight : 0,
  document.body ? document.body.offsetHeight : 0,
  document.documentElement.scrollHeight,
  document.documentElement.offsetHeight
)
"""

ERROR_MARKERS = (
    "temporarily offline",
    "internet archive services are temporarily offline",
    "the wayback machine has not archived that url",
    "job failed",
    "this url has been excluded",
    "429 too many requests",
)

HIDE_CSS = """
#wm-ipp-base, #wm-ipp-print, #wm-ipp, #donato, .wb-autocomplete-suggestions,
#wm-capinfo, #playback, div[id^="wm-ipp"],
[id*="cookie" i], [class*="cookie-banner" i], [class*="cookie-consent" i],
[class*="cookieconsent" i], [id*="onetrust" i], [class*="onetrust" i],
#CybotCookiebotDialog, [class*="gdpr" i], [id*="gdpr" i],
[aria-label*="cookie" i], [class*="consent" i][class*="banner" i],
[id*="consent-banner" i], .cc-window, .cmp-container,
[class*="newsletter-popup" i], [class*="modal-backdrop" i],
[class*="subscribe-overlay" i], [id*="popup-overlay" i] {
  display: none !important;
}
* { animation: none !important; transition: none !important;
    scroll-behavior: auto !important; }
"""

STRIP_JS = """
() => {
  const ids = ['wm-ipp-base', 'wm-ipp-print', 'wm-ipp', 'donato', 'wm-capinfo'];
  for (const id of ids) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }
  // Unstick overlays so they do not repeat down a full-page shot.
  // Sticky elements sit in the normal flow: switch them to static, never to
  // absolute, or the document height collapses to one viewport.
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const fullScreen =
      r.height > window.innerHeight * 0.7 && r.width > window.innerWidth * 0.7;
    if (cs.position === 'fixed') {
      if (fullScreen) {
        el.style.display = 'none';
      } else {
        el.style.position = 'absolute';
      }
    } else if (cs.position === 'sticky') {
      el.style.position = 'static';
    }
  }
  document.documentElement.style.setProperty('scroll-behavior', 'auto', 'important');
}
"""


def slugify(text: str) -> str:
    """Return a lowercase filename-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "untitled"


def normalize_wayback_url(url: str) -> str:
    """Insert the missing slash after a wayback timestamp when needed."""
    match = re.match(r"^(https?://web\.archive\.org/web/)(\d{14})(https?://.*)$", url)
    if match:
        return f"{match.group(1)}{match.group(2)}/{match.group(3)}"
    return url


def wayback_timestamp(url: str) -> str | None:
    """Return the 14-digit wayback timestamp in a URL, if present."""
    match = re.search(r"/web/(\d{14})", url)
    return match.group(1) if match else None


def id_only_url(url: str) -> str:
    """Return the wayback URL with the id_ raw-content modifier removed."""
    return re.sub(r"/web/(\d{14})(?:\w{2}_)?/", r"/web/\1/", url)


def load_targets(catalog_path: Path) -> list[dict[str, Any]]:
    """Collect wayback/website keepers, oldest publication first."""
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    targets: list[dict[str, Any]] = []
    for pub in data["publications"]:
        for keeper in pub.get("keepers", []):
            if keeper.get("kind") not in TARGET_KINDS:
                continue
            url = normalize_wayback_url(keeper["url"])
            targets.append(
                {
                    "pub_id": pub["id"],
                    "name": pub["name"],
                    "year_founded": pub.get("yearFounded"),
                    "kind": keeper["kind"],
                    "url": url,
                    "original_url": keeper["url"],
                    "old_file": keeper.get("localFile"),
                    "timestamp": wayback_timestamp(url) or "live",
                }
            )
    targets.sort(key=lambda t: (t["year_founded"] or 9999, t["pub_id"]))
    return targets


def out_name(target: dict[str, Any]) -> str:
    """Build the output filename for a target."""
    return f"{target['pub_id']:03d}-{slugify(target['name'])}-{target['timestamp']}.png"


def settle(page: Page, extra_wait: float) -> int:
    """Wait, strip chrome, scroll for lazy images, return to top.

    Returns the tallest document height seen, measured before and after the
    overlay strip.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=45_000)
    except Exception:
        pass
    pre_height = page.evaluate(DOC_HEIGHT_JS)
    page.add_style_tag(content=HIDE_CSS)
    page.evaluate(STRIP_JS)
    page.wait_for_timeout(int(extra_wait * 1000))
    height = page.evaluate(DOC_HEIGHT_JS)
    step = 900
    for offset in range(0, min(height, MAX_HEIGHT) + step, step):
        page.evaluate("(y) => window.scrollTo(0, y)", offset)
        page.wait_for_timeout(220)
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(1200)
    page.add_style_tag(content=HIDE_CSS)
    page.evaluate(STRIP_JS)
    page.wait_for_timeout(600)
    return max(pre_height, page.evaluate(DOC_HEIGHT_JS))


def verify(path: Path) -> tuple[bool, tuple[int, int], float, str]:
    """Check a PNG is a real, non-blank capture."""
    with Image.open(path) as img:
        size = img.size
        stddev = ImageStat.Stat(img.convert("L")).stddev[0]
    if size[1] < MIN_HEIGHT:
        return False, size, stddev, "height too small"
    if stddev < MIN_STDDEV:
        return False, size, stddev, f"near-blank (stddev {stddev:.1f})"
    return True, size, stddev, "ok"


def capture(page: Page, target: dict[str, Any], path: Path, extra_wait: float) -> dict[str, Any]:
    """Navigate and write one full-page PNG. Returns a partial log record."""
    response = page.goto(target["url"], wait_until="domcontentloaded", timeout=90_000)
    status = response.status if response else None
    settled_height = settle(page, extra_wait)
    text = (page.inner_text("body") or "")[:2000].lower()
    marker = next((m for m in ERROR_MARKERS if m in text), None)
    if marker:
        return {"http_status": status, "ok": False, "notes": f"archive error page: {marker}"}
    height = max(settled_height, page.evaluate(DOC_HEIGHT_JS))
    clip_used = height > MAX_HEIGHT
    # Resize the viewport to the document height: broken archived pages report a
    # short body and full_page then crops the content.
    page.set_viewport_size(
        {"width": VIEWPORT_WIDTH, "height": max(600, min(height, MAX_HEIGHT))}
    )
    page.wait_for_timeout(1500)
    page.add_style_tag(content=HIDE_CSS)
    page.evaluate(STRIP_JS)
    page.wait_for_timeout(500)
    if clip_used:
        page.screenshot(
            path=str(path),
            clip={"x": 0, "y": 0, "width": VIEWPORT_WIDTH, "height": MAX_HEIGHT},
        )
    else:
        page.screenshot(path=str(path), full_page=True)
    ok, size, stddev, note = verify(path)
    return {
        "http_status": status,
        "clipped": clip_used,
        "page_height": height,
        "dimensions": list(size),
        "stddev": round(stddev, 2),
        "ok": ok,
        "notes": note,
    }


def cdx_alternatives(url: str, limit: int = 5) -> list[str]:
    """Return alternative wayback timestamps for the original site URL."""
    import urllib.parse
    import urllib.request

    match = re.match(r"^https?://web\.archive\.org/web/\d{14}(?:\w{2}_)?/(.*)$", url)
    if not match:
        return []
    site = match.group(1)
    query = urllib.parse.urlencode(
        {"url": site, "output": "json", "fl": "timestamp,statuscode", "limit": limit,
         "filter": "statuscode:200", "collapse": "timestamp:6"}
    )
    try:
        with urllib.request.urlopen(f"https://web.archive.org/cdx/search/cdx?{query}", timeout=45) as fh:
            rows = json.loads(fh.read().decode("utf-8"))
    except Exception:
        return []
    return [f"https://web.archive.org/web/{row[0]}/{site}" for row in rows[1:]]


def run(targets: list[dict[str, Any]], delay: float) -> list[dict[str, Any]]:
    """Capture every target, retrying once with longer waits."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--hide-scrollbars"],
        )
        context = browser.new_context(
            viewport={"width": VIEWPORT_WIDTH, "height": 1000},
            device_scale_factor=2,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        )
        context.set_default_timeout(90_000)
        for index, target in enumerate(targets, start=1):
            path = OUT_DIR / out_name(target)
            record: dict[str, Any] = {
                "pub_id": target["pub_id"],
                "name": target["name"],
                "kind": target["kind"],
                "url": target["url"],
                "original_url": target["original_url"],
                "old_file": target["old_file"],
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            }
            print(f"[{index}/{len(targets)}] {target['pub_id']} {target['name']}", flush=True)
            result: dict[str, Any] = {}
            for attempt, wait in enumerate((3.0, 8.0), start=1):
                page = context.new_page()
                try:
                    result = capture(page, target, path, wait)
                except Exception as exc:  # noqa: BLE001
                    result = {"ok": False, "notes": f"{type(exc).__name__}: {exc}"[:300]}
                finally:
                    page.close()
                result["attempts"] = attempt
                if result.get("ok"):
                    break
                time.sleep(delay)
            if not result.get("ok"):
                alts = cdx_alternatives(target["url"])
                if alts:
                    result["cdx_alternatives"] = alts
            record.update(result)
            print(f"    -> {record.get('ok')} {record.get('dimensions')} {record.get('notes')}", flush=True)
            records.append(record)
            time.sleep(delay)
        context.close()
        browser.close()
    return records


def merge_log(records: list[dict[str, Any]]) -> None:
    """Write or update the capture log, keyed by pub_id + file."""
    existing: list[dict[str, Any]] = []
    if LOG_PATH.exists():
        existing = json.loads(LOG_PATH.read_text(encoding="utf-8")).get("captures", [])
    by_key = {(r["pub_id"], r["file"]): r for r in existing}
    for record in records:
        by_key[(record["pub_id"], record["file"])] = record
    merged = sorted(by_key.values(), key=lambda r: r["pub_id"])
    payload = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(merged),
        "ok": sum(1 for r in merged if r.get("ok")),
        "failed": sum(1 for r in merged if not r.get("ok")),
        "captures": merged,
    }
    LOG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="capture only the first N targets")
    parser.add_argument("--ids", type=str, default="", help="comma-separated publication ids")
    parser.add_argument("--delay", type=float, default=4.0, help="seconds between requests")
    parser.add_argument("--list", action="store_true", help="print targets and exit")
    args = parser.parse_args(argv)

    targets = load_targets(CATALOG)
    if args.ids:
        wanted = {int(x) for x in args.ids.split(",") if x.strip()}
        targets = [t for t in targets if t["pub_id"] in wanted]
    if args.limit:
        targets = targets[: args.limit]
    if args.list:
        for t in targets:
            print(t["pub_id"], t["year_founded"], t["name"], t["url"])
        return 0
    records = run(targets, args.delay)
    merge_log(records)
    ok = sum(1 for r in records if r.get("ok"))
    print(f"\ndone: {ok} ok / {len(records) - ok} failed -> {LOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
