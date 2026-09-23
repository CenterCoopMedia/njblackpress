"""Regression checks for the shared design system.

The site once carried two names for each colour, a second palette and font
set on the map, six footer variants, and per-page focus rules. These checks
keep one vocabulary, one footer, one focus style, and one font set.
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PAGES = ["index.html", "archive.html", "publication.html", "story.html", "era.html", "map.html", "historical-notes.html"]
WIKI = ROOT / "scripts" / "generate_html_wiki.py"
FONTS = "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300..700&family=Libre+Franklin:wght@400..900&display=swap"
LEGACY = re.compile(r"(?<![\w-])(?:[a-z0-9-]+:)*(?:bg|text|border|outline|placeholder|ring|from|via|to|divide|decoration|fill|stroke|shadow|caret)-(?:ink|paper|accent)(?![\w])")
OFF_PALETTE = re.compile(r"(?<![\w-])(?:[a-z0-9-]+:)*(?:bg|text|border)-(?:white|black|gray|slate|zinc|neutral|stone|red|orange|amber|yellow|blue|sky|indigo|pink|rose)(?:-\d+)?(?:/\d+)?(?![\w-])")


def sources() -> list[Path]:
    files = [DOCS / page for page in PAGES] + [WIKI]
    files += sorted(p for p in (DOCS / "js").rglob("*.js"))
    return files


def main() -> None:
    errors = []
    config = (ROOT / "tailwind.config.js").read_text(encoding="utf-8")
    for alias in ("ink:", "paper:", "accent:"):
        if alias in config:
            errors.append(f"tailwind.config.js still defines the legacy {alias[:-1]} alias")
    tokens = (ROOT / "src" / "input.css").read_text(encoding="utf-8")
    for name in ("--walnut-900", "--linen-100", "--stain", "--stain-light", "--mono", "--font-display"):
        if name not in tokens:
            errors.append(f"src/input.css does not define {name}")

    for path in sources():
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        for match in LEGACY.finditer(text):
            errors.append(f"{rel}: legacy colour class {match.group(0)}")
        for match in OFF_PALETTE.finditer(text):
            errors.append(f"{rel}: off-palette colour class {match.group(0)}")
        if "focus:outline-none" in text:
            errors.append(f"{rel}: focus:outline-none hides the shared focus ring")
        for font in ("Fraunces", "DM Mono", "DM+Mono"):
            if font in text:
                errors.append(f"{rel}: loads or names the retired font {font}")

    for page in PAGES:
        html = (DOCS / page).read_text(encoding="utf-8")
        for needle in ('href="css/tailwind.css"', 'href="css/styles.css"', FONTS, "<footer data-site-footer", "js/site-nav.js"):
            if needle not in html:
                errors.append(f"{page}: missing {needle}")
        if html.count("<footer") != 1:
            errors.append(f"{page}: has {html.count('<footer')} footers; use the shared one")
        footer_at = html.find("<footer data-site-footer")
        if footer_at != -1 and footer_at < html.find("</main>"):
            errors.append(f"{page}: the site footer sits inside <main>")
    wiki = WIKI.read_text(encoding="utf-8")
    for needle in (FONTS, "<footer data-site-footer", 'class="skip-link"', 'id="main-content"'):
        if needle not in wiki:
            errors.append(f"wiki template: missing {needle}")

    # A custom property that no stylesheet defines makes its declaration
    # invalid, so the colour silently falls back (the map lost its counts' colour this way).
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", tokens))
    for css in [DOCS / page for page in PAGES] + sorted((DOCS / "css").glob("*.css")):
        if css.name == "tailwind.css":
            continue
        text = css.read_text(encoding="utf-8")
        defined |= set(re.findall(r"(--[a-z0-9-]+)\s*:", text))
    for script in (DOCS / "js").rglob("*.js"):
        defined |= set(re.findall(r"setProperty\(\s*'(--[a-z0-9-]+)'", script.read_text(encoding="utf-8")))
    for css in [DOCS / page for page in PAGES] + sorted((DOCS / "css").glob("*.css")):
        if css.name == "tailwind.css":
            continue
        for name in sorted(set(re.findall(r"var\((--[a-z0-9-]+)\)", css.read_text(encoding="utf-8"))) - defined):
            errors.append(f"{css.relative_to(ROOT)}: var({name}) is never defined")

    styles = (DOCS / "css" / "styles.css").read_text(encoding="utf-8")
    if ":is(a, button, input, select, textarea, summary, [tabindex]):focus-visible" not in styles:
        errors.append("docs/css/styles.css lacks the shared focus rule")

    if errors:
        print("\n".join(errors))
        raise SystemExit(f"FAIL: {len(errors)} design system problems")
    print(f"PASS: one palette, one font set, one footer, and one focus style across {len(PAGES)} pages and the wiki")


if __name__ == "__main__":
    main()
