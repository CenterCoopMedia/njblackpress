"""One more NJ-only Newspapers.com pass for the four leftover civic titles."""

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
    "camden, new jersey", "atlantic city", "paterson", "asbury park",
    "freehold", "plainfield", "east orange", "union, new jersey",
    "vauxhall", "elizabeth, new jersey", "new brunswick",
)

SEARCHES = [
    (7, "citizen-dupaur-trenton", '"Du Paur" OR "DuPaur" (Trenton OR Princeton) newspaper', 1905, 1920, "Paur"),
    (7, "citizen-nj-colored", '"The Citizen" "New Jersey" (colored OR Negro) editor', 1908, 1915, "Citizen"),
    (3, "camden-pubco", '"Camden News Publishing"', 1914, 1920, "Camden News"),
    (3, "camden-green-colored", '"C. N. Green" (colored OR Negro OR editor)', 1914, 1922, "Green"),
    (45, "apex-1934-press", '"Apex News"', 1934, 1935, "Apex News"),
    (45, "apex-morgan-only", '"Archie J. Morgan"', 1928, 1942, "Morgan"),
    (79, "hiram-union", '"Hiram" (newspaper OR "Star-News") (Vauxhall OR Union)', 1946, 1955, "Hiram"),
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
    if "illinois" in t or "indiana" in t:
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
            continue
        send({"action": "screenshot", "name": f"q7i-{slug}.png"}, timeout=60)
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
            shot = f"q7iopen-{slug}-{y}.png"
            send({"action": "screenshot", "name": shot}, timeout=60)
            report["opened"].append({
                "id": pid, "slug": slug, "card": card["text"],
                "url": card["href"], "shot": shot,
            })
            time.sleep(0.4)
    (OUT / "q7i-four.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("done; chrome left open", flush=True)


if __name__ == "__main__":
    main()
