"""Tests for docs/data/events.json and docs/data/stories.json (issue #34/#36).

Run:
  python data/test_site_data.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_EVENTS = ROOT / "data" / "events.json"
DATA_STORIES = ROOT / "data" / "stories.json"
DOCS_EVENTS = ROOT / "docs" / "data" / "events.json"
DOCS_STORIES = ROOT / "docs" / "data" / "stories.json"
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
DOCS_PUBLICATIONS_PATH = ROOT / "docs" / "data" / "publications.json"
MALFORMED_WAYBACK_URL = re.compile(r"^https://web\.archive\.org/web/\d{8,14}https?://")
LOWERCASE_AFTER_COLON = re.compile(r":\s+[a-z]")


def load():
    events = json.loads(DOCS_EVENTS.read_text(encoding="utf-8"))
    stories = json.loads(DOCS_STORIES.read_text(encoding="utf-8"))
    publications = json.loads(PUBLICATIONS_PATH.read_text(encoding="utf-8"))
    return events, stories, publications


def test_events_parse_and_count_match():
    events = json.loads(DOCS_EVENTS.read_text(encoding="utf-8"))
    assert "events" in events and "metadata" in events, "events.json missing top-level keys"
    actual = len(events["events"])
    declared = events["metadata"]["totalCount"]
    assert actual == declared, f"events totalCount {declared} != actual {actual}"
    print(f"PASS: events.json parses, totalCount matches ({actual})")


def test_stories_parse_and_count_match():
    stories = json.loads(DOCS_STORIES.read_text(encoding="utf-8"))
    assert "stories" in stories and "metadata" in stories, "stories.json missing top-level keys"
    actual = len(stories["stories"])
    declared = stories["metadata"]["totalCount"]
    assert actual == declared, f"stories totalCount {declared} != actual {actual}"
    print(f"PASS: stories.json parses, totalCount matches ({actual})")


def test_event_publication_ids_exist(events, publications):
    pub_ids = {p["id"] for p in publications["publications"]}
    bad = []
    for e in events["events"]:
        for pid in e.get("publicationIds", []):
            if pid not in pub_ids:
                bad.append((e["id"], pid))
    assert not bad, f"events referencing missing publicationIds: {bad[:10]} (total {len(bad)})"
    print("PASS: every event publicationId exists in publications.json")


def test_story_event_ids_exist(stories, events):
    event_ids = {e["id"] for e in events["events"]}
    bad = []
    for s in stories["stories"]:
        for eid in s.get("eventIds", []):
            if eid not in event_ids:
                bad.append((s["id"], eid))
    assert not bad, f"stories referencing missing eventIds: {bad[:10]} (total {len(bad)})"
    print("PASS: every story eventId exists in events.json")


def test_story_publication_ids_exist(stories, publications):
    pub_ids = {p["id"] for p in publications["publications"]}
    bad = []
    for s in stories["stories"]:
        for pid in s.get("publicationIds", []):
            if pid not in pub_ids:
                bad.append((s["id"], pid))
    assert not bad, f"stories referencing missing publicationIds: {bad[:10]} (total {len(bad)})"
    print("PASS: every story publicationId exists in publications.json")


def test_data_and_docs_copies_identical():
    pairs = [(DATA_EVENTS, DOCS_EVENTS), (DATA_STORIES, DOCS_STORIES)]
    for src, dst in pairs:
        src_text = src.read_text(encoding="utf-8")
        dst_text = dst.read_text(encoding="utf-8")
        assert src_text == dst_text, f"{src} and {dst} differ"
    print("PASS: data/ and docs/data/ copies of events.json and stories.json are identical")


def test_wayback_urls_include_snapshot_separator():
    bad = []
    for path in (PUBLICATIONS_PATH, DOCS_PUBLICATIONS_PATH):
        data = json.loads(path.read_text(encoding="utf-8"))
        for publication in data["publications"]:
            for evidence in publication.get("evidence", []):
                url = evidence.get("url") or ""
                if MALFORMED_WAYBACK_URL.match(url):
                    bad.append((str(path.relative_to(ROOT)), publication["id"], url))
    assert not bad, f"Wayback URLs missing the snapshot separator: {bad}"
    print("PASS: Wayback URLs include the separator after the snapshot timestamp")


def test_visible_text_uses_capital_after_colon():
    visible_fields = {"title", "description", "thread", "historicalNotes", "missionStatement", "caption"}
    sources = (
        ("publications", PUBLICATIONS_PATH),
        ("events", DATA_EVENTS),
        ("stories", DATA_STORIES),
    )
    bad = []
    for collection, path in sources:
        rows = json.loads(path.read_text(encoding="utf-8"))[collection]
        for row in rows:
            for key, value in row.items():
                if key in visible_fields and isinstance(value, str):
                    prose = re.sub(r"\b(?:LCCN|OCLC):\s*\w+", "", value)
                    if LOWERCASE_AFTER_COLON.search(prose):
                        bad.append((collection, row.get("id"), key))
    assert not bad, f"Visible text has lowercase text after a colon: {bad}"
    print("PASS: visible text uses a capital letter after each colon")


def main():
    test_events_parse_and_count_match()
    test_stories_parse_and_count_match()
    events, stories, publications = load()
    test_event_publication_ids_exist(events, publications)
    test_story_event_ids_exist(stories, events)
    test_story_publication_ids_exist(stories, publications)
    test_data_and_docs_copies_identical()
    test_wayback_urls_include_snapshot_separator()
    test_visible_text_uses_capital_after_colon()
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
