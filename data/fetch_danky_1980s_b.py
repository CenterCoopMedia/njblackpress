"""Second batch of 1980s Danky leaves."""

from __future__ import annotations

import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "research" / "danky"
TPL = "https://archive.org/download/africanamericanne00dank/page/n{leaf}.jpg"
UA = {"User-Agent": "njblackpress-research/1.0"}

PAGES = {
    176: "corporate-176",
    435: "nubian-435",
    443: "oni-443",
    444: "oni-444",
    461: "perspectus-461",
    538: "starline-538",
    555: "testimony-555",
    579: "update-579",
    622: "write-on-622",
    342: "griot-342",
    392: "npsr-392",
    254: "gospel-254",
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
