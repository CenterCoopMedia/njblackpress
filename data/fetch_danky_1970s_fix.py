"""Adjacent Danky leaves for 1970s entries off by one page."""

from pathlib import Path
import urllib.request

OUT = Path(__file__).resolve().parent / "research" / "danky"
PAGES = {
    95: "racers",
    98: "sociologist",
    102: "truth",
    105: "bwuf",
    207: "edperspectives",
    224: "fire2",
    270: "hart",
    329: "kuumba",
    374: "mbpsr",
    575: "ujamaa",
    576: "unionmsg",
    577: "unionmsg2",
}


def main() -> None:
    for page, slug in PAGES.items():
        n = page + 43
        url = f"https://archive.org/download/africanamericanne00dank/page/n{n}.jpg"
        dest = OUT / f"danky-1998-p{page}-{slug}.jpg"
        print("GET", page, n, slug, flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
        with urllib.request.urlopen(req, timeout=40) as resp:
            dest.write_bytes(resp.read())
        print("  wrote", dest.name, dest.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
