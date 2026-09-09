"""Regression checks for the flat timeline's dock layout and for issue 72's
removal of the unused 3D-exhibit mesh and pluck/fray state from main.js."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "docs" / "css" / "woven.css").read_text(encoding="utf-8")
LABELS = (ROOT / "docs" / "js" / "woven" / "labels.js").read_text(encoding="utf-8")
MAIN = (ROOT / "docs" / "js" / "woven" / "main.js").read_text(encoding="utf-8")
HTML = (ROOT / "docs" / "historical-notes.html").read_text(encoding="utf-8")


def main() -> None:
    assert "#woven-stage.woven-legend-hidden #woven-canvas" in CSS
    assert "#woven-stage.woven-legend-hidden #woven-chrome" in CSS
    # These offsets and the flat timeline's own zoom controls used to live in
    # the now-deleted woven-exhibit.css; they moved here so the year rail, the
    # DOM labels, and the era markers still dock correctly beside the
    # publication index and record panel.
    assert "#woven-stage #woven-yearrail { right: var(--exhibit-dock" in CSS
    assert "#woven-stage #woven-labels, #woven-stage #woven-eras { right: var(--exhibit-dock" in CSS
    assert "#woven-timeline-controls" in CSS
    assert "stage.classList.toggle('woven-legend-hidden', busy)" in LABELS
    assert "app.resize = resize" in MAIN
    assert "state.scrollTwin = !!opts.scrollTwin" in MAIN
    assert "if (!opts.silent && !opts.fromTwin) panel.openPublication" in MAIN

    # Issue 72: main.js no longer allocates the two unused decade-grid meshes,
    # never adds them to the scene, and no longer drives the pluck ripple that
    # shaders.js does not otherwise use. cloth.js still exports buildWarp for
    # data/test_woven_model.mjs and shaders.js still declares the pluck and
    # fray uniforms unused, per hall-spec.md section 15's tooling facts and
    # the instruction to leave a uniform a shader still declares.
    for removed in ("warpFull", "warpCoarse", "buildWarp", "pluckUniforms", "canHover"):
        assert removed not in MAIN, f"issue 72 removed {removed} from main.js"

    # The obsolete 3D-exhibit stylesheet and its exhibit-only markup are gone.
    assert "woven-exhibit.css" not in HTML
    assert "css/hall.css" in HTML
    for removed_id in ("woven-exhibit-axis", "woven-turn-controls", "woven-exhibit-caption", "woven-motion"):
        assert f'id="{removed_id}"' not in HTML, f"{removed_id} should have been removed with the 3D exhibit"

    print("PASS: the flat timeline reclaims the dock width when the key is hidden, "
          "and issue 72's dead mesh and pluck state are gone from main.js")


if __name__ == "__main__":
    main()
