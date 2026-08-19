"""Download Danky directory plain text and search the four titles."""

from __future__ import annotations

import urllib.request
from pathlib import Path

URL = "https://archive.org/stream/africanamericanne00dank/africanamericanne00dank_djvu.txt"
OUT = Path(__file__).resolve().parent / "research" / "danky-hits.txt"
UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}

NEEDLES = (
    "apex news",
    "apex publishing",
    "archie j. morgan",
    "hiram star",
    "camden news",
    "the citizen",
    "du paur",
    "auston",
    "princeton",
    "vauxhall",
)


def main() -> None:
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    low = text.lower()
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        l = line.lower()
        if any(n in l for n in NEEDLES):
            start = max(0, i - 3)
            end = min(len(lines), i + 4)
            chunk = "\n".join(lines[start:end])
            hits.append(f"-- line {i} --\n{chunk}\n")
    OUT.write_text("\n".join(hits) if hits else "no hits\n", encoding="utf-8")
    print("chars", len(text), "hit_blocks", len(hits), "wrote", OUT)


if __name__ == "__main__":
    main()
