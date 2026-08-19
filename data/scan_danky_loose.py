"""Looser Danky text search; cache the directory locally."""

from __future__ import annotations

import urllib.request
from pathlib import Path

URL = "https://archive.org/stream/africanamericanne00dank/africanamericanne00dank_djvu.txt"
CACHE = Path(__file__).resolve().parent / "research" / "danky-full.txt"
OUT = Path(__file__).resolve().parent / "research" / "danky-1950s-loose.txt"
UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}

NEEDLES = (
    "thrills",
    "informer",
    "hinton",
    "jersey camera",
    "hours after",
    "nite lite",
    "nite-lite",
    "club world",
    "north jersey independent",
    "tiny prince",
)


def main() -> None:
    if CACHE.exists() and CACHE.stat().st_size > 1_000_000:
        text = CACHE.read_text(encoding="utf-8", errors="replace")
    else:
        req = urllib.request.Request(URL, headers=UA)
        with urllib.request.urlopen(req, timeout=90) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        CACHE.write_text(text, encoding="utf-8")
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        l = line.lower()
        if any(n in l for n in NEEDLES):
            start = max(0, i - 3)
            end = min(len(lines), i + 8)
            hits.append(f"-- line {i} --\n" + "\n".join(lines[start:end]) + "\n")
    OUT.write_text("\n".join(hits[:60]) if hits else "no hits\n", encoding="utf-8")
    print("cached", CACHE.exists(), "bytes", CACHE.stat().st_size, "blocks", len(hits))


if __name__ == "__main__":
    main()
