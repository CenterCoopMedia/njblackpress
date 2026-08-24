"""Tests for active-publication recent story data and rendering."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "recent-stories.json"
DOCS = ROOT / "docs" / "data" / "recent-stories.json"
PUBLICATION_JS = (ROOT / "docs" / "js" / "publication.js").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "data"))
from update_recent_stories import retain_previous


def main() -> None:
    assert DATA.read_text(encoding="utf-8") == DOCS.read_text(encoding="utf-8")
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    assert any(row["publicationId"] == 6 for row in payload["publications"])
    for row in payload["publications"]:
        assert 1 <= len(row["items"]) <= 5
        for item in row["items"]:
            assert item["title"] and item["url"].startswith("http") and item["published"]
    assert "buildRecentStoriesSection(pub)" in PUBLICATION_JS
    assert "data/recent-stories.json" in PUBLICATION_JS
    previous = {22: {"publicationId": 22, "items": [{"title": "Saved"}]}}
    retained = []
    assert retain_previous(retained, previous, 22)
    assert retained == [previous[22]]
    assert not retain_previous(retained, previous, 999)
    print("PASS: recent stories are valid and wired to active publication pages")


if __name__ == "__main__":
    main()
