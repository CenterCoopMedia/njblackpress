"""Regression checks for page metadata, icons, public facts, and external links.

Every public page must carry the same head contract so that search results,
social cards, and home-screen icons name the archive the same way.
"""

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = "https://centercoopmedia.github.io/njblackpress/"
NAME = "NJ Black Press Archive"
PAGES = [
    "index.html",
    "archive.html",
    "publication.html",
    "story.html",
    "era.html",
    "map.html",
    "historical-notes.html",
    "woven.html",
]
WIKI_SAMPLES = ["wiki/index.html", "wiki/statistics.html", "wiki/publications/001-hype.html"]
RETIRED_HOST = "centerforcooperativemedia.org/njblackpress"


class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.links = []
        self.title = ""
        self.anchors = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
        elif tag == "title":
            self._in_title = True
        elif tag == "a":
            self.anchors.append(a)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse(path: Path) -> Head:
    head = Head()
    head.feed(path.read_text(encoding="utf-8"))
    return head


def check_head(page: str, head: Head) -> list[str]:
    errors = []
    title = head.title.strip()
    if page == "index.html":
        if title != NAME:
            errors.append(f"{page}: home title is {title!r}, expected {NAME!r}")
    elif not page.startswith("wiki/") and not title.endswith(f" | {NAME}"):
        errors.append(f"{page}: title {title!r} does not end with ' | {NAME}'")
    required = [
        "description",
        "og:title",
        "og:description",
        "og:type",
        "og:url",
        "og:image",
        "og:image:alt",
        "og:image:width",
        "og:image:height",
        "og:site_name",
        "twitter:card",
        "twitter:title",
        "twitter:description",
        "twitter:image",
        "theme-color",
        "color-scheme",
    ]
    for key in required:
        if not head.meta.get(key):
            errors.append(f"{page}: missing meta {key}")
    if head.meta.get("og:site_name") and head.meta["og:site_name"] != NAME:
        errors.append(f"{page}: og:site_name is {head.meta['og:site_name']!r}")
    for key in ("og:image", "twitter:image"):
        if head.meta.get(key) and head.meta[key] != SITE + "og-image.png":
            errors.append(f"{page}: {key} is not the shared absolute og-image.png")
    if head.meta.get("og:title") and head.meta["og:title"] != title and not page.startswith("wiki/"):
        errors.append(f"{page}: og:title {head.meta['og:title']!r} differs from title {title!r}")

    rels = {(l.get("rel"), l.get("type")): l.get("href", "") for l in head.links}
    if ("icon", "image/svg+xml") not in rels or not rels[("icon", "image/svg+xml")].endswith("favicon.svg"):
        errors.append(f"{page}: missing SVG favicon")
    png = rels.get(("icon", "image/png"), "")
    if not png.endswith("favicon-32.png"):
        errors.append(f"{page}: PNG icon is {png!r}, expected favicon-32.png")
    touch = [l.get("href", "") for l in head.links if l.get("rel") == "apple-touch-icon"]
    if not touch or not touch[0].endswith("apple-touch-icon.png"):
        errors.append(f"{page}: missing apple-touch-icon")
    canonical = [l.get("href", "") for l in head.links if l.get("rel") == "canonical"]
    if not canonical or not canonical[0].startswith(SITE):
        errors.append(f"{page}: missing canonical URL on the Pages host")

    for a in head.anchors:
        if a.get("target") == "_blank":
            rel = set((a.get("rel") or "").split())
            if not {"noopener", "noreferrer"} <= rel:
                errors.append(f"{page}: external link {a.get('href')} lacks rel=noopener noreferrer")
        href = a.get("href") or ""
        if href.startswith("http") and not href.startswith(SITE) and a.get("target") != "_blank":
            errors.append(f"{page}: external link {href} does not open in a new tab")
    return errors


def check_icons() -> list[str]:
    from PIL import Image

    errors = []
    for name, size in (("favicon-32.png", 32), ("apple-touch-icon.png", 180)):
        path = DOCS / name
        if not path.exists():
            errors.append(f"missing docs/{name}")
            continue
        with Image.open(path) as im:
            if im.size != (size, size):
                errors.append(f"docs/{name} is {im.size}, expected {size}x{size}")
            if name == "apple-touch-icon.png" and im.mode not in ("RGB", "P", "L"):
                errors.append("apple-touch-icon.png must be opaque: iOS fills transparency with black")
    return errors


def check_js_links() -> list[str]:
    errors = []
    for path in sorted((DOCS / "js").rglob("*.js")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r'target=\\?"_blank\\?"[^>]{0,200}', text):
            if "noreferrer" not in match.group(0):
                line = text[: match.start()].count("\n") + 1
                errors.append(f"{path.relative_to(ROOT)}:{line}: target=_blank without noreferrer")
    return errors


def check_public_facts() -> list[str]:
    errors = []
    count = len(json.loads((DOCS / "data" / "publications.json").read_text())["publications"])
    llms = (DOCS / "llms.txt").read_text(encoding="utf-8")
    if RETIRED_HOST in llms:
        errors.append("docs/llms.txt links to the retired host")
    for number in re.findall(r"(\d+) Black-owned publications", llms):
        if int(number) != count:
            errors.append(f"docs/llms.txt says {number} publications, the record has {count}")
    if "Public domain" in llms:
        errors.append("docs/llms.txt claims a license the repository does not grant")
    index = (DOCS / "index.html").read_text(encoding="utf-8")
    if "creativecommons.org" in index:
        errors.append("docs/index.html JSON-LD claims a license the repository does not grant")
    for stale in ("NJ Black Press Database", "New Jersey Black Press Database"):
        if stale in index:
            errors.append(f"docs/index.html uses the old name {stale!r}")
    for path in DOCS.glob("*.html"):
        if RETIRED_HOST in path.read_text(encoding="utf-8"):
            errors.append(f"{path.name} links to the retired host")
    return errors


def check_sitemap() -> list[str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_sitemap.py"), "--check"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [f"docs/sitemap.xml is stale: {result.stdout.strip()} {result.stderr.strip()}"]
    return []


def main() -> None:
    errors = []
    for page in PAGES + WIKI_SAMPLES:
        errors += check_head(page, parse(DOCS / page))
    errors += check_icons()
    errors += check_js_links()
    errors += check_public_facts()
    errors += check_sitemap()
    if errors:
        print("\n".join(errors))
        raise SystemExit(f"FAIL: {len(errors)} metadata problems")
    print(f"PASS: metadata, icons, links, and public facts agree on {len(PAGES) + len(WIKI_SAMPLES)} pages")


if __name__ == "__main__":
    main()
