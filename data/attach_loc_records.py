"""Attach Library of Congress newspaper directory records as publication evidence.

For each ID:LCCN pair, this script:
1. fetches https://www.loc.gov/item/<lccn>/?fo=json (the Directory of U.S.
   Newspapers in American Libraries) unless the excerpt already exists;
2. writes a small excerpt to data/research/loc/<lccn>.json, which is committed
   (research images are git-ignored, so a screenshot would not travel);
3. adds a catalog_record keeper to that publication in
   data/research/source-catalog.json, and a hit under chronicling_america;
4. adds a metadata_only entry for the excerpt to the rights manifest.

It is idempotent: a pair that is already attached is left alone. Run
data/add_evidence.py afterwards to rebuild the publication record.

    python3 data/attach_loc_records.py 16:sn84025698 38:sn87068175
"""

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOC_DIR = ROOT / "data" / "research" / "loc"
CATALOG_PATH = ROOT / "data" / "research" / "source-catalog.json"
MANIFEST_PATH = ROOT / "data" / "research" / "rights" / "rights-manifest.json"
SOURCE = "Library of Congress, Directory of U.S. Newspapers in American Libraries"


def item_url(lccn: str) -> str:
    return f"https://www.loc.gov/item/{lccn}/"


def fetch_excerpt(lccn: str) -> dict:
    request = urllib.request.Request(item_url(lccn) + "?fo=json", headers={"User-Agent": "njblackpress-archive/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        item = json.load(response)["item"]
    if item.get("library_of_congress_control_number") != lccn:
        raise SystemExit(f"{lccn}: LOC returned {item.get('library_of_congress_control_number')!r}")
    first = lambda key: (item.get(key) or [None])[0]  # noqa: E731
    return {
        "lccn": lccn,
        "url": item_url(lccn),
        "title": item.get("title"),
        "datesOfPublication": item.get("dates_of_publication"),
        "place": item.get("created_published") or [],
        "frequency": first("publication_frequency"),
        "notes": item.get("notes") or [],
        "subjectHeadings": item.get("subject_headings") or [],
        "precedingTitles": [t["label"] for t in item.get("preceding_titles") or []],
        "succeedingTitles": [t["label"] for t in item.get("succeeding_titles") or []],
        "oclc": item.get("number_oclc") or [],
        "fetched": date.today().isoformat(),
        "source": SOURCE,
    }


def caption(excerpt: dict) -> str:
    notes = " ".join(n if n.endswith((".", "?", '"')) else n + "." for n in excerpt["notes"][:3])
    return f"Library of Congress record {excerpt['lccn']}: {excerpt['title']}. {notes}"


def citation(excerpt: dict) -> str:
    return f"{excerpt['title']}, {SOURCE}, LCCN {excerpt['lccn']}, {excerpt['url']}"


def record_success(row: dict, excerpt: dict) -> None:
    """Qualify an earlier failed lookup note, so the catalog does not say both."""
    sources = row.get("sources", {}).get("chronicling_america")
    if not sources:
        return
    success = f"loc.gov item record {excerpt['lccn']} retrieved {excerpt['fetched']}."
    notes = sources.get("notes") or ""
    if success in notes:
        return
    if "lookup failed" in notes and "Chronicling America" not in notes:
        notes = notes.replace("lookup failed", "Chronicling America lookup failed", 1)
    sources["notes"] = f"{notes.rstrip('.')}; {success}" if notes else success


def main(pairs: list[str]) -> None:
    LOC_DIR.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in catalog["publications"]}
    manifest_paths = {entry["path"] for entry in manifest["files"]}

    for pair in pairs:
        pub_id, lccn = pair.split(":")
        pub_id = int(pub_id)
        path = LOC_DIR / f"{lccn}.json"
        rel = path.relative_to(ROOT).as_posix()
        if path.exists():
            excerpt = json.loads(path.read_text(encoding="utf-8"))
        else:
            excerpt = fetch_excerpt(lccn)
            path.write_text(json.dumps(excerpt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        row = rows[pub_id]
        if not any(k.get("url") == excerpt["url"] for k in row["keepers"]):
            keeper = {
                "kind": "catalog_record",
                "title": excerpt["title"],
                "caption": caption(excerpt),
                "url": excerpt["url"],
                "localFile": rel,
                "source": SOURCE,
                "date": excerpt["datesOfPublication"] or "",
            }
            row["keepers"].append(keeper)
            sources = row.setdefault("sources", {}).setdefault("chronicling_america", {"searched": True, "hits": [], "notes": ""})
            sources["searched"] = True
            sources.setdefault("hits", []).append({"kind": "catalog_record", "title": excerpt["title"], "url": excerpt["url"], "localFile": rel})
            row["status"] = "has_keeper"
        record_success(row, excerpt)
        entry = next((e for e in manifest["files"] if e["path"] == rel), None)
        if entry and pub_id not in entry["publicationIds"]:
            entry["publicationIds"].append(pub_id)
        if rel not in manifest_paths:
            manifest["files"].append({
                "path": rel,
                "source": SOURCE,
                "publicationIds": [pub_id],
                "status": "metadata_only",
                "citation": citation(excerpt),
                "cropPlan": "",
                "notes": "Catalog metadata from the Library of Congress. Cite the record and link to it; the excerpt is not an image.",
            })
            manifest_paths.add(rel)
        print(f"{pub_id} {row['name']} <- {lccn} {excerpt['title']} ({excerpt['datesOfPublication']})")

    statuses = [entry["status"] for entry in manifest["files"]]
    manifest["metadata"]["totalCount"] = len(statuses)
    manifest["metadata"]["byStatus"] = {status: statuses.count(status) for status in manifest["metadata"]["byStatus"] | dict.fromkeys(statuses)}

    counts = catalog["counts"]
    counts["keeper_total"] = sum(len(row["keepers"]) for row in catalog["publications"])
    counts["has_keeper"] = sum(1 for row in catalog["publications"] if row["keepers"])
    counts["searched_none"] = len(catalog["publications"]) - counts["has_keeper"]
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1:])
