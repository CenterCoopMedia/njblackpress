"""Adjacent Danky leaves for 1990s entries off by one page."""

from pathlib import Path
import urllib.request

OUT = Path(__file__).resolve().parent / "research" / "danky"
PAGES = {
    298: "icp",
    316: "jaam",
}


def main() -> None:
    for page, slug in PAGES.items():
        n = page + 43
        dest = OUT / f"danky-1998-p{page}-{slug}.jpg"
        url = f"https://archive.org/download/africanamericanne00dank/page/n{n}.jpg"
        print("GET", page, slug, flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
        with urllib.request.urlopen(req, timeout=40) as resp:
            dest.write_bytes(resp.read())
        print("  wrote", dest.name, dest.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
