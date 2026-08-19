"""NJ-only mention search. Open only hits printed in New Jersey papers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

NJ_HINTS = (
    "new jersey",
    "trenton",
    "newark",
    "jersey city",
    "asbury park",
    "red bank",
    "long branch",
    "paterson",
    "camden",
    "atlantic city",
    "montclair",
    "plainfield",
    "freehold",
    "morristown",
    "passaic",
    "elizabeth",
    "new brunswick",
    "princeton",
    "teaneck",
    "east orange",
    "orange,",
    "hackensack",
    "hoboken",
)

SEARCHES = [
    ("herbert", '"R. Henri Herbert"'),
    ("trumpet", '"New Jersey Trumpet"'),
    ("murrell", '"William Murrell" (Trumpet OR editor)'),
    ("echo-red-bank", '"The Echo" "Red Bank"'),
    ("echo-long-branch", '"The Echo" "Long Branch"'),
    ("newark-herald", '"Newark Herald" (colored OR Negro OR Clark)'),
    ("guardian", '"New Jersey Guardian"'),
    ("nj-afro", '"New Jersey Afro-American"'),
]


def is_nj_hit(text: str) -> bool:
    t = (text or "").lower()
    return any(h in t for h in NJ_HINTS)


def extract_js() -> str:
    return """() => {
        const body = (document.body.innerText || '').replace(/\\s+/g, ' ');
        const count = (body.match(/([\\d,]+)\\s+matches/i) || [null, null])[1];
        const results = [];
        for (const a of document.querySelectorAll('a[href*="/image/"]')) {
            const href = a.href;
            const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
            if (!href || text.length < 8) continue;
            if (results.some(r => r.href === href)) continue;
            results.push({text: text.slice(0, 400), href});
            if (results.length >= 15) break;
        }
        return {url: location.href, title: document.title, count, results, sample: body.slice(0, 1200)};
    }"""


def apply_nj_location() -> dict:
    # Fill the search-form location box if present.
    filled = send({
        "action": "fill",
        "selector": 'input[placeholder*="city, state" i], input[placeholder*="Location" i]',
        "text": "New Jersey",
        "press": "Enter",
        "wait_ms": 3500,
    })
    if filled.get("ok"):
        return filled
    # Sidebar refine link.
    return send({
        "action": "click",
        "selector": 'a:has-text("New Jersey"), button:has-text("New Jersey")',
        "wait_ms": 3500,
    })


def main() -> None:
    findings = {"scope": "New Jersey newspapers only", "searches": [], "opened": []}

    for slug, keyword in SEARCHES:
        print("NJ SEARCH", slug, keyword)
        send({
            "action": "goto",
            "url": "https://www.newspapers.com/search/results/?keyword=" + quote_plus(keyword),
            "wait_ms": 3500,
        })
        loc = apply_nj_location()
        send({"action": "screenshot", "name": f"njsearch-{slug}.png"})
        extracted = send({"action": "eval", "js": extract_js()})
        data = extracted.get("value") or {}
        results = data.get("results") or []
        nj_results = [r for r in results if is_nj_hit(r.get("text", ""))]
        rec = {
            "slug": slug,
            "keyword": keyword,
            "url": data.get("url"),
            "count": data.get("count"),
            "location_ok": loc.get("ok"),
            "location_error": loc.get("error"),
            "all_results": results,
            "nj_results": nj_results,
        }
        findings["searches"].append(rec)
        print(f"  {rec.get('count')} matches; {len(nj_results)} look NJ")

        # Open the first two NJ hits only.
        for hit in nj_results[:2]:
            print("  OPEN", hit["text"][:80])
            opened = send({"action": "goto", "url": hit["href"], "wait_ms": 3500})
            # Jump to a distinctive word from the keyword.
            term = "Herbert" if "herbert" in slug else (
                "Trumpet" if slug in ("trumpet", "murrell") else (
                    "Echo" if "echo" in slug else (
                        "Herald" if "herald" in slug else (
                            "Guardian" if "guardian" in slug else "Afro-American"
                        )
                    )
                )
            )
            send({
                "action": "fill",
                "selector": 'input[placeholder="Find text on this page"]',
                "text": term,
                "press": "Enter",
                "wait_ms": 2200,
            })
            shot = f"njclip-{slug}-{len(findings['opened']):02d}.png"
            send({"action": "screenshot", "name": shot})
            findings["opened"].append({
                "slug": slug,
                "from": hit,
                "url": opened.get("url"),
                "title": opened.get("title"),
                "screenshot": shot,
            })
            time.sleep(1.5)
        time.sleep(2)

    path = OUT / "nj-only.json"
    path.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
