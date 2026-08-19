"""Extract Danky blocks for 1960s civic titles and guess printed pages."""

from __future__ import annotations

import re
from pathlib import Path

TEXT = Path(__file__).resolve().parent / "research" / "danky-full.txt"
OUT = Path(__file__).resolve().parent / "research" / "danky-1960s-extract.txt"

# Exact-ish line starts / unique phrases (OCR has extra spaces)
NEEDLES = (
    "243  afro-american  festival",
    "1867  the  cricket",
    "1978  deliverance  voice",
    "2512  freedom  reports",
    "4335  ncup",
    "6142  utimme",
    "6211  the  voice",
    "6279  wait.",
    "black  newark",
    "newark community union",
    "newark  community  union",
    "george  s.  adams",
    "committee for unified",
    "committee  for  unified",
)


def guess_page(lines: list[str], i: int) -> str | None:
    for j in range(i, max(-1, i - 40), -1):
        s = lines[j].strip()
        if re.fullmatch(r"\d{1,3}", s):
            return s
    return None


def main() -> None:
    lines = TEXT.read_text(encoding="utf-8", errors="replace").splitlines()
    chunks = []
    seen = set()
    for i, line in enumerate(lines):
        l = line.lower()
        if not any(n in l for n in NEEDLES):
            continue
        if i in seen:
            continue
        seen.add(i)
        page = guess_page(lines, i)
        start = max(0, i - 4)
        end = min(len(lines), i + 16)
        header = f"-- line {i} page~{page} --\n"
        chunks.append(header + "\n".join(lines[start:end]) + "\n")
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print("chunks", len(chunks), "wrote", OUT)
    for c in chunks:
        first = c.splitlines()[0]
        print(first)


if __name__ == "__main__":
    main()
