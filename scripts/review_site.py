"""Browser review of the main site pages: navigation, focus, targets, and structure.

scripts/review_hall.py covers the history hall. This review covers every other
public route at a desktop and a phone size, and fails on the regressions the
September 2026 sweep fixed:

- the mobile menu: out of the tab order while closed, a modal dialog while
  open, focus kept inside, Escape closes it and focus returns to its button;
- one h1 and no skipped heading level;
- an accessible name on every form control and button;
- WCAG 2.5.8 target size (24 by 24 CSS pixels, unless inline in text);
- one shared footer outside <main>;
- no running animation when the reader asks for reduced motion;
- no uncaught script error.

    python3 scripts/review_site.py [--output DIR]

Pages load from docs/ through request routing, so no server is needed.
Network requests other than Google Fonts and the Leaflet CDN are blocked.
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


DOCS = Path(__file__).resolve().parents[1] / "docs"
BASE = "https://site.invalid/"
ROUTES = [
    "index.html",
    "archive.html",
    "publication.html?id=1",
    "publication.html?id=99999",
    "story.html",
    "story.html?id=story-001",
    "era.html",
    "era.html?decade=1960s",
    "map.html",
    "wiki/index.html",
    "wiki/publications.html",
    "wiki/publications/001-hype.html",
    "wiki/decades/1960s.html",
]
FETCHED = {}

# A target may be smaller than 24px when it sits inline in a sentence (WCAG
# 2.5.8 inline exception). This finds controls that are not inline text links.
TARGETS_JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('a[href], button, input, select, summary, [role="button"]')) {
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none' || el.closest('[hidden], [inert], .sr-only, .skip-link')) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (el.tagName === 'A' && style.display === 'inline') {
      const parent = el.parentElement;
      const text = parent ? parent.textContent.trim() : '';
      if (text.length > el.textContent.trim().length + 20) continue;  // inline in running text
    }
    if (el.closest('.leaflet-container')) continue;  // map library controls
    if (r.width < 24 || r.height < 24) out.push(`${el.tagName.toLowerCase()} "${(el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40)}" ${Math.round(r.width)}x${Math.round(r.height)}`);
  }
  return out;
}"""

NAMES_JS = """() => {
  const out = [];
  for (const el of document.querySelectorAll('input:not([type=hidden]), select, textarea, button')) {
    if (el.closest('[hidden]')) continue;
    const labelled = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || (el.id && document.querySelector(`label[for="${el.id}"]`)) || el.closest('label') || el.textContent.trim() || el.title;
    if (!labelled) out.push(`${el.tagName.toLowerCase()}#${el.id}`);
  }
  return out;
}"""

HEADINGS_JS = """() => {
  const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(h => h.getClientRects().length || h.closest('.sr-only'));
  const out = [];
  const h1 = hs.filter(h => h.tagName === 'H1').length;
  if (h1 !== 1) out.push(`${h1} h1 elements`);
  let last = 0;
  for (const h of hs) {
    const level = Number(h.tagName[1]);
    if (last && level > last + 1) out.push(`h${last} to h${level}: "${h.textContent.trim().slice(0, 40)}"`);
    last = level;
  }
  return out;
}"""


def route(r) -> None:
    url = r.request.url
    if url.startswith(BASE):
        path = DOCS / url[len(BASE):].split("?")[0].split("#")[0]
        if path.is_dir():
            path = path / "index.html"
        return r.fulfill(path=str(path)) if path.is_file() else r.fulfill(status=404)
    if url.startswith(("https://fonts.googleapis.com/", "https://fonts.gstatic.com/", "https://unpkg.com/leaflet")):
        if url not in FETCHED:
            request = urllib.request.Request(url, headers={"User-Agent": r.request.headers.get("user-agent", "")})
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    FETCHED[url] = (response.status, response.read(), response.headers.get("Content-Type", ""))
            except OSError:
                FETCHED[url] = None
        if FETCHED[url]:
            status, body, kind = FETCHED[url]
            return r.fulfill(status=status, body=body, headers={"Content-Type": kind, "Access-Control-Allow-Origin": "*"})
    return r.abort()


