"""Print historic print titles from publications.json."""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path(__file__).with_name("publications.json")


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    pubs = data["publications"]
    print(f"count={len(pubs)} meta={data['metadata']['totalCount']}")
    rows = []
    for pub in pubs:
        year = pub.get("yearFounded") or 9999
        fmt = (pub.get("format") or "").lower()
        if year <= 2000 or "newspaper" in fmt:
            rows.append(pub)
    rows.sort(key=lambda p: (p.get("yearFounded") or 9999, p["name"]))
    for pub in rows:
        print(
            f"{pub['id']}|{pub['name']}|{pub.get('city')}|{pub.get('yearFounded')}-"
            f"{pub.get('yearCeased')}|{pub.get('format')}|archive={bool(pub.get('archiveUrl'))}"
        )


if __name__ == "__main__":
    main()
