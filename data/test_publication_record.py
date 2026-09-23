"""Checks that the published publication record matches its sources.

data/publications.json is written only by data/add_evidence.py. Two kinds of
drift reached the live site before this check existed: evidence citations
edited in the output but not in the rights manifest, and metadata lists
(decades, formats) that no longer described the records. This check rebuilds
both from their sources and needs no evidence image corpus.
"""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))

import add_evidence  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    record = load(ROOT / "data" / "publications.json")
    errors = []
    if record != load(ROOT / "docs" / "data" / "publications.json"):
        errors.append("docs/data/publications.json differs from data/publications.json")

    evidence_total = sum(len(pub["evidence"]) for pub in record["publications"])
    expected = add_evidence.derive_metadata(record["publications"], evidence_total)
    for key, value in expected.items():
        if record["metadata"].get(key) != value:
            errors.append(f"metadata.{key} is stale; run python3 data/add_evidence.py")

    catalog = {row["id"]: row for row in load(add_evidence.CATALOG_PATH)["publications"]}
    rights = add_evidence.build_rights_lookup(load(add_evidence.MANIFEST_PATH))
    for pub in record["publications"]:
        row = catalog.get(pub["id"])
        if row is None:
            errors.append(f"publication {pub['id']}: no row in the source catalog")
            continue
        rebuilt = add_evidence.build_evidence_for_publication(row, rights)
        if pub["evidence"] != rebuilt:
            errors.append(f"publication {pub['id']}: evidence differs from the source catalog and rights manifest")

    manifest = load(add_evidence.MANIFEST_PATH)
    statuses = [entry["status"] for entry in manifest["files"]]
    if manifest["metadata"]["totalCount"] != len(statuses):
        errors.append("rights manifest metadata.totalCount is stale")
    if manifest["metadata"]["byStatus"] != {s: statuses.count(s) for s in manifest["metadata"]["byStatus"] | dict.fromkeys(statuses)}:
        errors.append("rights manifest metadata.byStatus is stale")

    lccn = re.compile(r"^(sn)?\d{8,10}$")
    for pub in record["publications"]:
        for item in pub["evidence"]:
            if item["source"] == "loc" and item["file"].endswith(".json"):
                excerpt = load(ROOT / item["file"])
                if not lccn.match(excerpt.get("lccn", "")):
                    errors.append(f"{item['file']}: missing or malformed lccn")
                if item["url"] != f"https://www.loc.gov/item/{excerpt.get('lccn')}/":
                    errors.append(f"{item['file']}: evidence url does not match the catalog record")

    if errors:
        print("\n".join(errors))
        raise SystemExit(f"FAIL: {len(errors)} publication record problems")
    print(f"PASS: {len(record['publications'])} publications match their metadata, catalog, and rights sources")


if __name__ == "__main__":
    main()
