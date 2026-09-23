"""Build docs/sitemap.xml from the browser data so it lists every public route.

The wiki keeps its own sitemap (docs/wiki/sitemap.xml, written by
scripts/generate_html_wiki.py); this one lists the main pages, the wiki
index pages, and one URL per publication, story, and decade.

The sitemap carries no lastmod: a date that does not track real edits is
worse than none, and search engines ignore changefreq and priority.

    python3 scripts/build_sitemap.py          # write docs/sitemap.xml
    python3 scripts/build_sitemap.py --check  # fail if the file is stale
"""

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "sitemap.xml"
SITE = "https://centercoopmedia.github.io/njblackpress/"
PAGES = [
    "",
    "archive.html",
    "story.html",
    "era.html",
    "map.html",
    "historical-notes.html",
    "wiki/",
    "wiki/publications.html",
    "wiki/statistics.html",
    "wiki/featured.html",
    "wiki/cities.html",
    "wiki/decades.html",
    "wiki/formats.html",
]


def load(name: str) -> dict:
    return json.loads((DOCS / "data" / name).read_text(encoding="utf-8"))


def decade_of(value) -> str | None:
    """Mirror decadeOfYear() in docs/js/era.js."""
    match = re.search(r"\d{4}", str(value or ""))
    return match.group(0)[:3] + "0s" if match else None


def decades(publications: list[dict], events: list[dict]) -> list[str]:
    """Mirror indexByDecade() in docs/js/era.js: every decade that holds a record.

    Clippings are placed in their publication's decade, so they add none.
    """
    found = set()
    for pub in publications:
        decade = pub.get("decade") if pub.get("decade") not in (None, "", "Unknown") else decade_of(pub.get("yearFounded"))
        if decade:
            found.add(decade)
    for event in events:
        decade = decade_of(event.get("date"))
        if decade:
            found.add(decade)
    return sorted(found, key=lambda d: int(d[:4]))


def urls() -> list[str]:
    publications = load("publications.json")["publications"]
    stories = load("stories.json")["stories"]
    events = load("events.json")["events"]
    out = [SITE + page for page in PAGES]
    out += [f"{SITE}publication.html?id={pub['id']}" for pub in sorted(publications, key=lambda p: p["id"])]
    out += [f"{SITE}story.html?id={story['id']}" for story in stories]
    out += [f"{SITE}era.html?decade={decade}" for decade in decades(publications, events)]
    return out


def render() -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += [f"  <url><loc>{escape(url)}</loc></url>" for url in urls()]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if docs/sitemap.xml is stale")
    args = parser.parse_args()
    text = render()
    if args.check:
        if OUT.read_text(encoding="utf-8") != text:
            sys.exit("docs/sitemap.xml is stale; run python3 scripts/build_sitemap.py")
        print(f"docs/sitemap.xml is current ({text.count('<url>')} URLs)")
        return
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote docs/sitemap.xml ({text.count('<url>')} URLs)")


if __name__ == "__main__":
    main()
