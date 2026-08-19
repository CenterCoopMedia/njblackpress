"""Attach local preview files to keepers that only have URLs."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAT_PATH = ROOT / "research" / "source-catalog.json"
IA_DIR = ROOT / "research" / "wayback" / "ia-issues"
IA_DIR.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "njblackpress-research/1.0"}


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as resp:
            dest.write_bytes(resp.read())
        return dest.stat().st_size > 500
    except Exception as exc:
        print("fail", url, exc)
        return False


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    downloaded = 0
    attached = 0
    for row in cat["publications"]:
        for hit in row.get("keepers", []):
            ident = hit.get("identifier")
            url = hit.get("url") or ""
            if "archive.org/details/" in url and not ident:
                ident = url.rstrip("/").split("/")[-1]
                hit["identifier"] = ident
            if ident:
                dest = IA_DIR / f"{ident}.jpg"
                rel = str(dest.relative_to(ROOT.parent)).replace("\\", "/")
                if not dest.exists():
                    if download(f"https://archive.org/services/img/{ident}", dest):
                        downloaded += 1
                        print("thumb", dest.name, dest.stat().st_size)
                    time.sleep(0.25)
                if dest.exists():
                    hit["localFile"] = rel
                    attached += 1
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("downloaded", downloaded, "attached", attached)


if __name__ == "__main__":
    main()
