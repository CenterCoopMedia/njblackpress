"""Regression checks for Woven's first-visit guidance, explicit controls, and
the history hall's naming rules."""

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "docs" / "historical-notes.html"
CSS_PATH = ROOT / "docs" / "css" / "woven-guide.css"
JS_PATH = ROOT / "docs" / "js" / "woven" / "guide.js"
DIALOG_PATH = ROOT / "docs" / "js" / "woven" / "guide-dialog.js"
STAGE_PATH = ROOT / "docs" / "js" / "woven" / "guide-stage.js"
HALL_DIR = ROOT / "docs" / "js" / "hall"
HALL_CSS_PATH = ROOT / "docs" / "css" / "hall.css"

# Words from the old textile metaphor. New interface language and new code use
# publication, sheet, frame, volume, page, reading table, and rail instead
# (hall-spec.md section 2). A handful of internal names are kept on purpose —
# see the allowlist below and WOVEN_REVIEW.md.
TEXTILE_WORDS = ["loom", "cloth", "weave", "thread", "warp", "weft", "stitch", "fabric"]
TEXTILE_RE = re.compile(r"\b(" + "|".join(TEXTILE_WORDS) + r")\b", re.IGNORECASE)

# Legacy identifiers kept for compatibility (hall-spec.md section 2: "the
# legacy color-token names where compatibility requires them") are not new
# interface language, so a textile word inside one of these exact names does
# not count as the word appearing in the file. The one-sentence note that
# names the internal/public boundary in layout.js and views.js is the
# documented allowlist entry for that boundary, not new prose.
ALLOWED_TEXTILE_TOKENS = re.compile(
    r"--thread-color|surface-cloth|link-thread|woven-key-thread|key-thread"
    r"|The woven model calls a publication[^\n]*\."
    # The retained data model's own field names (hall-spec.md section 15:
    # "model.tours[] has id, title, era, strength, people, thread, threadIds,
    # stops[]"). Reading that field is not new interface language.
    r"|\.threads?\b|\bthreadIds\b|\bthreadIndex\b|\bthreadColor\b"
)

# A "woven" match not glued to a hyphen, underscore, dot, or quote on either
# side is a standalone word, not part of an internal id, class, module path,
# or route alias (#woven-canvas, woven-btn, __woven, ../woven/records.js,
# view=woven, woven: 'hall').
LOOSE_WOVEN_RE = re.compile(r"(?<![-\w#.'\"_])[Ww]oven(?![-\w'\"_])")


class WovenParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []
        self.text_chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"] or "")
        if tag == "link" and values.get("rel") == "stylesheet" and values.get("href"):
            self.stylesheets.append(values["href"] or "")
        # Script and style bodies are code, not visible text.
        if tag in ("script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.text_chunks.append(data)


def hall_js_files() -> list[Path]:
    return sorted(HALL_DIR.glob("*.js"))


def visible_markup_text(js_source: str) -> str:
    """Text a visitor would read out of a hall module's own HTML templates.

    Hall modules build their DOM from backtick template literals, the same
    convention docs/js/woven/main.js uses. The text between '>' and '<' inside
    one of those templates is what renders; an attribute value such as
    id="woven-canvas" or a JS identifier outside a template never reaches
    this text, so it is not checked here.
    """
    chunks: list[str] = []
    for template in re.findall(r"`([^`]*)`", js_source, re.DOTALL):
        chunks += re.findall(r">([^<>{}]+)<", template)
    return " ".join(chunks)


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")
    js = JS_PATH.read_text(encoding="utf-8")
    dialog_js = DIALOG_PATH.read_text(encoding="utf-8")
    stage_js = STAGE_PATH.read_text(encoding="utf-8")
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
        # The history hall's own controls (hall-spec.md section 5: previous
        # and next publication, previous and next decade, the decade
        # navigator, back to entrance, wheel-navigation mode, and the
        # adaptive-tier control).
        "woven-hall-controls",
        "hall-previous-pub",
        "hall-next-pub",
        "hall-previous-decade",
        "hall-decade",
        "hall-next-decade",
        "hall-entrance",
        "hall-scroll-toggle",
        "hall-tier",
        "hall-tier-note",
        "hall-where",
        "hall-hint",
        "hall-reader",
        "hall-inspector",
    }
    assert required_ids.issubset(parser.ids), required_ids - set(parser.ids)
    assert "css/woven-guide.css" in parser.stylesheets
    assert "css/hall.css" in parser.stylesheets, "the hall's stylesheet must be linked"
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
    assert "createStartDialog" in js and "createStageCoordinator" in js
    assert "stopImmediatePropagation" in js
    assert "fetch('data/publications.json')" in js
    assert "window.njbpWoven?.open" in js
    assert "aria-activedescendant" in js
    assert "woven-mobile-tour" in js
    assert "woven-story-expanded" in js
    assert "Read story" in js and "More timeline" in js
    assert "closeSearchResults(true)" in js

    assert "aria-modal" in dialog_js
    assert "document.addEventListener('keydown', containFocus, true)" in dialog_js
    assert "event.key !== 'Tab' || !media.matches" in dialog_js
    assert "window.njbpWoven?.exit?.()" in stage_js
    assert "woven-help-card" in stage_js and "woven-tourpicker" in stage_js
    assert "MutationObserver(refreshChrome)" in stage_js
    assert "app?.labels?.update" in stage_js

    assert "#woven-search-results" in css
    assert "#woven-start-card" in css
    assert "#woven-more-tools" in css
    assert "body.woven-mobile-tour:not(.woven-story-expanded) #woven-card" in css
    assert "[data-guide-story-toggle]" in css

    assert len(css.splitlines()) <= 400, "split the guidance stylesheet before it exceeds 400 lines"
    assert len(js.splitlines()) <= 400, "split the guidance module before it exceeds 400 lines"
    assert len(dialog_js.splitlines()) <= 400
    assert len(stage_js.splitlines()) <= 400

    # ---- the history hall's naming rules (hall-spec.md section 2, section 15
    # decision 2, and the allowlist recorded in WOVEN_REVIEW.md) --------------
    canvas_help = html[html.index('id="woven-canvas-help"'):html.index("</p>", html.index('id="woven-canvas-help"'))]
    assert "history hall" in canvas_help.lower(), "the canvas help text must name the hall"

    hall_files = hall_js_files()
    assert hall_files, "docs/js/hall/ must hold the hall's modules"
    for path in hall_files:
        text = path.read_text(encoding="utf-8")
        first_line = text.splitlines()[0] if text.splitlines() else ""
        assert first_line.startswith("//"), f"{path.name} is missing its header comment"
        scrubbed = ALLOWED_TEXTILE_TOKENS.sub("", text)
        hits = TEXTILE_RE.findall(scrubbed)
        assert not hits, f"{path.name} uses a textile word outside the allowlist: {hits}"
        loose = LOOSE_WOVEN_RE.findall(visible_markup_text(text))
        assert not loose, f"{path.name} shows the word woven to a visitor"

    hall_css = HALL_CSS_PATH.read_text(encoding="utf-8")
    scrubbed_css = ALLOWED_TEXTILE_TOKENS.sub("", hall_css)
    css_hits = TEXTILE_RE.findall(scrubbed_css)
    assert not css_hits, f"hall.css uses a textile word outside the allowlist: {css_hits}"

    visible_text = " ".join(parser.text_chunks)
    text_textile_hits = TEXTILE_RE.findall(ALLOWED_TEXTILE_TOKENS.sub("", visible_text))
    assert not text_textile_hits, f"historical-notes.html shows a textile word: {text_textile_hits}"
    assert not LOOSE_WOVEN_RE.findall(visible_text), "historical-notes.html shows the word woven to a visitor"

    print("PASS: Woven has guided entry, explicit search, progressive tools, mobile story "
          "balance, and the hall never shows its internal name or the old textile words")


if __name__ == "__main__":
    main()
