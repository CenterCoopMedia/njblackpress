"""Find Apex News and Camden News entries in Danky."""

from __future__ import annotations

import urllib.request
from pathlib import Path

URL = "https://archive.org/stream/africanamericanne00dank/africanamericanne00dank_djvu.txt"
OUT = Path(__file__).resolve().parent / "research" / "danky-hits2.txt"
UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}


def main() -> None:
    req = urllib.request.Request(URL, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        l = line.lower()
        if "apex" in l or ("camden" in l and "news" in l) or "archie" in l and "morgan" in l:
            start = max(0, i - 2)
            end = min(len(lines), i + 6)
            hits.append(f"-- line {i} --\n" + "\n".join(lines[start:end]) + "\n")
    OUT.write_text("\n".join(hits[:40]), encoding="utf-8")
    print("blocks", len(hits), "wrote first", min(40, len(hits)))


if __name__ == "__main__":
    main()
