"""Newspapers.com NJ searches for remaining 1970s civic titles."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"
NJ = (
    "new jersey", "trenton", "newark", "plainfield", "east orange",
    "paterson", "montclair", "asbury park", "camden, new jersey",
    "wayne", "jersey city", "cherry hill", "atlantic city",
)

SEARCHES = [
    (39, "forum-newark", '"The Forum" (Newark) (Negro OR Black OR newspaper)', 1970, 1978, "Forum"),
    (42, "essex-forum", '"Essex Forum" (East Orange OR Newark)', 1972, 1980, "Essex Forum"),
    (56, "union-messenger", '"Union Messenger" (Camden OR UAME OR church)', 1978, 1984, "Messenger"),
    (68, "medic-news", '"MEDIC News" Newark', 1970, 1976, "MEDIC"),
    (103, "ujamaa", '"Ujamaa" (Wayne OR "William Paterson")', 1971, 1978, "Ujamaa"),
    (122, "hart-fund", '"Hart Fund" (Newark OR Congressman)', 1971, 1974, "Hart"),
    (105, "primer-ymca", '"Primer" ("East Orange") (YMCA OR Christmas)', 1973, 1978, "Primer"),
    (80, "fire-ii", '"Fire II" (Trenton OR "Trenton State")', 1975, 1984, "Fire"),
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
    return any(m in (text or "").lower() for m in NJ)


def year_of(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text or "")]
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
        send({"action": "screenshot", "name": f"q9-{slug}.png"}, timeout=60)
        extracted = send({"action": "eval", "js": EXTRACT}, timeout=60)
        data = extracted.get("value") or {}
        cards = data.get("results") or []
        nj = [c for c in cards if is_nj(c.get("text") or "")]
        nj.sort(key=lambda c: year_of(c.get("text") or ""))
        report["searches"].append({"id": pid, "slug": slug, "count": data.get("count"), "nj": nj})
        print(f"  count={data.get('count')} cards={len(cards)} nj={len(nj)}", flush=True)
        for card in nj[:2]:
            y = year_of(card.get("text") or "")
            print("  OPEN", card["text"][:110], flush=True)
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
            shot = f"q9open-{slug}-{y}.png"
            send({"action": "screenshot", "name": shot}, timeout=60)
            report["opened"].append(
                {"id": pid, "slug": slug, "card": card["text"], "url": card["href"], "shot": shot}
            )
            time.sleep(0.4)
    (OUT / "q9-1970s.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("done; chrome left open", flush=True)


if __name__ == "__main__":
    main()
