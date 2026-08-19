"""Search oldest ceased titles on Newspapers.com. Keep only New Jersey cards."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

NJ_MARKERS = (
    "new jersey", "trenton", "newark", "jersey city", "asbury park",
    "red bank", "long branch", "paterson", "camden, new jersey",
    "atlantic city", "montclair", "plainfield", "freehold", "morristown",
    "passaic", "elizabeth, new jersey", "new brunswick", "princeton, new jersey",
    "teaneck", "east orange", "hackensack", "hoboken", "orange, new jersey",
    "bayonne", "irvington", "vineland", "bridgeton", "somerville",
    "bound brook", "perth amboy", "ridgewood", "saddle river", "bergen",
    "bordentown", "cape may", "glassboro", "fort dix", "dover, new jersey",
    "paramus", "park ridge",
)

# (pub_id, slug, keyword, year_start, year_end, find_term)
SEARCHES = [
    (34, "landscape-smith", '"A. P. Smith" OR "A.P. Smith" "Saddle River"', 1880, 1910, "Smith"),
    (34, "landscape-title", '"The Landscape" "Saddle River"', 1880, 1910, "Landscape"),
    (7, "citizen-dupaur", '"Du Paur" OR DuPaur OR "DuPaur"', 1905, 1925, "Paur"),
    (7, "citizen-auston", '"Henry J. Auston" OR "Henry Auston" Princeton', 1905, 1925, "Auston"),
    (3, "camden-green", '"Camden News" (colored OR negro OR "C. N. Green")', 1914, 1922, "Camden News"),
    (57, "ironsides", '"Ironsides Echo" OR "Ironsides" Bordentown', 1916, 1956, "Ironsides"),
    (45, "apex", '"Apex News" (Atlantic OR Morgan OR colored)', 1928, 1942, "Apex News"),
    (2, "jersey-express", '"Jersey Express" Montclair', 1930, 1940, "Express"),
    (2, "jersey-express-johnson", '"Melvin B. Johnson" (editor OR newspaper) Montclair', 1930, 1945, "Johnson"),
    (37, "guardian", '"New Jersey Guardian" (colored OR Negro OR Newark)', 1934, 1943, "Guardian"),
]

EXTRACT = """() => {
    const results = [];
    for (const a of document.querySelectorAll('a[href*="/image/"]')) {
        const href = a.href;
        const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
        if (!href || text.length < 12) continue;
        if (results.some(r => r.href === href)) continue;
        results.push({text: text.slice(0, 400), href});
        if (results.length >= 16) break;
    }
    const body = (document.body.innerText || '').replace(/\\s+/g, ' ');
    const count = (body.match(/([\\d,]+)\\s+matches/i) || [null, null])[1];
    return {url: location.href, title: document.title, count, results};
}"""


def is_nj(text: str) -> bool:
    t = (text or "").lower()
    if "illinois" in t or "indiana" in t or "kentucky" in t:
        return False
    return any(m in t for m in NJ_MARKERS)


def year_of(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text or "")]
    return min(years) if years else 9999


def main() -> None:
    login = send({"action": "login_check"}, timeout=90)
    print("login", login.get("logged_in"), login.get("url"), flush=True)
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
        send({"action": "screenshot", "name": f"q7-{slug}.png"}, timeout=60)
        extracted = send({"action": "eval", "js": EXTRACT}, timeout=60)
        data = extracted.get("value") or {}
        cards = data.get("results") or []
        nj = sorted([c for c in cards if is_nj(c.get("text") or "")], key=lambda c: year_of(c.get("text") or ""))
        rec = {
            "id": pid,
            "slug": slug,
            "keyword": keyword,
            "count": data.get("count"),
            "cards": len(cards),
            "nj_cards": nj,
            "url": data.get("url") or url,
        }
        report["searches"].append(rec)
        print(f"  count={data.get('count')} cards={len(cards)} nj={len(nj)}", flush=True)
        for card in nj[:2]:
            print("  OPEN", card["text"][:120], flush=True)
            send({"action": "goto", "url": card["href"], "wait_ms": 3500}, timeout=120)
            send({
                "action": "fill",
                "selector": 'input[placeholder="Find text on this page"]',
                "text": find_term,
                "press": "Enter",
                "wait_ms": 2200,
            }, timeout=60)
            shot = f"q7open-{slug}-{year_of(card['text'])}.png"
            send({"action": "screenshot", "name": shot}, timeout=60)
            report["opened"].append({
                "id": pid,
                "slug": slug,
                "card": card["text"],
                "url": card["href"],
                "shot": shot,
                "find": find_term,
            })
            time.sleep(0.8)

    (OUT / "q7-oldest-ceased.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote", OUT / "q7-oldest-ceased.json", flush=True)
    print("done; chrome left open", flush=True)


if __name__ == "__main__":
    main()
