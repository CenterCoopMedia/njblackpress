"""Tighter NJ searches for remaining pre-1950 searched_none titles."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

NJ = (
    "new jersey", "trenton", "newark", "princeton, new jersey",
    "camden, new jersey", "atlantic city", "bordentown", "montclair",
    "paterson", "asbury park", "freehold", "long branch", "plainfield",
    "east orange", "ridgewood", "hackensack", "woodbury", "bridgewater",
    "passaic", "vauxhall", "union, new jersey", "chatsworth", "glassboro",
    "cape may", "fort dix", "new lisbon", "berlin, new jersey",
    "glen ridge",
)

# Unique slugs. Open at most 2 NJ cards each. Shot names include year.
SEARCHES = [
    (7, "citizen-auston-only", '"Henry J. Auston"', 1905, 1920, "Auston"),
    (7, "citizen-colored-wkly", '"The Citizen" (colored OR Negro) Princeton', 1908, 1916, "Citizen"),
    (45, "apex-news-quoted", '"Apex News"', 1929, 1941, "Apex News"),
    (45, "apex-publishing", '"Apex Publishing"', 1928, 1942, "Apex"),
    (101, "webber-afterhours", '"Harry B. Webber" (After Hours OR magazine OR editor)', 1945, 1960, "Webber"),
    (79, "hiram-starnews", '"Star-News" Vauxhall', 1945, 1965, "Star"),
    (136, "penn-crusader", '"Penn Crusader"', 1935, 1941, "Crusader"),
    (102, "berlin-broadcast", '"Camp Berlin" (Broadcast OR newspaper OR CCC)', 1933, 1936, "Berlin"),
    (90, "little-ease", '"Little Ease Echo"', 1937, 1940, "Ease"),
    (94, "dias-creek", '"Dias Creek Echo"', 1937, 1940, "Dias"),
    (48, "ash-can-ccc", '"Ash Can" (CCC OR Chatsworth OR camp)', 1934, 1937, "Ash Can"),
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


def is_nj(text: str) -> bool:
    t = (text or "").lower()
    if "illinois" in t or "indiana" in t or "kentucky" in t:
        return False
    return any(m in t for m in NJ)


def year_of(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text or "")]
    return min(years) if years else 9999


def main() -> None:
    login = send({"action": "login_check"}, timeout=90)
    print("login", login.get("logged_in"), flush=True)
    if login.get("logged_in") is False:
        print("NOT LOGGED IN; stop", flush=True)
        return

    report = {"searches": [], "opened": []}
    for pid, slug, keyword, y0, y1, find_term in SEARCHES:
        url = (
            "https://www.newspapers.com/search/results/?"
            f"keyword={quote_plus(keyword)}&date-year={y0}&date-year-end={y1}"
        )
        print("SEARCH", pid, slug, flush=True)
        goto = send({"action": "goto", "url": url, "wait_ms": 4500}, timeout=120)
        if not goto.get("ok"):
            print("  fail", goto.get("error"), flush=True)
            report["searches"].append({"id": pid, "slug": slug, "error": goto.get("error")})
            continue
        send({"action": "screenshot", "name": f"q7e-{slug}.png"}, timeout=60)
        extracted = send({"action": "eval", "js": EXTRACT}, timeout=60)
        data = extracted.get("value") or {}
        cards = data.get("results") or []
        nj = [c for c in cards if is_nj(c.get("text") or "")]
        nj.sort(key=lambda c: year_of(c.get("text") or ""))
        rec = {"id": pid, "slug": slug, "count": data.get("count"), "nj": nj, "keyword": keyword}
        report["searches"].append(rec)
        print(f"  count={data.get('count')} cards={len(cards)} nj={len(nj)}", flush=True)
        for card in nj[:2]:
            y = year_of(card.get("text") or "")
            print("  OPEN", card["text"][:110], flush=True)
            send({"action": "goto", "url": card["href"], "wait_ms": 3500}, timeout=120)
            send({
                "action": "fill",
                "selector": 'input[placeholder="Find text on this page"]',
                "text": find_term,
                "press": "Enter",
                "wait_ms": 2200,
            }, timeout=60)
            shot = f"q7eopen-{slug}-{y}.png"
            send({"action": "screenshot", "name": shot}, timeout=60)
            report["opened"].append({
                "id": pid,
                "slug": slug,
                "card": card["text"],
                "url": card["href"],
                "shot": shot,
            })
            time.sleep(0.4)

    (OUT / "q7e-pre1950.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote", OUT / "q7e-pre1950.json", flush=True)
    print("done; chrome left open", flush=True)


if __name__ == "__main__":
    main()
