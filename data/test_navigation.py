"""Regression checks for cross-page fragment navigation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "docs" / "js" / "app.js").read_text(encoding="utf-8")
NAV = ROOT / "docs" / "js" / "site-nav.js"


def main() -> None:
    assert 'id="about"' in INDEX, "the About section lacks its fragment target"
    assert "function restoreInitialFragment()" in APP
    assert "await loadData();\n    restoreInitialFragment();" in APP
    nav = NAV.read_text(encoding="utf-8")
    for label in ("Home", "Timeline", "Archive", "Stories", "Eras", "Map", "Wiki", "Woven", "About"):
        assert f"label: '{label}'" in nav, f"global navigation lacks {label}"
    for page in ("index.html", "archive.html", "publication.html", "story.html", "era.html", "map.html", "woven.html"):
        html = (ROOT / "docs" / page).read_text(encoding="utf-8")
        assert 'js/site-nav.js' in html, f"{page} lacks the global navigation script"
    print("PASS: initial fragments are restored after publication cards render")


if __name__ == "__main__":
    main()
