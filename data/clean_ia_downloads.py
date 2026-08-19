"""Download the best direct file (PDF, else large JPG) for Internet Archive keepers.

Reads data/research/source-catalog.json (read-only). Writes to
data/research/ia/clean/ and logs to data/research/ia/clean/ia-download-log.json.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "research" / "source-catalog.json"
OUT_DIR = ROOT / "data" / "research" / "ia" / "clean"
LOG_PATH = OUT_DIR / "ia-download-log.json"

IA_KINDS = {"full_issue", "full_issue_preview"}
UA = "njblackpress-archive-research/1.0 (amditisj@montclair.edu)"
DELAY = 4.0


def fetch(url: str, timeout: int = 120) -> bytes:
    """GET a URL with a descriptive user agent."""
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def identifiers(catalog_path: Path) -> list[dict[str, Any]]:
    """Return unique IA identifiers from keepers, with the first owning publication."""
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    seen: dict[str, dict[str, Any]] = {}
    for pub in data["publications"]:
        for keeper in pub.get("keepers", []):
            ident = keeper.get("identifier")
            if keeper.get("kind") not in IA_KINDS or not ident or ident in seen:
                continue
            seen[ident] = {
                "identifier": ident,
                "pub_id": pub["id"],
                "name": pub["name"],
                "url": keeper["url"],
                "old_file": keeper.get("localFile"),
            }
    return list(seen.values())


def pick_file(meta: dict[str, Any]) -> tuple[str, str, int] | None:
    """Choose the best downloadable file: PDF first, then largest JPEG."""
    files = meta.get("files", [])
    pdfs = [f for f in files if f.get("name", "").lower().endswith(".pdf")]
    if pdfs:
        best = max(pdfs, key=lambda f: int(f.get("size") or 0))
        return best["name"], "pdf", int(best.get("size") or 0)
    jpgs = [
        f
        for f in files
        if f.get("name", "").lower().endswith((".jpg", ".jpeg"))
        and "thumb" not in f.get("name", "").lower()
    ]
    if jpgs:
        best = max(jpgs, key=lambda f: int(f.get("size") or 0))
        return best["name"], "jpg", int(best.get("size") or 0)
    return None


def download_one(item: dict[str, Any]) -> dict[str, Any]:
    """Fetch metadata, pick the best file, and save it."""
    ident = item["identifier"]
    record: dict[str, Any] = {**item, "ok": False}
    try:
        meta = json.loads(fetch(f"https://archive.org/metadata/{ident}", timeout=60))
    except Exception as exc:  # noqa: BLE001
        record["notes"] = f"metadata failed: {exc}"
        return record
    choice = pick_file(meta)
    if not choice:
        record["notes"] = "no PDF or JPG in item"
        record["available"] = sorted({Path(f["name"]).suffix for f in meta.get("files", [])})
        return record
    name, kind, size = choice
    out_path = OUT_DIR / f"{ident}{Path(name).suffix.lower()}"
    record.update({"file_kind": kind, "remote_name": name, "remote_size": size})
    if out_path.exists() and out_path.stat().st_size == size:
        record.update({"ok": True, "file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                       "bytes": size, "notes": "already downloaded"})
        return record
    url = f"https://archive.org/download/{ident}/{urllib.parse.quote(name)}"
    try:
        data = fetch(url, timeout=300)
    except Exception as exc:  # noqa: BLE001
        record["notes"] = f"download failed: {exc}"
        return record
    out_path.write_bytes(data)
    record.update(
        {
            "ok": True,
            "file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": len(data),
            "download_url": url,
            "notes": "ok",
        }
    )
    return record


def main() -> int:
    """Entry point."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = identifiers(CATALOG)
    records = []
    for index, item in enumerate(items, start=1):
        record = download_one(item)
        print(
            f"[{index}/{len(items)}] {item['identifier']} -> "
            f"{record.get('ok')} {record.get('file_kind')} "
            f"{(record.get('bytes') or 0) // 1024}KB {record.get('notes')}",
            flush=True,
        )
        records.append(record)
        time.sleep(DELAY)
    LOG_PATH.write_text(
        json.dumps(
            {
                "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total": len(records),
                "ok": sum(1 for r in records if r["ok"]),
                "downloads": records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"done: {sum(1 for r in records if r['ok'])}/{len(records)} -> {LOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
