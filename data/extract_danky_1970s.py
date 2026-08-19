"""Extract Danky blocks for remaining 1970s civic and campus titles."""

from __future__ import annotations

import re
from pathlib import Path

TEXT = Path(__file__).resolve().parent / "research" / "danky-full.txt"
OUT = Path(__file__).resolve().parent / "research" / "danky-1970s-extract.txt"

NEEDLES = (
    "the  forum",
    "essex  forum",
    "union  messenger",
    "medic  news",
    "ujamaa",
    "hart  fund",
    "black  sociologist",
    "primer",
    "monthly  black  periodicals",
    "black  racers",
    "kuumba",
    "fire  ii",
    "black  women's  united",
    "black  women\u2019s  united",
    "educational  perspectives",
    "black  atlantic",
    "black  truth",
    "black  journal",
    "right  on",
    "bootstrap",
)


def guess_page(lines: list[str], i: int) -> str | None:
    for j in range(i, max(-1, i - 40), -1):
        s = lines[j].strip()
        if re.fullmatch(r"\d{1,3}", s):
            return s
    for j in range(i, min(len(lines), i + 20)):
        s = lines[j].strip()
        if re.fullmatch(r"\d{1,3}", s):
            return s
    return None


def main() -> None:
    lines = TEXT.read_text(encoding="utf-8", errors="replace").splitlines()
    chunks = []
    seen: set[int] = set()
    for i, line in enumerate(lines):
        l = line.lower()
        if not any(n in l for n in NEEDLES):
            continue
        if i in seen:
            continue
        seen.add(i)
        page = guess_page(lines, i)
        start = max(0, i - 3)
        end = min(len(lines), i + 14)
        chunks.append(f"-- line {i} page~{page} --\n" + "\n".join(lines[start:end]) + "\n")
    OUT.write_text("\n".join(chunks[:60]), encoding="utf-8")
    print("chunks", len(chunks), "wrote", OUT)
    for c in chunks[:40]:
        print(c.splitlines()[0])


if __name__ == "__main__":
    main()
