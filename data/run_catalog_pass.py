"""First pass: does newspapers.com HOLD the oldest NJ Black papers?"""

from __future__ import annotations

import json
import time
from pathlib import Path

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"
SHOTS = OUT / "screenshots"

# Oldest ceased titles first. Catalog query is the paper-directory filter,
# not a full-text article search.
CATALOG = [
    ("new-jersey-afro-american", "New Jersey Afro-American"),
    ("afro-american", "Afro-American"),
    ("newark-herald", "Newark Herald"),
    ("new-jersey-herald-news", "New Jersey Herald News"),
    ("new-jersey-guardian", "New Jersey Guardian"),
    ("new-jersey-trumpet", "New Jersey Trumpet"),
    ("the-echo-red-bank", "The Echo Red Bank"),
    ("the-echo", "The Echo"),
    ("the-sentinel-trenton", "The Sentinel Trenton"),
    ("the-landscape-saddle", "The Landscape Saddle River"),
    ("the-citizen-princeton", "The Citizen Princeton"),
    ("camden-news", "The Camden News"),
    ("apex-news", "Apex News Atlantic City"),
]


def dump(name: str, payload) -> None:
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path)


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    findings = {"catalog": []}

    r = send({"action": "goto", "url": "https://www.newspapers.com/papers/", "wait_ms": 4000})
    print("papers page", r.get("url"), r.get("title"))
    send({"action": "screenshot", "name": "catalog-home.png"})

    selectors = send({
        "action": "eval",
        "js": """() => {
            const inputs = [...document.querySelectorAll('input')].map(el => ({
                type: el.type, placeholder: el.placeholder, name: el.name,
                id: el.id, aria: el.getAttribute('aria-label')
            }));
            const cards = [...document.querySelectorAll('a')].slice(0, 20).map(a => ({
                text: (a.innerText||'').trim().slice(0,120), href: a.href
            }));
            return {inputs, url: location.href, title: document.title};
        }""",
    })
    dump("catalog-page-structure.json", selectors)
    print("inputs", json.dumps(selectors.get("value", {}).get("inputs", []), indent=2)[:1500])

    # Prefer a visible filter input.
    filter_sel = None
    for item in (selectors.get("value") or {}).get("inputs") or []:
        blob = " ".join(str(item.get(k) or "") for k in ("placeholder", "aria", "name", "id")).lower()
        if "filter" in blob or "paper" in blob or "location" in blob or "search" in blob:
            if item.get("placeholder"):
                filter_sel = f'input[placeholder="{item["placeholder"]}"]'
                break
    if not filter_sel:
        filter_sel = 'input[placeholder*="Filter" i], input[type="search"]'
    print("using selector", filter_sel)

    for slug, query in CATALOG:
        print("CATALOG", query)
        # Return to catalog each time so the filter is clean.
        send({"action": "goto", "url": "https://www.newspapers.com/papers/", "wait_ms": 2500})
        filled = send({
            "action": "fill",
            "selector": filter_sel,
            "text": query,
            "press": "Enter",
            "wait_ms": 3500,
        })
        if not filled.get("ok"):
            print("fill failed", filled)
        send({"action": "screenshot", "name": f"catalog-{slug}.png"})
        extracted = send({
            "action": "eval",
            "js": """() => {
                const text = document.body.innerText || '';
                const papers = [];
                for (const a of document.querySelectorAll('a[href*="/paper/"]')) {
                    const t = (a.innerText || '').trim();
                    if (!t) continue;
                    papers.push({text: t.slice(0, 300), href: a.href});
                }
                const seen = new Set();
                const uniq = [];
                for (const p of papers) {
                    if (seen.has(p.href)) continue;
                    seen.add(p.href);
                    uniq.push(p);
                }
                return {
                    url: location.href,
                    title: document.title,
                    count_hint: (text.match(/Showing\\s+[\\d,]+\\s+papers?/i) || [null])[0],
                    papers: uniq.slice(0, 20),
                    sample: text.replace(/\\s+/g, ' ').slice(0, 1200)
                };
            }""",
        })
        rec = {
            "query": query,
            "slug": slug,
            "fill_ok": filled.get("ok"),
            "url": (extracted.get("value") or {}).get("url") or filled.get("url"),
            "data": extracted.get("value"),
            "error": extracted.get("error"),
        }
        findings["catalog"].append(rec)
        n = len(((extracted.get("value") or {}).get("papers")) or [])
        print(f"  -> {n} paper links; {rec.get('url')}")
        time.sleep(1.5)

    dump("catalog-pass.json", findings)
    print("done catalog pass; chrome left open")


if __name__ == "__main__":
    main()
