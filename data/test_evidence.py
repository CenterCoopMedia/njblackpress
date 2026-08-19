"""Tests for the evidence array added by data/add_evidence.py (issue #33).

Run:
  python data/test_evidence.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
CATALOG_PATH = ROOT / "data" / "research" / "source-catalog.json"

VALID_RIGHTS_STATUSES = {
    "publishable",
    "publishable_with_credit",
    "crop_first",
    "metadata_only",
    "unlisted",
}


def load():
    publications_data = json.loads(PUBLICATIONS_PATH.read_text(encoding="utf-8"))
    catalog_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return publications_data, catalog_data


def test_evidence_files_exist_on_disk(publications_data):
    missing = []
    for pub in publications_data["publications"]:
        for e in pub.get("evidence", []):
            file_path = e.get("file")
            if not file_path:
                missing.append((pub["id"], "<empty file field>"))
                continue
            if not (ROOT / file_path).exists():
                missing.append((pub["id"], file_path))
    assert not missing, f"evidence files missing on disk: {missing[:10]} (total {len(missing)})"
    print("PASS: all evidence files exist on disk")


def test_rights_status_valid(publications_data):
    bad = []
    for pub in publications_data["publications"]:
        for e in pub.get("evidence", []):
            status = e.get("rightsStatus")
            if status not in VALID_RIGHTS_STATUSES:
                bad.append((pub["id"], e.get("file"), status))
    assert not bad, f"invalid rightsStatus values: {bad[:10]} (total {len(bad)})"
    print("PASS: all rightsStatus values are valid enum or 'unlisted'")


def test_pubs_with_keepers_have_evidence(publications_data, catalog_data):
    catalog_by_id = {p["id"]: p for p in catalog_data["publications"]}
    empty = []
    for pub in publications_data["publications"]:
        catalog_entry = catalog_by_id.get(pub["id"])
        if catalog_entry and catalog_entry.get("keepers"):
            if not pub.get("evidence"):
                empty.append(pub["id"])
    assert not empty, f"pubs with catalog keepers but empty evidence: {empty}"
    print("PASS: every publication with catalog keepers has a non-empty evidence array")


def test_counts_reconcile(publications_data, catalog_data):
    catalog_by_id = {p["id"]: p for p in catalog_data["publications"]}

    total_evidence = sum(len(pub.get("evidence", [])) for pub in publications_data["publications"])
    total_keepers = sum(len(p.get("keepers", [])) for p in catalog_data["publications"])
    assert total_evidence == total_keepers, (
        f"evidence total {total_evidence} != catalog keeper total {total_keepers}"
    )

    metadata_count = publications_data["metadata"].get("evidenceCount")
    assert metadata_count == total_evidence, (
        f"metadata.evidenceCount {metadata_count} != actual evidence total {total_evidence}"
    )

    pubs_with_evidence = sum(1 for pub in publications_data["publications"] if pub.get("evidence"))
    pubs_with_keepers = sum(1 for p in catalog_data["publications"] if p.get("keepers"))
    assert pubs_with_evidence == pubs_with_keepers, (
        f"pubs with evidence {pubs_with_evidence} != pubs with catalog keepers {pubs_with_keepers}"
    )

    print(
        f"PASS: counts reconcile ({total_evidence} evidence entries, "
        f"{pubs_with_evidence} pubs with evidence)"
    )


def test_every_publication_has_evidence_key(publications_data, catalog_data):
    missing_key = [p["id"] for p in publications_data["publications"] if "evidence" not in p]
    assert not missing_key, f"publications missing 'evidence' key: {missing_key}"
    catalog_ids = {p["id"] for p in catalog_data["publications"]}
    pub_ids = {p["id"] for p in publications_data["publications"]}
    assert pub_ids == catalog_ids, (
        f"id mismatch between publications.json and source-catalog.json: "
        f"{pub_ids.symmetric_difference(catalog_ids)}"
    )
    print("PASS: every publication has an evidence key, ids match the catalog")


def main():
    publications_data, catalog_data = load()
    test_evidence_files_exist_on_disk(publications_data)
    test_rights_status_valid(publications_data)
    test_pubs_with_keepers_have_evidence(publications_data, catalog_data)
    test_counts_reconcile(publications_data, catalog_data)
    test_every_publication_has_evidence_key(publications_data, catalog_data)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
