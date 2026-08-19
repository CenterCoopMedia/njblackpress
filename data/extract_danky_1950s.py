"""Extract Danky blocks for 1950s civic titles and guess printed pages."""

from __future__ import annotations

from pathlib import Path

TEXT = Path(__file__).resolve().parent / "research" / "danky-full.txt"
OUT = Path(__file__).resolve().parent / "research" / "danky-1950s-extract.txt"

NEEDLES = (
    "jersey  camera",
    "hours  after",
    "nite  lite",
    "club  world",
    "north  jersey  independent",
    "northern  new  jersey",
    "tiny  prince",
    "bronze  thrills",
)


def main() -> None:
    lines = TEXT.read_text(encoding="utf-8", errors="replace").splitlines()
    chunks = []
    for i, line in enumerate(lines):
        l = line.lower()
        if any(n in l for n in NEEDLES):
            start = max(0, i - 4)
            end = min(len(lines), i + 12)
            chunks.append(f"-- line {i} --\n" + "\n".join(lines[start:end]) + "\n")
    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print("chunks", len(chunks), "wrote", OUT)


if __name__ == "__main__":
    main()
