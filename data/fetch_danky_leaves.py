"""Download full Danky printed-page JPEGs (leaf = printed page + 43)."""

from __future__ import annotations

from pathlib import Path
import urllib.request

OUT = Path(__file__).resolve().parent / "research" / "danky"
OUT.mkdir(parents=True, exist_ok=True)

# printed page -> why
PAGES = {
    24: "festival-243-below-fold",
    91: "blacknewark-934-below-fold",
    179: "cricket-1867",
    190: "deliverance-guess",
    191: "deliverance-guess2",
    417: "ncup-see-ref",
    418: "ncup-entry",
    587: "utimme-guess",
    594: "voice-guess",
}

# BookReaderImages pattern used by IA viewer
TPL = (
    "https://archive.org/download/africanamericanne00dank/"
    "page/n{leaf}.jpg"
)


def main() -> None:
    for page, slug in PAGES.items():
        leaf = page + 43  # 1-based leaf shown in viewer
        # IA n-parameter is 0-based in some URLs; try printed-page leaf-1
        for n in (leaf - 1, leaf, page):
            url = TPL.format(leaf=n)
            dest = OUT / f"danky-leaf-p{page}-n{n}-{slug}.jpg"
            print("GET", url, flush=True)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
                with urllib.request.urlopen(req, timeout=40) as resp:
                    data = resp.read()
                dest.write_bytes(data)
                print("  wrote", dest.name, len(data), resp.status, flush=True)
                if len(data) > 20000:
                    break
            except Exception as exc:
                print("  fail", exc, flush=True)


if __name__ == "__main__":
    main()
