"""Guess printed Danky pages by nearby standalone numbers."""

from pathlib import Path
import re

TEXT = Path(__file__).resolve().parent / "research" / "danky-full.txt"
lines = TEXT.read_text(encoding="utf-8", errors="replace").splitlines()

TARGETS = {
    62: "243  Afro-American  Festival",
    28: "934  Black  New  Ark",
    69: "1867  The  Cricket",
    70: "1978  Deliverance  Voice",
    133: "2512  Freedom  Reports",
    76: "4335  Newark  Community  Union  Project  News",
    73: "6142  Utimme",
    41: "6211  The  Voice.  1968",
    113: "6279  Wait.",
}


def nearby_pages(i: int) -> list[tuple[int, int, str]]:
    found = []
    for j in range(max(0, i - 25), min(len(lines), i + 20)):
        s = lines[j].strip()
        if re.fullmatch(r"\d{1,3}", s):
            n = int(s)
            if 1 <= n <= 750:
                found.append((j - i, n, s))
    return found


for pid, needle in TARGETS.items():
    hit = None
    for i, line in enumerate(lines):
        if needle.lower() in line.lower() or needle in line:
            hit = i
            break
    print("=" * 60)
    print("id", pid, "needle", needle, "line", hit)
    if hit is None:
        continue
    print("context page nums (offset, value):", nearby_pages(hit))
    print(lines[hit][:120])
