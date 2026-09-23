"""Rebuild the social card and the PNG icons from the live pages and the SVG favicon.

Outputs, all under docs/:
- og-image.png: 1200x630 capture of the home page hero, used by every page.
- favicon-32.png: 32x32 render of favicon.svg for browsers without SVG icons.
- apple-touch-icon.png: 180x180 opaque render of njblackpress-icon.png for
  iOS home screens. iOS fills transparency with black, so it is flattened.

Run after a visible change to the home page hero or the navigation:

    python3 scripts/make_social_assets.py

Needs Pillow and Playwright with a Chromium build. In the cloud container,
set PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers.
"""

import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


DOCS = Path(__file__).resolve().parents[1] / "docs"


BASE = "https://site.invalid/"


def serve_docs(route) -> None:
    """Answer requests for BASE from docs/ so no local server or proxy rule is needed."""
    path = DOCS / route.request.url[len(BASE):].split("?")[0].split("#")[0]
    if path.is_file():
        route.fulfill(path=str(path))
    else:
        route.fulfill(status=404)


def fetch_font(route) -> None:
    """Fetch Google Fonts with Python so TLS uses the system CA bundle and any HTTPS_PROXY."""
    request = urllib.request.Request(route.request.url, headers={"User-Agent": route.request.headers.get("user-agent", "")})
    with urllib.request.urlopen(request, timeout=30) as response:
        route.fulfill(status=response.status, body=response.read(),
                      headers={"Content-Type": response.headers.get("Content-Type", ""), "Access-Control-Allow-Origin": "*"})


def make_card(page, base: str) -> None:
    page.set_viewport_size({"width": 1200, "height": 630})
    page.emulate_media(reduced_motion="reduce")
    page.goto(base + "index.html", wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    # The grain overlay and scroll hints are decoration; a still card reads better without them.
    page.add_style_tag(content=".grain-overlay{display:none!important}")
    # The hero counters count up for 1.5 seconds; capture them at their final totals.
    page.wait_for_timeout(2000)
    page.screenshot(path=str(DOCS / "og-image.png"), clip={"x": 0, "y": 0, "width": 1200, "height": 630})


def make_favicon(page, base: str) -> None:
    page.set_viewport_size({"width": 32, "height": 32})
    page.set_content(
        f'<style>html,body{{margin:0;background:transparent}}</style>'
        f'<img src="{base}favicon.svg" width="32" height="32">'
    )
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(DOCS / "favicon-32.png"), omit_background=True)


def make_touch_icon() -> None:
    with Image.open(DOCS / "njblackpress-icon.png") as source:
        icon = source.convert("RGBA").resize((180, 180), Image.LANCZOS)
    flat = Image.new("RGB", icon.size, (255, 255, 255))
    flat.paste(icon, mask=icon.getchannel("A"))
    flat.save(DOCS / "apple-touch-icon.png", optimize=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        page.route(BASE + "**", serve_docs)
        # Google Fonts must load for the card to match the site.
        page.route("https://fonts.googleapis.com/**", fetch_font)
        page.route("https://fonts.gstatic.com/**", fetch_font)
        make_card(page, BASE)
        make_favicon(page, BASE)
        browser.close()
    make_touch_icon()
    print("wrote docs/og-image.png, docs/favicon-32.png, docs/apple-touch-icon.png")


if __name__ == "__main__":
    main()
