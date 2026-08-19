"""Download Danky leaves for remaining 1990s titles. n = printed_page + 43."""

from pathlib import Path
import urllib.request

OUT = Path(__file__).resolve().parent / "research" / "danky"
OUT.mkdir(parents=True, exist_ok=True)

PAGES = {
    1: "hype",
    2: "hype2",
    18: "afrworld",
    19: "afrworld2",
    50: "artz",
    51: "artz2",
    52: "crossroads",
    75: "bbc",
    85: "hairdigest",
    134: "captain",
    235: "fotorama",
    236: "franklin",
    267: "harambee",
    287: "hypehair",
    300: "icp",
    317: "jaam",
    323: "jfbm",
    356: "mcsq",
    404: "network",
    405: "network2",
    409: "deadline",
    484: "rapmasters",
    535: "spirit",
    560: "tbw",
    570: "tryhair",
    620: "wordup",
    625: "yes",
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
