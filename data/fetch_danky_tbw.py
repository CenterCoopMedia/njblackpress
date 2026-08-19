from pathlib import Path
import urllib.request
OUT = Path(__file__).resolve().parent / "research" / "danky"
for page in (561, 562):
    n = page + 43
    dest = OUT / f"danky-1998-p{page}-tbw.jpg"
    url = f"https://archive.org/download/africanamericanne00dank/page/n{n}.jpg"
    print("GET", page, flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        dest.write_bytes(resp.read())
    print(" wrote", dest.name, dest.stat().st_size, flush=True)
