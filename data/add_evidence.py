"""Issue #33: add a per-publication evidence array to publications.json.

Deterministic build from three inputs:
  - data/publications.json          (138 publications, target of the update)
  - data/research/source-catalog.json (per-publication keepers)
  - data/research/rights/rights-manifest.json (per-file rights status/citation)

Run:
  python data/add_evidence.py

Writes data/publications.json and copies it to docs/data/publications.json.
No hand-editing of publications.json — this script is the only writer.
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
CATALOG_PATH = ROOT / "data" / "research" / "source-catalog.json"
MANIFEST_PATH = ROOT / "data" / "research" / "rights" / "rights-manifest.json"
DOCS_PUBLICATIONS_PATH = ROOT / "docs" / "data" / "publications.json"

VALID_SOURCES = {"newspapers.com", "wayback", "ia", "danky", "depth-hunt", "loc", "other"}

# data/research/<segment>/... -> evidence "source" enum value
SEGMENT_TO_SOURCE = {
    "newspapers-com": "newspapers.com",
    "wayback": "wayback",
    "ia": "ia",
    "danky": "danky",
    "depth-hunt": "depth-hunt",
    "loc": "loc",
}


def normalize_path(path):
    """Normalize a file path to forward slashes for cross-platform matching."""
    return path.replace("\\", "/") if path else path


def source_from_file(local_file):
    """Derive the evidence 'source' enum from a repo-relative localFile path."""
    if not local_file:
        return "other"
    parts = normalize_path(local_file).split("/")
    # Expect data/research/<segment>/...
    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "research":
        segment = parts[2]
        return SEGMENT_TO_SOURCE.get(segment, "other")
    return "other"


def build_rights_lookup(manifest):
    """Map normalized file path -> rights manifest entry."""
    lookup = {}
    for entry in manifest.get("files", []):
        path = normalize_path(entry.get("path"))
        if path:
            lookup[path] = entry
    return lookup


def build_evidence_for_publication(pub_catalog_entry, rights_lookup):
    """Build the evidence array for one publication's catalog entry."""
    evidence = []
    for keeper in pub_catalog_entry.get("keepers", []):
        local_file = normalize_path(keeper.get("localFile"))
        rights_entry = rights_lookup.get(local_file) if local_file else None

        if rights_entry:
            rights_status = rights_entry.get("status", "unlisted")
            citation = rights_entry.get("citation", "")
        else:
            rights_status = "unlisted"
            citation = ""

        evidence.append(
            {
                "type": keeper.get("kind", ""),
                "source": source_from_file(local_file),
                "date": keeper.get("date", "") or "",
                "caption": keeper.get("caption", "") or "",
                "file": local_file or "",
                "rightsStatus": rights_status,
                "citation": citation,
                "url": keeper.get("url", "") or "",
            }
        )
    return evidence


def main():
    publications_data = json.loads(PUBLICATIONS_PATH.read_text(encoding="utf-8"))
    catalog_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    rights_lookup = build_rights_lookup(manifest_data)
    catalog_by_id = {p["id"]: p for p in catalog_data["publications"]}

    total_evidence = 0
    pubs_with_evidence = 0
    pubs_without_evidence = 0

    for pub in publications_data["publications"]:
        catalog_entry = catalog_by_id.get(pub["id"])
        if catalog_entry is None:
            evidence = []
        else:
            evidence = build_evidence_for_publication(catalog_entry, rights_lookup)

        pub["evidence"] = evidence
        total_evidence += len(evidence)
        if evidence:
            pubs_with_evidence += 1
        else:
            pubs_without_evidence += 1

    publications_data["metadata"]["evidenceCount"] = total_evidence

    PUBLICATIONS_PATH.write_text(
        json.dumps(publications_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    shutil.copyfile(PUBLICATIONS_PATH, DOCS_PUBLICATIONS_PATH)

    print(
        f"evidence added: {total_evidence} entries across {pubs_with_evidence} pubs "
        f"({pubs_without_evidence} pubs with none)"
    )


if __name__ == "__main__":
    main()
