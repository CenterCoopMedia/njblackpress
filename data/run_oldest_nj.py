"""Oldest New Jersey newspaper hits only. Filter cards in Python, not the broken sidebar."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

NJ_CITIES = (
    "new jersey", "trenton", "newark", "jersey city", "asbury park",
    "red bank", "long branch", "paterson", "camden", "atlantic city",
    "montclair", "plainfield", "freehold", "morristown", "passaic",
    "elizabeth", "new brunswick", "princeton", "teaneck", "east orange",
    "hackensack", "hoboken", "orange, new jersey", "bayonne", "irvington",
    "vineland", "bridgeton", "somerville", "bound brook", "perth amboy",
)

# Tight queries. Date-bounded where the paper is old.
SEARCHES = [
    ("herbert", '"R. Henri Herbert"', 1880, 1915),
    ("trumpet", '"New Jersey Trumpet"', 1887, 1900),
    ("murrell", '"Colonel Murrell" (Trumpet OR editor OR newspaper)', 1887, 1900),
    ("echo-rock", '"W. E. Rock" OR "William E. Rock" OR "William Rock" Echo', 1904, 1943),
    ("echo-title", '"Red Bank Echo" OR "Echo of Red Bank"', 1904, 1943),
    ("herald", '"Newark Herald" (colored OR Negro OR "Editor Clark")', 1928, 1940),
    ("guardian", '"New Jersey Guardian"', 1934, 1943),
    ("colored-trenton", '"colored newspaper" Trenton', 1880, 1910),
    ("colored-newark", '"colored newspaper" Newark', 1880, 1940),
]


def nj_card(text: str) -> bool:
    t = (text or "").lower()
    return any(c in t for c in NJ_CITIES)


def year_of(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(18[7-9]\d|19[0-6]\d)\b", text or "")]
    return min(years) if years else 9999


EXTRACT = """() => {
    const results = [];
    for (const a of document.querySelectorAll('a[href*="/image/"]')) {
        const href = a.href;
        const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
        if (!href || text.length < 12) continue;
        if (results.some(r => r.href === href)) continue;
        results.push({text: text.slice(0, 400), href});
        if (results.length >= 20) break;
    }
    const body = (document.body.innerText || '').replace(/\\s+/g, ' ');
    const count = (body.match(/([\\d,]+)\\s+matches/i) || [null, null])[1];
    return {url: location.href, title: document.title, count, results};
}"""


def main() -> None:
    findings = {"searches": [], "opened": []}
    for slug, keyword, y0, y1 in SEARCHES:
        url = (
            "https://www.newspapers.com/search/results/?"
            f"keyword={quote_plus(keyword)}&date-year={y0}&date-year-end={y1}"
        )
        print("SEARCH", slug, y0, y1)
        r = send({"action": "goto", "url": url, "wait_ms": 5000}, timeout=120)
        if not r.get("ok"):
            print("  goto failed", r)
            findings["searches"].append({"slug": slug, "error": r})
            continue
        send({"action": "screenshot", "name": f"oldnj-{slug}.png"}, timeout=60)
        extracted = send({"action": "eval", "js": EXTRACT}, timeout=60)
        data = extracted.get("value") or {}
        cards = data.get("results") or []
        nj = [c for c in cards if nj_card(c.get("text", ""))]
        nj.sort(key=lambda c: year_of(c.get("text", "")))
        rec = {
            "slug": slug,
            "keyword": keyword,
            "url": data.get("url") or r.get("url"),
            "count": data.get("count"),
            "cards": cards,
            "nj_sorted": nj,
        }
        findings["searches"].append(rec)
        print(f"  {rec.get('count')} matches; {len(nj)} NJ cards")
        for hit in nj[:2]:
            print("  OPEN", year_of(hit["text"]), hit["text"][:90])
            opened = send({"action": "goto", "url": hit["href"], "wait_ms": 4000}, timeout=120)
            term = "Herbert" if "herbert" in slug else (
                "Trumpet" if slug in ("trumpet", "murrell") else (
                    "Echo" if "echo" in slug else (
                        "Herald" if "herald" in slug else (
                            "Guardian" if "guardian" in slug else "colored"
                        )
                    )
                )
            )
            send({
                "action": "fill",
                "selector": 'input[placeholder="Find text on this page"]',
                "text": term,
                "press": "Enter",
                "wait_ms": 2500,
            }, timeout=60)
            shot = f"oldnjclip-{slug}-{len(findings['opened']):02d}.png"
            shot_res = send({"action": "screenshot", "name": shot}, timeout=60)
            findings["opened"].append({
                "slug": slug,
                "from": hit,
                "year": year_of(hit["text"]),
                "url": opened.get("url"),
                "title": opened.get("title"),
                "screenshot": shot,
                "shot_ok": shot_res.get("ok"),
            })
            time.sleep(2)
        time.sleep(2)

    path = OUT / "oldest-nj.json"
    path.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
