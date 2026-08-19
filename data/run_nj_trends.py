"""NJ-only newspapers.com pass plus dataset trend counts. Leaves Chrome open."""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "research" / "newspapers-com"
PUBS = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))

SEARCHES = [
    ("herbert", '"R. Henri Herbert"'),
    ("trumpet", '"New Jersey Trumpet"'),
    ("murrell", '"Colonel Murrell" editor'),
    ("echo", '"The Echo" (Rock OR "Red Bank" OR "Long Branch")'),
    ("herald-fold", '"Newark Herald" (ceased OR folded OR suspend)'),
    ("guardian", '"New Jersey Guardian"'),
    ("afro", '"New Jersey Afro-American"'),
    ("colored-newspaper-nj", '"colored newspaper" (Newark OR Trenton OR "Jersey City")'),
]


def dataset_trends() -> dict:
    pubs = PUBS["publications"]
    decades = Counter()
    cities = Counter()
    cease_decades = Counter()
    formats = Counter()
    for p in pubs:
        decades[p.get("decade") or "unknown"] += 1
        cities[p.get("city") or "unknown"] += 1
        formats[p.get("format") or "unknown"] += 1
        yc = p.get("yearCeased")
        if yc:
            cease_decades[f"{(yc // 10) * 10}s"] += 1
    pre1950 = [p for p in pubs if (p.get("yearFounded") or 9999) < 1950]
    newspapers = [p for p in pubs if "newspaper" in (p.get("format") or "").lower()]
    return {
        "total": len(pubs),
        "active": sum(1 for p in pubs if p.get("isActive")),
        "ceased": sum(1 for p in pubs if not p.get("isActive")),
        "pre1950": len(pre1950),
        "newspaper_format": len(newspapers),
        "foundings_by_decade": dict(sorted(decades.items())),
        "closures_by_decade": dict(sorted(cease_decades.items())),
        "top_cities": cities.most_common(12),
        "oldest": sorted(
            [p for p in pubs if p.get("yearFounded")],
            key=lambda p: p["yearFounded"],
        )[:12],
    }


CLICK_NJ = """() => {
    const nodes = [...document.querySelectorAll('a, button, li, span, div')];
    const el = nodes.find(e => {
        const t = (e.innerText || '').replace(/\\s+/g, ' ').trim();
        return /^(New Jersey)\\s*[\\d,K+]*$/.test(t) || /^New Jersey\\s+[\\d,]+$/.test(t);
    });
    if (!el) return {clicked: false, candidates: nodes
        .map(e => (e.innerText || '').replace(/\\s+/g, ' ').trim())
        .filter(t => /new jersey/i.test(t) && t.length < 40)
        .slice(0, 10)};
    el.click();
    return {clicked: true, text: (el.innerText || '').trim().slice(0, 40)};
}"""

EXTRACT = """() => {
    const body = (document.body.innerText || '').replace(/\\s+/g, ' ');
    const count = (body.match(/([\\d,]+)\\s+matches/i) || [null, null])[1];
    const results = [];
    for (const a of document.querySelectorAll('a[href*="/image/"]')) {
        const href = a.href;
        const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
        if (!href || text.length < 12) continue;
        if (results.some(r => r.href === href)) continue;
        results.push({text: text.slice(0, 350), href});
        if (results.length >= 12) break;
    }
    return {url: location.href, title: document.title, count, results, sample: body.slice(0, 900)};
}"""


def main() -> None:
    trends = {"dataset": dataset_trends(), "searches": [], "opened": []}
    oldest = [
        {"id": p["id"], "name": p["name"], "city": p.get("city"), "years": f"{p.get('yearFounded')}-{p.get('yearCeased')}"}
        for p in trends["dataset"]["oldest"]
    ]
    trends["dataset"]["oldest"] = oldest
    print("dataset", trends["dataset"]["total"], "foundings", trends["dataset"]["foundings_by_decade"])

    for slug, keyword in SEARCHES:
        print("SEARCH", slug)
        send({
            "action": "goto",
            "url": "https://www.newspapers.com/search/results/?keyword=" + quote_plus(keyword),
            "wait_ms": 4000,
        })
        clicked = send({"action": "eval", "js": CLICK_NJ})
        print("  nj click", (clicked.get("value") or {}))
        time.sleep(3.5)
        send({"action": "screenshot", "name": f"trend-{slug}.png"})
        extracted = send({"action": "eval", "js": EXTRACT})
        data = extracted.get("value") or {}
        rec = {
            "slug": slug,
            "keyword": keyword,
            "nj_click": clicked.get("value"),
            "url": data.get("url"),
            "count": data.get("count"),
            "results": data.get("results") or [],
        }
        trends["searches"].append(rec)
        print(f"  {rec.get('count')} matches, {len(rec['results'])} cards")

        # Oldest-looking NJ card: prefer 18xx/19xx dates in the card text.
        pick = None
        for r in rec["results"]:
            if any(y in r["text"] for y in ("188", "189", "190", "191", "192", "193", "194")):
                pick = r
                break
        if pick is None and rec["results"]:
            pick = rec["results"][0]
        if pick:
            print("  OPEN", pick["text"][:90])
            opened = send({"action": "goto", "url": pick["href"], "wait_ms": 3500})
            send({
                "action": "fill",
                "selector": 'input[placeholder="Find text on this page"]',
                "text": keyword.split('"')[1] if '"' in keyword else keyword.split()[0],
                "press": "Enter",
                "wait_ms": 2200,
            })
            shot = f"trendclip-{slug}.png"
            send({"action": "screenshot", "name": shot})
            trends["opened"].append({
                "slug": slug,
                "from": pick,
                "url": opened.get("url"),
                "title": opened.get("title"),
                "screenshot": shot,
            })
        time.sleep(2)

    path = OUT / "trends.json"
    path.write_text(json.dumps(trends, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
