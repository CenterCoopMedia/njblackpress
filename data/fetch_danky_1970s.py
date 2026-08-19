"""Download Danky leaves for remaining 1970s titles. n = printed_page + 43."""

from pathlib import Path
import urllib.request

OUT = Path(__file__).resolve().parent / "research" / "danky"
OUT.mkdir(parents=True, exist_ok=True)

# printed page -> slug
PAGES = {
    74: "atlantic",
    87: "journal",
    94: "racers",
    97: "sociologist",
    103: "truth",
    104: "bwuf",
    206: "edperspectives",
    223: "fire2",
    269: "hart",
    330: "kuumba",
    357: "medic",
    373: "mbpsr",
    472: "primer",
    493: "righton",
    494: "righton2",
    574: "ujamaa",
    585: "unionmsg",
    586: "unionmsg2",
}


def main() -> None:
    for page, slug in PAGES.items():
        n = page + 43
        url = f"https://archive.org/download/africanamericanne00dank/page/n{n}.jpg"
        dest = OUT / f"danky-1998-p{page}-{slug}.jpg"
        print("GET", page, n, slug, flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read()
        dest.write_bytes(data)
        print("  wrote", dest.name, len(data), flush=True)


if __name__ == "__main__":
    main()
