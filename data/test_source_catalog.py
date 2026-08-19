"""Prove source-catalog.json covers every publication and claimed files exist."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBS = ROOT / "data" / "publications.json"
CAT = ROOT / "data" / "research" / "source-catalog.json"
CLIPS = ROOT / "data" / "research" / "newspapers-com" / "clips"


def main() -> int:
    pubs = json.loads(PUBS.read_text(encoding="utf-8"))["publications"]
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    errors: list[str] = []

    pub_ids = {p["id"] for p in pubs}
    row_ids = set(rows)
    missing = sorted(pub_ids - row_ids)
    extra = sorted(row_ids - pub_ids)
    if missing:
        errors.append(f"catalog missing ids: {missing}")
    if extra:
        errors.append(f"catalog extra ids: {extra}")
    if cat.get("publicationCount") != len(pubs):
        errors.append(f"publicationCount {cat.get('publicationCount')} != {len(pubs)}")

    required = {"id", "name", "status", "sources", "keepers"}
    source_keys = {"newspapers_com", "internet_archive", "wayback", "chronicling_america", "other"}
    for pid, row in rows.items():
        if not required.issubset(row):
            errors.append(f"{pid} missing fields {required - set(row)}")
        if set(row.get("sources", {})) != source_keys:
            errors.append(f"{pid} bad source keys {list(row.get('sources', {}))}")
        if row["status"] == "has_keeper" and not row["keepers"]:
            errors.append(f"{pid} marked has_keeper but keepers empty")
        for hit in row.get("keepers", []):
            local = hit.get("localFile")
            if not local:
                errors.append(f"{pid} keeper missing localFile: {hit.get('url')}")
                continue
            path = ROOT / local if not Path(local).is_absolute() else Path(local)
            alt = CLIPS / Path(local).name
            if not path.exists() and not alt.exists():
                errors.append(f"{pid} missing localFile {local}")
            if not hit.get("url"):
                errors.append(f"{pid} keeper missing url: {hit}")
        for key, src in row.get("sources", {}).items():
            for src_hit in src.get("hits") or []:
                lf = src_hit.get("localFile")
                if not lf:
                    continue
                hp = ROOT / lf if not Path(lf).is_absolute() else Path(lf)
                if not hp.exists():
                    errors.append(f"{pid} {key} hit localFile missing {lf}")

    # Known keepers from this session must still be present.
    must = {
        10: "newspapers.com/image/1194114727",
        31: "newspapers.com/image/497174278",
        38: "newspapers.com/image/436807841",
        16: "archive.org/details/",
    }
    for pid, needle in must.items():
        urls = " ".join(h.get("url") or "" for h in rows[pid]["keepers"])
        if needle not in urls:
            errors.append(f"{pid} missing expected keeper containing {needle}")

    for key in source_keys:
        n = sum(1 for r in rows.values() if r["sources"][key]["searched"])
        if n != len(rows):
            errors.append(f"{key} searched {n} != {len(rows)}")
    fake = []
    for pid, row in rows.items():
        for key, src in row["sources"].items():
            note = src.get("notes") or ""
            if any(p in note for p in ("not re-run", "no additional IA", "this pass", "CDX not re-run")):
                fake.append(f"{pid} {key}: {note}")
    if fake:
        errors.append("bulk/fake search notes: " + "; ".join(fake[:8]))
    print(f"pubs={len(pubs)} catalog={len(rows)} counts={cat.get('counts')}")
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
