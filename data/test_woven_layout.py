"""Regression checks for the loom width when its docked key is hidden."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "docs" / "css" / "woven.css").read_text(encoding="utf-8")
LABELS = (ROOT / "docs" / "js" / "woven" / "labels.js").read_text(encoding="utf-8")
MAIN = (ROOT / "docs" / "js" / "woven" / "main.js").read_text(encoding="utf-8")


def main() -> None:
    assert "#woven-stage.woven-legend-hidden #woven-canvas" in CSS
    assert "#woven-stage.woven-legend-hidden #woven-chrome" in CSS
    assert "stage.classList.toggle('woven-legend-hidden', busy)" in LABELS
    assert "app.resize = resize" in MAIN
    assert "state.scrollTwin = !!opts.scrollTwin" in MAIN
    assert "if (!opts.silent && !opts.fromTwin) panel.openPublication" in MAIN
    print("PASS: the loom reclaims the dock width when the key is hidden")


if __name__ == "__main__":
    main()