def review_menu(page, name: str, check) -> None:
    menu = page.locator("#mobile-menu")
    button = page.locator("#mobile-menu-btn")
    check(f"{name}: one menu button and one menu", button.count() == 1 and menu.count() == 1)
    if button.count() != 1 or menu.count() != 1:
        return
    check(f"{name}: closed menu is hidden from focus", menu.evaluate("el => el.hidden"))
    check(f"{name}: menu is a modal dialog", menu.get_attribute("role") == "dialog" and menu.get_attribute("aria-modal") == "true")
    button.click()
    check(f"{name}: open moves focus to Close", page.evaluate("document.activeElement.id") == "mobile-menu-close")
    check(f"{name}: open sets aria-expanded", button.get_attribute("aria-expanded") == "true")
    items = page.evaluate("[...document.querySelectorAll('#mobile-menu a')].map(a => a.getBoundingClientRect().height)")
    check(f"{name}: menu links are at least 44px tall", bool(items) and min(items) >= 44, str(items[:3]))
    inside = True
    for _ in range(12):
        page.keyboard.press("Tab")
        inside = inside and page.evaluate("document.getElementById('mobile-menu').contains(document.activeElement)")
    check(f"{name}: Tab stays inside the open menu", inside)
    page.keyboard.press("Escape")
    check(f"{name}: Escape closes the menu", menu.evaluate("el => el.hidden"))
    check(f"{name}: focus returns to the menu button", page.evaluate("document.activeElement.id") == "mobile-menu-btn")
    check(f"{name}: page scroll is unlocked", not page.evaluate("document.body.classList.contains('overflow-hidden')"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", default="/tmp/site-review")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    results = {"passed": [], "errors": []}

    def check(label: str, ok: bool, detail: str = "") -> None:
        (results["passed"] if ok else results["errors"]).append(label + (f": {detail}" if detail and not ok else ""))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for size, viewport in (("desktop", {"width": 1440, "height": 900}), ("phone", {"width": 390, "height": 844})):
            context = browser.new_context(viewport=viewport, reduced_motion="reduce")
            context.route("**/*", route)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            for path in ROUTES:
                name = f"{size} {path}"
                errors.clear()
                page.goto(BASE + path, wait_until="networkidle")
                page.wait_for_timeout(700)
                check(f"{name}: no uncaught script error", not errors, "; ".join(errors))
                headings = page.evaluate(HEADINGS_JS)
                check(f"{name}: one h1 and no skipped heading level", not headings, "; ".join(headings))
                unnamed = page.evaluate(NAMES_JS)
                check(f"{name}: every control has a name", not unnamed, ", ".join(unnamed))
                small = page.evaluate(TARGETS_JS)
                check(f"{name}: targets are at least 24px", not small, "; ".join(small[:6]))
                check(f"{name}: one site footer, outside main", page.evaluate(
                    "document.querySelectorAll('footer[data-site-footer]').length === 1 && !document.querySelector('main footer[data-site-footer]')"))
                running = page.evaluate("document.getAnimations().filter(a => a.playState === 'running' && a.effect && a.effect.getTiming().duration > 50).length")
                check(f"{name}: no running animation under reduced motion", running == 0, f"{running} running")
                if size == "phone":
                    check(f"{name}: no horizontal page scroll", page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                    review_menu(page, name, check)
                page.screenshot(path=str(out / f"{size}-{path.replace('/', '_').replace('?', '_')}.png"))
            context.close()
        browser.close()

    (out / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps({"passed": len(results["passed"]), "errors": results["errors"]}, indent=2))
    sys.exit(1 if results["errors"] else 0)


if __name__ == "__main__":
    main()
