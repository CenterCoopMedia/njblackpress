"""Focused checks for the static publication map.

Run: python3 data/test_map.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from build_map_data import ROOT, visible_in_decade


CENTERS = ROOT / "data" / "municipality-centers.json"
SOURCE = ROOT / "data" / "publications.json"
MAP_DATA = ROOT / "data" / "map-publications.json"
DOCS_MAP_DATA = ROOT / "docs" / "data" / "map-publications.json"
MAP_HTML = ROOT / "docs" / "map.html"
MAP_JS = ROOT / "docs" / "js" / "map.js"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_generated_data_is_current() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "data" / "build_map_data.py"), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert MAP_DATA.read_text(encoding="utf-8") == DOCS_MAP_DATA.read_text(encoding="utf-8")
    print("PASS: generated map data is current and mirrored")


def test_every_city_value_has_one_rule() -> None:
    centers = load(CENTERS)
    source = load(SOURCE)
    mapped = {
        city
        for location in centers["locations"]
        for city in location["cityValues"]
    }
    unmapped = {item["city"] for item in centers["unmappedCityValues"]}
    source_values = {publication.get("city") for publication in source["publications"]}
    assert not mapped & unmapped, "A city value cannot be both mapped and unmapped"
    assert source_values == mapped | unmapped, "Every source city value needs one explicit map rule"
    print("PASS: every source city value has one map rule")


def test_coordinate_and_grouping_contract() -> None:
    payload = load(MAP_DATA)
    source = load(SOURCE)
    mapped_ids = []
    for location in payload["locations"]:
        assert 38 <= location["latitude"] <= 42
        assert -89 <= location["longitude"] <= -73
        ids = [publication["id"] for publication in location["publications"]]
        assert ids, f"{location['label']} has no publication records"
        mapped_ids.extend(ids)
    unmapped_ids = [publication["id"] for publication in payload["unmapped"]]
    assert len(mapped_ids) == len(set(mapped_ids)), "A publication must have one marker group"
    assert not set(mapped_ids) & set(unmapped_ids)
    assert set(mapped_ids) | set(unmapped_ids) == {publication["id"] for publication in source["publications"]}
    newark = next(location for location in payload["locations"] if location["id"] == "newark-nj")
    assert len(newark["publications"]) == 38, "Newark must remain one city marker with 38 records"
    assert {publication["city"] for publication in payload["unmapped"]} == {None, "Unknown"}
    assert any(location["id"] == "new-jersey-statewide" for location in payload["locations"])
    assert any(location["id"] == "fort-wayne-in" for location in payload["locations"])
    assert any(location["id"] == "chicago-il" for location in payload["locations"])
    print("PASS: marker groups and unmapped records are complete")


def test_decade_overlap_rule() -> None:
    assert visible_in_decade({"yearFounded": 1880, "yearCeased": 1880}, 1880, 1889, 2026)
    assert visible_in_decade({"yearFounded": 1904, "yearCeased": 1943}, 1940, 1949, 2026)
    assert not visible_in_decade({"yearFounded": 1904, "yearCeased": 1943}, 1950, 1959, 2026)
    assert visible_in_decade({"yearFounded": 2022, "yearCeased": None}, 2020, 2029, 2026)
    assert not visible_in_decade({"yearFounded": None, "yearCeased": 1979}, 1970, 1979, 2026)
    print("PASS: decade visibility uses inclusive lifespan overlap")


def test_map_page_contract() -> None:
    html = MAP_HTML.read_text(encoding="utf-8")
    javascript = MAP_JS.read_text(encoding="utf-8")
    assert "leaflet@1.9.4" in html
    assert "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" in html
    assert "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" in html
    assert 'id="decade-slider"' in html and 'type="range"' in html
    assert 'id="map-summary"' in html and 'aria-live="polite"' in html
    assert "tile.openstreetmap.org" in javascript
    assert "data/map-publications.json" in javascript
    assert "${count} ${countLabel(count)}" not in javascript
    print("PASS: page includes Leaflet, OSM tiles, and accessible map controls")


def main() -> None:
    test_generated_data_is_current()
    test_every_city_value_has_one_rule()
    test_coordinate_and_grouping_contract()
    test_decade_overlap_rule()
    test_map_page_contract()
    print("ALL MAP TESTS PASSED")


if __name__ == "__main__":
    main()
