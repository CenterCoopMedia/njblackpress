"""Download the correct Danky leaves. n = printed_page + 43."""

from pathlib import Path
import urllib.request

OUT = Path(__file__).resolve().parent / "research" / "danky"

PAGES = {
    24: "festival",
    91: "blacknewark",
    179: "cricket",
    240: "freedom",
    587: "utimme",
    594: "voice",
    595: "voice2",
    601: "wait",
}


def main() -> None:
    for page, slug in PAGES.items():
        n = page + 43
        url = f"https://archive.org/download/africanamericanne00dank/page/n{n}.jpg"
        dest = OUT / f"danky-1998-p{page}-{slug}.jpg"
        print("GET", page, n, flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read()
        dest.write_bytes(data)
        print("  wrote", dest.name, len(data), flush=True)


if __name__ == "__main__":
    main()
