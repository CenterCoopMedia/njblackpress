"""Find Wayback and Internet Archive records for NJ Black press titles."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "research" / "wayback"
OUT.mkdir(parents=True, exist_ok=True)

SITES = [
    (4, "Black In Jersey", "https://www.blackinjersey.com/"),
    (6, "Front Runner New Jersey", "https://frontrunnernewjersey.com/"),
    (12, "Five Wards Media", "https://www.fivewardsmedia.com/"),
    (17, "Trenton Journal", "https://trentonjournal.com/"),
    (19, "NJ in Color", "https://njincolor.com/"),
    (20, "New Jersey Urban News", "https://njurbannews.com/"),
    (22, "Ark Republic", "https://www.arkrepublic.com/"),
    (23, "The Newark Times", "https://thenewarktimes.com/"),
    (25, "Atlantic City Focus", "https://www.atlanticcityfocus.com/"),
    (29, "Faithfully Magazine", "https://faithfullymagazine.com/"),
    (32, "Trenton365 Stream with Jacque Howard", "https://jacque-howard.com/trenton365-stream"),
    (36, "More Jersey", "https://morejersey.com/"),
    (43, "Public Square Amplified", "https://www.publicsq.org/"),
    (84, "Unity and Struggle", "https://www.marxists.org/history/erol/periodicals/unity-struggle/index.htm"),
    (128, "Newark Black Newspapers Collection", "https://collections.libraries.rutgers.edu/newark-black-newspapers"),
    (33, "The Black Observer", "https://scarletandblack.rutgers.edu/archive/items/show/949"),
    (71, "The Missionary Magazine", "https://www.wms-amec.org/missionary-magazine.html"),
    (95, "Right On!", "https://archive.org/details/right-on-v-06n-04-1977-02.-laufer-d-m"),
]

IA_QUERIES = [
    "New Jersey Afro-American newspaper",
    "Newark Herald African American newspaper",
    '"Black Newark" newspaper',
    '"Ironsides Echo" Bordentown',
    '"The Echo" "Red Bank" newspaper',
    "Unity and Struggle Newark",
    "New Jersey Herald News African American",
    "Nubian News Trenton",
]


def get_json(url: str, timeout: int = 40):
    req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def get_text(url: str, timeout: int = 40) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "njblackpress-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def cdx(url: str) -> dict:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc or parsed.path
    host = host.replace("www.", "")
    query = urllib.parse.urlencode(
        {
            "url": host + "/*",
            "output": "json",
            "filter": "statuscode:200",
            "fl": "timestamp,original,statuscode,mimetype,length",
            "collapse": "timestamp:6",
            "limit": 30,
        }
    )
    rows = get_json("https://web.archive.org/cdx/search/cdx?" + query)
    if not rows or len(rows) < 2:
        avail = get_json("https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe=""))
        closest = (avail.get("archived_snapshots") or {}).get("closest") or {}
        return {"host": host, "count": 0, "snapshots": [], "closest": closest}
    headers, *data = rows
    snaps = [dict(zip(headers, row)) for row in data]
    html = [s for s in snaps if "html" in (s.get("mimetype") or "")]
    images = [s for s in snaps if (s.get("mimetype") or "").startswith("image/")]
    first = snaps[0]
    last = snaps[-1]
    return {
        "host": host,
        "count": len(snaps),
        "first": first,
        "last": last,
        "html_sample": html[:8],
        "image_sample": images[:8],
        "wayback_first": f"https://web.archive.org/web/{first['timestamp']}/{first['original']}" if first else None,
        "wayback_last": f"https://web.archive.org/web/{last['timestamp']}/{last['original']}" if last else None,
    }


def ia_search(q: str) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "q": q,
            "fl[]": "identifier,title,year,description,downloads,item_size",
            "rows": 8,
            "output": "json",
        }
    )
    # advancedsearch wants repeated fl[] ; build manually
    url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode({"q": q, "rows": 8, "output": "json", "fl[]": "identifier"})
        + "&fl[]=title&fl[]=year&fl[]=description"
    )
    data = get_json(url)
    docs = ((data.get("response") or {}).get("docs")) or []
    out = []
    for d in docs:
        ident = d.get("identifier")
        out.append(
            {
                "identifier": ident,
                "title": d.get("title"),
                "year": d.get("year"),
                "description": (d.get("description") or "")[:400] if isinstance(d.get("description"), str) else d.get("description"),
                "url": f"https://archive.org/details/{ident}" if ident else None,
            }
        )
    return out


def main() -> None:
    findings = {"sites": [], "ia_search": []}
    for pid, name, url in SITES:
        print("CDX", name, url)
        try:
            rec = cdx(url)
            rec.update({"id": pid, "name": name, "url": url})
            findings["sites"].append(rec)
            print(" ", rec.get("count"), "snaps", rec.get("wayback_first"))
        except Exception as exc:
            findings["sites"].append({"id": pid, "name": name, "url": url, "error": str(exc)})
            print("  ERR", exc)
        time.sleep(1.4)

    for q in IA_QUERIES:
        print("IA", q)
        try:
            docs = ia_search(q)
            findings["ia_search"].append({"query": q, "hits": docs})
            print(" ", len(docs), "hits")
            for d in docs[:3]:
                print("   ", d.get("year"), d.get("title"))
        except Exception as exc:
            findings["ia_search"].append({"query": q, "error": str(exc)})
            print("  ERR", exc)
        time.sleep(1.4)

    path = OUT / "wayback-index.json"
    path.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
