"""Tests for the generated publication index table."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "wiki" / "publications.html"


def main() -> None:
    html = PAGE.read_text(encoding="utf-8")
    for key in ("publication", "city", "years", "status"):
        assert f'data-sort-key="{key}"' in html, f"missing {key} sort control"
    assert 'aria-sort="ascending"' in html, "missing the initial sort state"
    assert html.count('aria-sort=') == 1, "only the active header can have aria-sort"
    assert html.count('data-sort-value=') == 136 * 4, "publication rows lack sort values"
    assert "pl-5" in html and "pr-5" in html, "table edges lack the required cell padding"
    assert 'id="publication-index"' in html, "publication table lacks a script scope"
    assert "focus-visible:outline" in html, "sort controls lack a visible keyboard focus"
    assert 'src="../js/wiki-publications.js"' in html, "publication sort script is missing"
    print("PASS: the publication index has sortable headers and padded edge cells")


if __name__ == "__main__":
    main()
