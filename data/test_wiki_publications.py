"""Generated publication tables and verbatim editorial paragraph contracts."""

from html.parser import HTMLParser
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "wiki" / "publications.html"


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "p" and self.current is not None:
            self.values.append("".join(self.current))
            self.current = None


def check_editorial_copy():
    for pub in json.loads((ROOT / "docs/data/publications.json").read_text())["publications"]:
        notes = pub.get("historicalNotes") or ""
        if not notes:
            continue
        expected = [line for line in notes.strip().splitlines() if line.strip()]
        page, = (ROOT / "docs/wiki/publications").glob(f"{pub['id']:03d}-*.html")
        paragraphs = Paragraphs()
        paragraphs.feed(page.read_text())
        assert all(line in paragraphs.values for line in expected), f"{page.name}: Editorial paragraphs changed"
        markdown, = (ROOT / "okf/publications").glob(f"{pub['id']:03d}-*.md")
        assert "\n\n".join(expected) in markdown.read_text(), f"{markdown.name}: Editorial paragraphs changed"
    print("PASS: HTML and portable wikis preserve source editorial text and paragraphs")


def main() -> None:
    html = PAGE.read_text(encoding="utf-8")
    for key in ("publication", "city", "years", "status"):
        assert f'data-sort-key="{key}"' in html, f"missing {key} sort control"
    assert 'aria-sort="ascending"' in html, "missing the initial sort state"
    assert html.count('aria-sort=') == 1, "only the active header can have aria-sort"
    publications = json.loads((ROOT / "docs/data/publications.json").read_text())["publications"]
    assert html.count('data-sort-value=') == len(publications) * 4, "publication rows lack sort values"
    assert "pl-5" in html and "pr-5" in html, "table edges lack the required cell padding"
    assert 'id="publication-index"' in html, "publication table lacks a script scope"
    styles = (ROOT / "docs" / "css" / "styles.css").read_text(encoding="utf-8")
    assert 'href="../css/styles.css"' in html and ":focus-visible" in styles, "sort controls lack a visible keyboard focus"
    assert 'src="../js/wiki-publications.js"' in html, "publication sort script is missing"
    print("PASS: the publication index has sortable headers and padded edge cells")
    check_editorial_copy()


if __name__ == "__main__":
    main()
