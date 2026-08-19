"""Open leftover 1930s NJ cards and a few tighter searches."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

PAGES = [
    ("jersey-express-1933-herald", "https://www.newspapers.com/image/525928236/", "Express"),
    ("johnson-1934-apr", "https://www.newspapers.com/image/515682726/", "Johnson"),
    ("johnson-1949-app", "https://www.newspapers.com/image/143065742/", "Johnson"),
    ("johnson-1949-ledger", "https://www.newspapers.com/image/1108232407/", "Johnson"),
]

SEARCHES = [
    (2, "the-jersey-express", '"The Jersey Express"', 1932, 1940, "Jersey Express"),
    (45, "apex-exact", '"Apex News" "Atlantic City"', 1929, 1941, "Apex"),
    (57, "ironsides-exact", '"Ironsides Echo"', 1917, 1956, "Ironsides"),
    (34, "smith-newspaper", '"A. P. Smith" (newspaper OR editor OR Landscape) Saddle', 1880, 1910, "Smith"),
    (37, "guardian-voice", '"Voice of the Colored People" Guardian', 1934, 1943, "Guardian"),
]

EXTRACT = """() => {
    const results = [];
    for (const a of document.querySelectorAll('a[href*="/image/"]')) {
        const href = a.href;
        const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
        if (!href || text.length < 12) continue;
        if (results.some(r => r.href === href)) continue;
        results.push({text: text.slice(0, 400), href});
        if (results.length >= 12) break;
    }
    const body = (document.body.innerText || '').replace(/\\s+/g, ' ');
    const count = (body.match(/([\\d,]+)\\s+matches/i) || [null, null])[1];
    return {url: location.href, title: document.title, count, results};
}"""

NJ = (
    "new jersey", "trenton", "newark", "montclair", "atlantic city",
    "paterson", "asbury park", "passaic", "camden", "bordentown",
    "saddle", "ridgewood", "freehold", "long branch",
)


def is_nj(text: str) -> bool:
    t = (text or "").lower()
    return any(m in t for m in NJ)


def main() -> None:
    opened = []
    for slug, url, term in PAGES:
        print("OPEN", slug, flush=True)
        send({"action": "goto", "url": url, "wait_ms": 3500}, timeout=120)
        send({
            "action": "fill",
            "selector": 'input[placeholder="Find text on this page"]',
            "text": term,
            "press": "Enter",
            "wait_ms": 2200,
        }, timeout=60)
        shot = f"q7more-{slug}.png"
        send({"action": "screenshot", "name": shot}, timeout=60)
        opened.append({"slug": slug, "url": url, "shot": shot})
        time.sleep(0.6)

    searches = []
    for pid, slug, keyword, y0, y1, find_term in SEARCHES:
        url = (
            "https://www.newspapers.com/search/results/?"
            f"keyword={quote_plus(keyword)}&date-year={y0}&date-year-end={y1}"
        )
        print("SEARCH", slug, flush=True)
        goto = send({"action": "goto", "url": url, "wait_ms": 4500}, timeout=120)
        if not goto.get("ok"):
            print("  fail", goto.get("error"), flush=True)
            continue
        send({"action": "screenshot", "name": f"q7b-{slug}.png"}, timeout=60)
        extracted = send({"action": "eval", "js": EXTRACT}, timeout=60)
        data = extracted.get("value") or {}
        cards = [c for c in (data.get("results") or []) if is_nj(c.get("text") or "")]
        rec = {"id": pid, "slug": slug, "count": data.get("count"), "nj": cards}
        searches.append(rec)
        print(f"  count={data.get('count')} nj={len(cards)}", flush=True)
        for card in cards[:2]:
            print("  OPEN", card["text"][:110], flush=True)
            send({"action": "goto", "url": card["href"], "wait_ms": 3500}, timeout=120)
            send({
                "action": "fill",
                "selector": 'input[placeholder="Find text on this page"]',
                "text": find_term,
                "press": "Enter",
                "wait_ms": 2200,
            }, timeout=60)
            shot = f"q7bopen-{slug}.png"
            send({"action": "screenshot", "name": shot}, timeout=60)
            opened.append({"slug": slug, "url": card["href"], "shot": shot, "card": card["text"]})
            time.sleep(0.5)

    (OUT / "q7-more.json").write_text(json.dumps({"searches": searches, "opened": opened}, indent=2), encoding="utf-8")
    print("done; chrome left open", flush=True)


if __name__ == "__main__":
    main()
