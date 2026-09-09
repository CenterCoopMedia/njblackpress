"""Focused checks for the history hall's wall copies and their manifest.

Run: python3 data/test_hall_assets.py

These checks read only public files. They confirm that the derivative set is
exactly the eligible public clipping set, that the manifest describes what is on
disk, and that a repeat build writes nothing.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from make_wall_copies import (
    CLIPPINGS_PATH,
    DOCS,
    ELIGIBLE_STATUSES,
    ENCODER,
    EVIDENCE_DIR,
    MANIFEST_PATH,
    ROOT,
    WALL_DIR,
    scaled_size,
    stem_for,
)

BUILDER = ROOT / "data" / "make_wall_copies.py"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> list[dict]:
    assert MANIFEST_PATH.is_file(), "run python3 data/make_wall_copies.py first"
    with open(MANIFEST_PATH, encoding="utf-8") as handle:
        document = json.load(handle)
    assert document["metadata"]["encoder"] == ENCODER, "the manifest records the encoder settings once"
    return document["wallCopies"]


def eligible_clippings() -> list[dict]:
    with open(CLIPPINGS_PATH, encoding="utf-8") as handle:
        document = json.load(handle)
    clippings = document.get("clippings", document)
    return [c for c in clippings if (c.get("rightsStatus") or c.get("status")) in ELIGIBLE_STATUSES]


def test_derivative_set_matches_eligible_clippings() -> None:
    entries = load_manifest()
    expected = {stem_for(c["webPath"]) for c in eligible_clippings()}
    assert {e["id"] for e in entries} == expected, "the manifest must list every eligible public clipping and nothing else"
    on_disk = {p.stem for p in WALL_DIR.iterdir() if p.is_file()}
    assert on_disk == expected, "the wall directory must hold one copy per eligible clipping"
    assert len({e["wallPath"] for e in entries}) == len(entries), "output names are unique"
    assert len({e["id"] for e in entries}) == len(entries), "clipping ids are unique"
    print(f"PASS: {len(entries)} wall copies match the eligible public clippings")


def test_manifest_describes_what_is_on_disk() -> None:
    for entry in load_manifest():
        source = DOCS / entry["sourcePath"]
        wall = DOCS / entry["wallPath"]
        assert source.is_file(), f"{entry['id']}: missing public source"
        assert wall.is_file(), f"{entry['id']}: missing wall copy"
        assert sha256_file(source) == entry["sourceSha256"], f"{entry['id']}: source hash changed"
        assert sha256_file(wall) == entry["outputSha256"], f"{entry['id']}: output hash does not match the manifest"
        assert wall.read_bytes()[:3] == b"\xff\xd8\xff", f"{entry['id']}: wall copy is not a JPEG"
        with Image.open(wall) as image:
            assert image.format == "JPEG"
            assert (image.width, image.height) == (entry["outputWidth"], entry["outputHeight"])
        with Image.open(source) as image:
            assert (image.width, image.height) == (entry["sourceWidth"], entry["sourceHeight"])
        assert entry["status"] in ELIGIBLE_STATUSES, f"{entry['id']}: unknown rights status"
        assert entry["citation"], f"{entry['id']}: a published clipping needs its citation"
        assert entry["altText"], f"{entry['id']}: a published clipping needs alternative text"
        assert "encoder" not in entry, f"{entry['id']}: the encoder settings belong to the manifest, once"
    print("PASS: every manifest row matches its files, hashes, and required credit")


def test_dimension_bounds() -> None:
    for entry in load_manifest():
        width = entry["outputWidth"]
        height = entry["outputHeight"]
        assert 0 < width <= ENCODER["targetWidth"], f"{entry['id']}: wall copies are at most 400 px wide"
        assert max(width, height) <= ENCODER["maxLongEdge"], f"{entry['id']}: long edge is capped"
        assert width <= entry["sourceWidth"], f"{entry['id']}: never upscaled"
        assert height <= entry["sourceHeight"], f"{entry['id']}: never upscaled"
        # The whole approved public image is kept: one proportional scale, no crop.
        assert (width, height) == scaled_size(entry["sourceWidth"], entry["sourceHeight"]), (
            f"{entry['id']}: output size is not the proportional scale of the source"
        )
    print("PASS: wall copies keep their proportions inside the size bounds")


def test_paths_stay_inside_public_directories() -> None:
    evidence = EVIDENCE_DIR.resolve()
    wall = WALL_DIR.resolve()
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    assert "data/research" not in text, "the manifest must never name a research path"
    assert "sourcePath" in text and "../" not in text
    for entry in load_manifest():
        source = (DOCS / entry["sourcePath"]).resolve()
        output = (DOCS / entry["wallPath"]).resolve()
        assert source.is_relative_to(evidence), f"{entry['id']}: source outside the public evidence directory"
        assert source.parent != wall, f"{entry['id']}: a wall copy is not a source"
        assert output.parent == wall, f"{entry['id']}: output outside the wall directory"
        assert output.suffix == ".jpg", f"{entry['id']}: the extension must match the encoded format"
    print("PASS: no path leaves the public evidence and wall directories")


def test_repeat_build_writes_nothing() -> None:
    before = {p.name: (sha256_file(p), p.stat().st_mtime_ns) for p in sorted(WALL_DIR.iterdir()) if p.is_file()}
    manifest_before = (sha256_file(MANIFEST_PATH), MANIFEST_PATH.stat().st_mtime_ns)
    result = subprocess.run([sys.executable, str(BUILDER)], capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    assert "0 written" in result.stdout, f"a repeat build must rewrite nothing: {result.stdout.strip()}"
    after = {p.name: (sha256_file(p), p.stat().st_mtime_ns) for p in sorted(WALL_DIR.iterdir()) if p.is_file()}
    assert after == before, "a repeat build changed the wall copies"
    assert (sha256_file(MANIFEST_PATH), MANIFEST_PATH.stat().st_mtime_ns) == manifest_before, "a repeat build changed the manifest"
    check = subprocess.run([sys.executable, str(BUILDER), "--check"], capture_output=True, text=True, cwd=ROOT)
    assert check.returncode == 0, check.stderr
    print("PASS: the builder is deterministic and a second run rewrites nothing")


def main() -> None:
    test_derivative_set_matches_eligible_clippings()
    test_manifest_describes_what_is_on_disk()
    test_dimension_bounds()
    test_paths_stay_inside_public_directories()
    test_repeat_build_writes_nothing()
    print("ALL HALL ASSET TESTS PASSED")


if __name__ == "__main__":
    main()
