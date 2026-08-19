"""Real IA / CA / LOC / library queries for Citizen, Camden News, Apex News, Hiram Star-News."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "research" / "four-source-query.json"
UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}

QUERIES = {
    7: [
        'The Citizen Princeton Negro newspaper',
        '"The Citizen" Princeton "New Jersey" (Negro OR colored)',
        '"Henry J. Auston" Princeton',
        '"Du Paur" newspaper Princeton',
    ],
    3: [
        '"Camden News" (Negro OR colored) 1915',
        '"C. N. Green" Camden newspaper',
        'Camden News Publishing Co',
    ],
    45: [
        '"Apex News" Atlantic City',
        '"Apex Publishing" newspaper',
        '"Archie J. Morgan" Apex',
    ],
    79: [
        '"Hiram Star-News"',
        '"Hiram Star" Vauxhall',
        '"Star-News" Vauxhall New Jersey',
    ],
}


def http_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def http_text(url: str, timeout: int = 30) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, (exc.read().decode("utf-8", errors="replace") if exc.fp else "")
    except Exception as exc:
        return 0, str(exc)


def ia_search(q: str) -> list[dict]:
    url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode({"q": f"({q}) AND mediatype:texts", "rows": 5, "output": "json"})
        + "&fl[]=identifier&fl[]=title&fl[]=date&fl[]=year"
    )
    data = http_json(url)
    return ((data.get("response") or {}).get("docs")) or []


def ca_titles(q: str) -> dict:
    url = (
        "https://chroniclingamerica.loc.gov/search/titles/results/?"
        + urllib.parse.urlencode({"terms": q, "format": "json", "page": 1})
    )
    try:
        return http_json(url)
    except Exception as exc:
        return {"error": str(exc)}


def main() -> None:
    report = {"titles": {}}
    libs = {
        "npl": "https://archive.org/details/newarkafamnewspapers",
        "rutgers": "https://collections.libraries.rutgers.edu/newark-black-newspapers",
        "njsl": "https://www.njstatelib.org/ironsides_echo/",
        "redbank": "http://www.digifind-it.com/redbank/echo.php",
        "danky": "https://archive.org/details/africanamericanne00dank",
    }
    print("library pages", flush=True)
    lib_hits = {}
    for key, url in libs.items():
        status, text = http_text(url)
        low = text.lower()
        lib_hits[key] = {
            "status": status,
            "url": url,
            "has_citizen": "the citizen" in low and "princeton" in low,
            "has_camden_news": "camden news" in low,
            "has_apex": "apex news" in low,
            "has_hiram": "hiram" in low and "star" in low,
        }
        print(" ", key, status, lib_hits[key], flush=True)
    report["libraries"] = lib_hits

    for pid, qs in QUERIES.items():
        rec = {"ia": [], "ca": []}
        for q in qs:
            print("IA", pid, q, flush=True)
            try:
                docs = ia_search(q)
            except Exception as exc:
                rec["ia"].append({"q": q, "error": str(exc)})
                continue
            rec["ia"].append(
                {
                    "q": q,
                    "n": len(docs),
                    "docs": [
                        {
                            "id": d.get("identifier"),
                            "title": d.get("title"),
                            "url": f"https://archive.org/details/{d.get('identifier')}",
                        }
                        for d in docs
                    ],
                }
            )
            print("  docs", len(docs), flush=True)
        print("CA titles", pid, qs[0], flush=True)
        rec["ca"] = ca_titles(qs[0])
        items = (rec["ca"] or {}).get("items") or []
        print("  ca items", len(items), flush=True)
        report["titles"][str(pid)] = rec

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
