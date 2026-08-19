"""Download Danky leaves around BCALA Newsletter."""

from __future__ import annotations

import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "research" / "danky"
TPL = "https://archive.org/download/africanamericanne00dank/page/n{leaf}.jpg"
UA = {"User-Agent": "njblackpress-research/1.0"}

PAGES = {
    76: "bcala-76",
    77: "bcala-77",
    78: "bcala-78",
}


def main() -> None:
    for page, slug in PAGES.items():
        leaf = page + 43
        dest = OUT / f"danky-leaf-p{page}-n{leaf}-{slug}.jpg"
        url = TPL.format(leaf=leaf)
        print("GET", page, flush=True)
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
            dest.write_bytes(data)
            print("  wrote", dest.name, len(data), flush=True)
        except Exception as exc:
            print("  fail", exc, flush=True)


if __name__ == "__main__":
    main()
