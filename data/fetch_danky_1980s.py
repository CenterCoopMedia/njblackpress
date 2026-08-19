"""Download Danky leaves for 1980s civic titles."""

from __future__ import annotations

import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "research" / "danky"
TPL = "https://archive.org/download/africanamericanne00dank/page/n{leaf}.jpg"
UA = {"User-Agent": "njblackpress-research/1.0"}

PAGES = {
    91: "black-nj-mag",
    113: "bootstrap",
    114: "bootstrap-114",
    154: "city-news",
    155: "city-news-155",
    167: "communique",
    168: "communique-168",
    171: "connection",
    172: "connection-172",
    177: "corporate-hq",
    343: "literary-griot",
    427: "aahgs",
    436: "nubian",
    445: "oni",
    460: "perspectus",
    539: "starline",
    556: "testimony",
    580: "update",
    581: "update-581",
    623: "write-on",
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
