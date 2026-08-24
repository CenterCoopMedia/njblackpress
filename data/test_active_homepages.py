"""Tests for the bounded active-homepage capture pipeline."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "current-homepages.json"
DOCS = ROOT / "docs" / "data" / "current-homepages.json"
SOURCES = ROOT / "data" / "active-homepage-sources.json"
PUBLICATIONS = ROOT / "data" / "publications.json"
SCRIPT = ROOT / "data" / "capture_active_homepages.py"
PUBLICATION_JS = ROOT / "docs" / "js" / "publication.js"
LIVE_SITES = ROOT / "data" / "research" / "live-sites"
CURRENT_SITES = ROOT / "data" / "research" / "current-sites"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def valid_http_url(value) -> bool:
    if not isinstance(value, str) or value != value.strip() or not value:
        return False
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def png_text(path: Path) -> dict[str, str]:
    """Read PNG tEXt chunks with the standard library."""

    raw = path.read_bytes()
    assert raw.startswith(b"\x89PNG\r\n\x1a\n"), f"not a PNG: {path}"
    offset = 8
    result = {}
    while offset < len(raw):
        length = struct.unpack(">I", raw[offset : offset + 4])[0]
        kind = raw[offset + 4 : offset + 8]
        payload = raw[offset + 8 : offset + 8 + length]
        if kind == b"tEXt" and b"\0" in payload:
            key, value = payload.split(b"\0", 1)
            result[key.decode("latin-1")] = value.decode("latin-1")
        offset += length + 12
        if kind == b"IEND":
            break
    return result


def png_dimensions(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")
    assert raw[12:16] == b"IHDR"
    return struct.unpack(">II", raw[16:24])


def test_manifest_matches_active_valid_urls() -> None:
    sources = load(SOURCES)["sources"]
    publications = {row["id"]: row for row in load(PUBLICATIONS)["publications"]}
    assert sources
    source_ids = {row["publicationId"] for row in sources}
    expected_ids = {
        row["id"]
        for row in publications.values()
        if row.get("isActive") is True and valid_http_url(row.get("websiteUrl"))
    }
    assert source_ids == expected_ids
    assert len(source_ids) == len(sources)
    for source in sources:
        publication = publications[source["publicationId"]]
        assert publication["isActive"] is True
        assert source["name"] == publication["name"]
        assert source["url"] == publication["websiteUrl"]
        assert valid_http_url(source["url"])
    print(f"PASS: manifest has {len(sources)} active publications with valid HTTP URLs")


def test_pipeline_is_bounded_and_keeps_single_file_out_of_docs() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "concurrency" in source
    assert "max-parallel-workers" not in source
    assert "single-file" in source
    assert "full_page=False" in source
    assert "LIVE_SITES_DIR" in source
    assert "DOCS_CURRENT_HOMEpages_PATH" in source
    assert "docs/research/live-sites" not in source
    print("PASS: pipeline uses one worker, SingleFile, and viewport screenshots")


def test_data_copies_match_and_schema_is_valid() -> None:
    assert DATA.read_text(encoding="utf-8") == DOCS.read_text(encoding="utf-8")
    payload = load(DATA)
    metadata = payload["metadata"]
    captures = payload["homepages"]
    failures = payload["failures"]
    assert metadata["concurrency"] == 1
    assert metadata["viewport"] == {"width": 1440, "height": 900}
    assert metadata["captureCount"] == len(captures)
    assert metadata["failureCount"] == len(failures)
    assert metadata["attemptedCount"] == len(load(SOURCES)["sources"])
    assert metadata["attemptedCount"] >= len(captures)
    assert metadata["rights"]["status"] == "crop_first"
    assert len(captures) >= 1, "the capture run should retain at least one success"

    seen = set()
    for capture in captures:
        publication_id = capture["publicationId"]
        assert publication_id not in seen
        seen.add(publication_id)
        assert capture["status"] == "captured"
        assert valid_http_url(capture["sourceUrl"])
        assert capture["screenshotPath"].startswith("data/research/current-sites/")
        assert capture["singleFilePath"] is None or capture["singleFilePath"].startswith(
            "data/research/live-sites/"
        )
        assert capture["rights"]["status"] == "crop_first"
        screenshot = ROOT / capture["screenshotPath"]
        assert screenshot.is_file() and screenshot.stat().st_size > 100
        assert png_dimensions(screenshot) == (1440, 900)
        text = png_text(screenshot)
        assert text["Source URL"] == capture["sourceUrl"]
        assert text["Capture date"] == capture["captureDate"]
        assert text["Viewport"] == "1440x900"
        if capture["singleFilePath"]:
            html = ROOT / capture["singleFilePath"]
            assert html.is_file() and html.stat().st_size > 512
            assert html.is_relative_to(LIVE_SITES)
    print(f"PASS: {len(captures)} homepage captures have HTML and screenshot records")


def test_publication_page_withholds_restricted_captures() -> None:
    source = PUBLICATION_JS.read_text(encoding="utf-8")
    assert "data/current-homepages.json" in source
    assert "buildCurrentHomepageSection(pub)" in source
    assert "capture.sourceUrl" in source
    assert "publishableCaptureStatuses" in source
    assert "capture.screenshotPath" in source
    assert "singleFilePath" not in source, "research-only SingleFile paths must not be published"
    assert "crop_first" not in source.split("publishableCaptureStatuses", 1)[1].split(";", 1)[0]
    print("PASS: active publication pages withhold crop-first screenshots and SingleFile files")


def main() -> None:
    test_manifest_matches_active_valid_urls()
    test_pipeline_is_bounded_and_keeps_single_file_out_of_docs()
    test_data_copies_match_and_schema_is_valid()
    test_publication_page_withholds_restricted_captures()
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
