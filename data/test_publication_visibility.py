"""Public listing holds must survive every generated publication surface."""

import copy
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

from add_evidence import public_payload


ROOT = Path(__file__).resolve().parent.parent
WITHHELD_IDS = {52, 99}  # Cassandra's October 30 editorial request.


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def check_csv_refresh_preserves_holds():
    """Run the real converter on a fresh synthetic export in an isolated tree."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data = root / "data"
        (data / "research/rights").mkdir(parents=True)
        (root / "docs/data").mkdir(parents=True)
        for name in ["convert_csv.py", "add_evidence.py", "activity.py"]:
            shutil.copyfile(ROOT / "data" / name, data / name)
        (data / "publications.json").write_text(json.dumps({"metadata": {}, "publications": [
            {"id": 52, "isPublic": False, "isActive": False},
            {"id": 1, "isActive": False},
        ]}))
        (data / "publications.csv").write_text("ID,Publication,Year founded,Year ceased\n52,Withheld title,1979,1985\n1,Public title,1880,1881\n")
        (data / "research/source-catalog.json").write_text(json.dumps({"publications": []}))
        (data / "research/rights/rights-manifest.json").write_text(json.dumps({"files": []}))
        subprocess.run([sys.executable, "convert_csv.py"], cwd=data, capture_output=True, text=True, check=True)
        source = json.loads((data / "publications.json").read_text())
        public = json.loads((root / "docs/data/publications.json").read_text())
        assert next(p for p in source["publications"] if p["id"] == 52)["isPublic"] is False
        assert [p["id"] for p in public["publications"]] == [1]


def main():
    editorial = load("data/publications.json")
    original = copy.deepcopy(editorial)
    source = {p["id"]: p for p in editorial["publications"]}
    assert len(source) == 136, "Listing holds must preserve the editorial records"
    assert {p["id"] for p in source.values() if p.get("isPublic") is False} == WITHHELD_IDS

    published = load("docs/data/publications.json")
    assert published == public_payload(editorial)
    assert editorial == original, "Public projection must not delete or change editorial records"
    public_ids = {p["id"] for p in published["publications"]}
    assert len(public_ids) == published["metadata"]["totalCount"] == 134
    assert public_ids == source.keys() - WITHHELD_IDS
    assert "Chicago/National" not in published["metadata"]["cities"]
    assert published["metadata"]["evidenceCount"] == sum(len(p["evidence"]) for p in published["publications"])

    for pid, founded in [(3, 1915), (37, 1934)]:
        pub = next(p for p in published["publications"] if p["id"] == pid)
        assert pub["yearFounded"] == founded and pub["yearCeased"] is None
        assert pub["isActive"] is False, "Unknown final year must not reactivate a historical title"
        assert pub["historicalNotes"]

    # Releasing an editorial hold restores the same record and its evidence.
    restored = copy.deepcopy(editorial)
    for pub in restored["publications"]:
        pub.pop("isPublic", None)
    assert {p["id"] for p in public_payload(restored)["publications"]} == source.keys()
    invalid = copy.deepcopy(editorial)
    invalid["publications"][0]["isPublic"] = None
    try:
        public_payload(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Malformed visibility must fail instead of silently publishing a record")

    mapped = load("docs/data/map-publications.json")
    map_ids = {p["id"] for group in mapped["locations"] for p in group["publications"]}
    map_ids.update(p["id"] for p in mapped["unmapped"])
    assert map_ids == public_ids and mapped["metadata"]["publicationCount"] == 134

    for directory, suffix in [("docs/wiki/publications", ".html"), ("okf/publications", ".md")]:
        page_ids = {int(p.name.split("-", 1)[0]) for p in (ROOT / directory).glob("*" + suffix)}
        assert page_ids == public_ids, f"{directory} exposes a withheld record or omits a public record"
    sitemap = (ROOT / "docs/sitemap.xml").read_text()
    for pid in WITHHELD_IDS:
        assert f"publication.html?id={pid}<" not in sitemap

    names = [source[pid]["name"] for pid in WITHHELD_IDS]
    for folder, patterns in [("docs", ["*.html", "*.txt", "*.xml"]), ("okf", ["*.md"]), ("docs/data", ["*.json"])]:
        for pattern in patterns:
            for path in (ROOT / folder).rglob(pattern):
                text = path.read_text(encoding="utf-8")
                assert not any(name in text for name in names), f"Withheld title appears in {path.relative_to(ROOT)}"
    for name, collection in [("clippings", "clippings"), ("wall-copies", "wallCopies"), ("events", "events"), ("stories", "stories")]:
        for row in load(f"docs/data/{name}.json")[collection]:
            assert not WITHHELD_IDS.intersection(row.get("publicationIds", []))
    for pub in load("docs/data/featured-publications.json")["featuredHistoric"] + load("docs/data/featured-publications.json")["featuredContemporary"]:
        assert pub["id"] in public_ids
        if pub["id"] == 37:
            assert pub["yearCeased"] is None and pub["historicalNotes"] == source[37]["historicalNotes"]

    check_csv_refresh_preserves_holds()

    print("PASS: 136 editorial records, 134 public records, reversible holds, unknown final years and no withheld public references")


if __name__ == "__main__":
    main()
