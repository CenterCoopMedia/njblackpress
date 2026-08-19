"""Targeted mention/citation search for the oldest ceased NJ Black papers.

Does not use the broken paper-catalog titleKeyword API.
Leaves Chrome open via the daemon.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

# Oldest first. Queries are exact enough to avoid ABM-missile / generic hits.
SEARCHES = [
    {
        "slug": "herbert-sentinel",
        "label": "R. Henri Herbert / The Sentinel (1880)",
        "keyword": '"R. Henri Herbert"',
        "need": "founding or identity of Trenton's first Black paper",
    },
    {
        "slug": "colored-newspaper-trenton-1880s",
        "label": "colored newspaper Trenton 1880s",
        "keyword": '"colored newspaper" Trenton Herbert',
        "need": "contemporary notice of The Sentinel",
    },
    {
        "slug": "nj-trumpet",
        "label": "New Jersey Trumpet",
        "keyword": '"New Jersey Trumpet"',
        "need": "existence, founding, Murrell, closing",
    },
    {
        "slug": "murrell-trumpet",
        "label": "William Murrell Trumpet",
        "keyword": '"William Murrell" (Trumpet OR newspaper) (Newark OR "Jersey City")',
        "need": "publisher biography / paper founding",
    },
    {
        "slug": "ap-smith-landscape",
        "label": "A.P. Smith The Landscape",
        "keyword": '"The Landscape" "Saddle River" Smith',
        "need": "monthly paper 1881-1901",
    },
    {
        "slug": "rock-echo",
        "label": "William Elijah Rock / The Echo",
        "keyword": '"William Elijah Rock"',
        "need": "Echo founder, Long Branch / Red Bank",
    },
    {
        "slug": "echo-colored-red-bank",
        "label": "The Echo Red Bank as a Black paper",
        "keyword": '"The Echo" "Red Bank" (colored OR Negro OR "Afro-American")',
        "need": "identification of The Echo as Black press",
    },
    {
        "slug": "nj-guardian",
        "label": "New Jersey Guardian",
        "keyword": '"New Jersey Guardian" (colored OR Negro OR "Voice of the Colored")',
        "need": "1934-1942 Newark weekly",
    },
    {
        "slug": "newark-herald-black",
        "label": "Newark Herald as Black paper",
        "keyword": '"Newark Herald" (Negro OR colored OR "Afro-American")',
        "need": "1928-1939 paper identity / succession",
    },
    {
        "slug": "nj-afro-american-1940s",
        "label": "New Jersey Afro-American 1940s",
        "keyword": '"New Jersey Afro-American"',
        "need": "held pages of the paper or contemporary citations",
    },
]


def search_url(keyword: str) -> str:
    return "https://www.newspapers.com/search/results/?keyword=" + quote_plus(keyword)


def extract_js() -> str:
    return """() => {
        const body = (document.body.innerText || '').replace(/\\s+/g, ' ');
        const count = (body.match(/([\\d,]+)\\s+matches/i) || [null, null])[1];
        const results = [];
        const cards = document.querySelectorAll('a[href*="/image/"]');
        for (const a of cards) {
            const href = a.href;
            if (!href || results.some(r => r.href === href)) continue;
            const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
            if (text.length < 8) continue;
            results.push({text: text.slice(0, 400), href});
            if (results.length >= 12) break;
        }
        const papers = [];
        for (const a of document.querySelectorAll('a')) {
            const t = (a.innerText || '').trim();
            const href = a.href || '';
            if (/\\/paper\\//.test(href) && t) papers.push({text: t.slice(0, 200), href});
        }
        return {
            url: location.href,
            title: document.title,
            count,
            results,
            papers: papers.slice(0, 15),
            sample: body.slice(0, 1600)
        };
    }"""


def main() -> None:
    findings = {"searches": [], "opened": []}

    # One location-filtered catalog attempt, then stop using that API.
    print("papers + Location New Jersey")
    send({"action": "goto", "url": "https://www.newspapers.com/papers/", "wait_ms": 4000})
    loc = send({"action": "click", "selector": 'button:has-text("Location"), [aria-label*="Location" i]', "wait_ms": 1500})
    print("location click", loc.get("ok"), loc.get("error"))
    send({"action": "screenshot", "name": "catalog-location-open.png"})
    typed = send({
        "action": "eval",
        "js": """() => {
            const items = [...document.querySelectorAll('button, a, li, label, div')]
                .filter(el => /new jersey/i.test(el.innerText || '') && (el.innerText || '').trim().length < 40)
                .slice(0, 8)
                .map(el => ({tag: el.tagName, text: el.innerText.trim().slice(0, 40), cls: el.className}));
            return items;
        }""",
    })
    print("nj options", typed.get("value"))

    for item in SEARCHES:
        print("SEARCH", item["slug"], item["keyword"])
        r = send({"action": "goto", "url": search_url(item["keyword"]), "wait_ms": 4500})
        if not r.get("ok"):
            findings["searches"].append({**item, "error": r})
            print("  goto failed", r)
            time.sleep(2)
            continue
        send({"action": "screenshot", "name": f"mention-{item['slug']}.png"})
        extracted = send({"action": "eval", "js": extract_js()})
        data = extracted.get("value") or {}
        rec = {
            **item,
            "url": data.get("url") or r.get("url"),
            "count": data.get("count"),
            "results": data.get("results") or [],
            "source_papers": data.get("papers") or [],
            "sample": data.get("sample"),
            "error": extracted.get("error"),
        }
        findings["searches"].append(rec)
        print(f"  {rec.get('count')} matches, {len(rec['results'])} image links")

        # Open only the first image hit. One page per query.
        if rec["results"]:
            hit = rec["results"][0]
            opened = send({"action": "goto", "url": hit["href"], "wait_ms": 4000})
            send({"action": "screenshot", "name": f"clip-{item['slug']}.png"})
            text = send({"action": "text", "limit": 1800})
            findings["opened"].append({
                "slug": item["slug"],
                "from": hit,
                "url": opened.get("url"),
                "title": opened.get("title"),
                "text": (text.get("text") or "")[:1800],
                "error": opened.get("error"),
            })
            print("  opened", opened.get("url"))
        time.sleep(2.5)

    path = OUT / "oldest-mentions.json"
    path.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
