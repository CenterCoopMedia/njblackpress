"""Regression checks for Woven's first-visit guidance and explicit controls."""

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "docs" / "woven.html"
CSS_PATH = ROOT / "docs" / "css" / "woven-guide.css"
JS_PATH = ROOT / "docs" / "js" / "woven" / "guide.js"


class WovenParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"] or "")
        if tag == "link" and values.get("rel") == "stylesheet" and values.get("href"):
            self.stylesheets.append(values["href"] or "")


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    js = JS_PATH.read_text(encoding="utf-8")
    parser = WovenParser()
    parser.feed(html)

    duplicates = [element_id for element_id, count in Counter(parser.ids).items() if count > 1]
    assert not duplicates, f"duplicate element IDs: {duplicates}"

    required_ids = {
        "btn-start",
        "btn-tours",
        "btn-help",
        "btn-ghost",
        "btn-reset",
        "btn-fullscreen",
        "woven-more-tools",
        "woven-search",
        "woven-search-results",
        "woven-start-card",
        "woven-coach",
        "woven-tourbar",
    }
    assert required_ids.issubset(parser.ids), required_ids - set(parser.ids)
    assert "css/woven-guide.css" in parser.stylesheets
    assert "js/woven/guide.js" in parser.scripts
    assert parser.scripts.index("js/woven/guide.js") < parser.scripts.index("js/woven/main.js")

    details_start = html.index('<details id="woven-more-tools">')
    details_end = html.index("</details>", details_start)
    for control_id in ("btn-help", "btn-ghost", "btn-reset", "btn-fullscreen"):
        position = html.index(f'id="{control_id}"')
        assert details_start < position < details_end, f"{control_id} must stay under More tools"

    assert html.count('data-guide-action="story"') == 1
    assert html.count('data-guide-action="search"') == 1
    assert html.count('data-guide-action="explore"') == 1
    assert 'role="combobox"' in html
    assert 'role="listbox"' in html
    assert "Previous era" in html and "Next era" in html and "Whole timeline" in html

    assert "sessionStorage" in js
    assert "stopImmediatePropagation" in js
    assert "fetch('data/publications.json')" in js
    assert "window.njbpWoven?.open" in js
    assert "aria-activedescendant" in js
    assert "woven-mobile-tour" in js
    assert "woven-story-expanded" in js
    assert "Read story" in js and "More loom" in js

    assert "#woven-search-results" in css
    assert "#woven-start-card" in css
    assert "#woven-more-tools" in css
    assert "body.woven-mobile-tour:not(.woven-story-expanded) #woven-card" in css
    assert "[data-guide-story-toggle]" in css

    assert len(css.splitlines()) <= 400, "split the guidance stylesheet before it exceeds 400 lines"
    assert len(js.splitlines()) <= 400, "split the guidance module before it exceeds 400 lines"
    print("PASS: Woven has guided entry, explicit search, progressive tools, and mobile story balance")


if __name__ == "__main__":
    main()
