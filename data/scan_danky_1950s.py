"""Find 1950s civic titles in the Danky directory text."""

from __future__ import annotations

import urllib.request
from pathlib import Path

URL = "https://archive.org/stream/africanamericanne00dank/africanamericanne00dank_djvu.txt"
OUT = Path(__file__).resolve().parent / "research" / "danky-1950s.txt"
UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}

NEEDLES = (
    "northern new jersey informer",
    "north jersey independent",
    "jersey camera",
    "hours after",
    "bronze thrills",
    "club world",
    "nite lite",
    "nite-lite",
    "the liberator",
    "theodore hinton",
    "albert e. hart",
    "tiny prince",
    "edna m. strothers",
    "sally cooke young",
)


def main() -> None:
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        l = line.lower()
        if any(n in l for n in NEEDLES):
            start = max(0, i - 2)
            end = min(len(lines), i + 8)
            hits.append(f"-- line {i} --\n" + "\n".join(lines[start:end]) + "\n")
    OUT.write_text("\n".join(hits) if hits else "no hits\n", encoding="utf-8")
    print("blocks", len(hits), "wrote", OUT)


if __name__ == "__main__":
    main()
