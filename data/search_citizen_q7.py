"""q7: The Citizen (Princeton 1909). Search de Paur spelling and colored-newspaper phrasing."""

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
    "princeton, nj", "teaneck", "east orange", "hackensack", "hoboken",
    "orange, new jersey", "bayonne", "irvington", "vineland", "bridgeton",
    "somerville", "bound brook", "perth amboy", "ridgewood", "saddle river",
    "bergen", "bordentown", "cape may", "glassboro", "fort dix",
    "dover, new jersey", "paramus", "park ridge", "witherspoon",
)

# Daily Princetonian cards say Princeton, New Jersey
NJ_MARKERS_LOOSE = NJ_MARKERS + ("princeton",)

SEARCHES = [
    (7, "citizen-depaur", '"de Paur" OR "De Paur" Princeton', 1905, 1925, "de Paur"),
    (7, "citizen-depaur-cafe", '"De Paur" (cafe OR restaurant OR caterer)', 1905, 1920, "Paur"),
    (7, "citizen-colored-paper", 'Princeton "colored newspaper"', 1905, 1925, "colored newspaper"),
    (7, "citizen-title-race", '"The Citizen" Princeton (colored OR negro OR "Negro race")', 1908, 1920, "Citizen"),
    (7, "citizen-witherspoon", '"9 Witherspoon"', 1908, 1915, "Witherspoon"),
    (7, "citizen-mission", '"industrial improvement of the Negro"', 1905, 1925, "Negro"),
    (7, "citizen-auston-editor", '"Henry J. Auston" OR "Henry Auston" (editor OR newspaper OR Citizen)', 1905, 1930, "Auston"),
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
    return any(m in t for m in NJ_MARKERS_LOOSE)


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
        print("SEARCH", pid, slug, keyword, flush=True)
        goto = send({"action": "goto", "url": url, "wait_ms": 4500}, timeout=120)
        if not goto.get("ok"):
            print("  fail", goto.get("error"), flush=True)
            report["searches"].append({"id": pid, "slug": slug, "error": goto.get("error")})
            continue
        send({"action": "screenshot", "name": f"q7c-{slug}.png"}, timeout=60)
        extracted = send({"action": "eval", "js": EXTRACT}, timeout=60)
        data = extracted.get("value") or {}
        cards = data.get("results") or []
        nj = sorted(
            [c for c in cards if is_nj(c.get("text") or "")],
            key=lambda c: year_of(c.get("text") or ""),
        )
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
            send(
                {
                    "action": "fill",
                    "selector": 'input[placeholder="Find text on this page"]',
                    "text": find_term,
                    "press": "Enter",
                    "wait_ms": 2200,
                },
                timeout=60,
            )
            shot = f"q7copen-{slug}-{year_of(card['text'])}.png"
            send({"action": "screenshot", "name": shot}, timeout=60)
            report["opened"].append(
                {
                    "id": pid,
                    "slug": slug,
                    "card": card["text"],
                    "url": card["href"],
                    "shot": shot,
                    "find": find_term,
                }
            )
            time.sleep(0.8)

    (OUT / "q7-citizen.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote", OUT / "q7-citizen.json", flush=True)
    print("done; chrome left open", flush=True)


if __name__ == "__main__":
    main()
