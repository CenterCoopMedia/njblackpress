"""New Jersey-only Newspapers.com search for every publication."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from send_cmd import send

ROOT = Path(__file__).resolve().parent
PUBS = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))["publications"]
CAT_PATH = ROOT / "research" / "source-catalog.json"
OUT = ROOT / "research" / "newspapers-com" / "all138.json"

NJ_CITIES = (
    "new jersey", "trenton", "newark", "jersey city", "asbury park",
    "red bank", "long branch", "paterson", "camden", "atlantic city",
    "montclair", "plainfield", "freehold", "morristown", "passaic",
    "elizabeth", "new brunswick", "princeton", "teaneck", "east orange",
    "hackensack", "hoboken", "bayonne", "irvington", "vineland",
    "orange, new jersey", "paramus", "river edge", "cresskill",
    "saddle river", "saddle brook", "somerset", "swedesboro",
    "pleasantville", "glassboro", "fort dix", "bordentown", "wayne",
    "west orange", "hillside", "glen ridge", "cherry hill", "edison",
    "piscataway", "leonia", "dover", "berlin", "chatsworth",
    "new lisbon", "cape may", "vauxhall", "fort lee",
)

EXTRACT = """() => {
    const results = [];
    for (const a of document.querySelectorAll('a[href*="/image/"]')) {
        const href = a.href;
        const text = (a.innerText || '').trim().replace(/\\s+/g, ' ');
        if (!href || text.length < 12) continue;
        if (results.some(r => r.href === href)) continue;
        results.push({text: text.slice(0, 350), href});
        if (results.length >= 15) break;
    }
    const body = (document.body.innerText || '').replace(/\\s+/g, ' ');
    const count = (body.match(/([\\d,]+)\\s+matches/i) || [null, null])[1];
    return {url: location.href, count, results};
}"""


def is_nj(text: str) -> bool:
    t = (text or "").lower()
    return any(c in t for c in NJ_CITIES)


def year_of(text: str) -> int:
    years = [int(y) for y in re.findall(r"\b(18[7-9]\d|19\d{2}|20[0-2]\d)\b", text or "")]
    return min(years) if years else 9999


def query_for(pub: dict) -> str:
    name = (pub.get("name") or "").split("|")[0].strip()
    city = pub.get("city") or ""
    if city and city.lower() not in ("unknown", "chicago/national", "fort wayne"):
        city_bit = city.split("/")[0]
        return f'"{name}" {city_bit}'
    return f'"{name}" New Jersey'


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}
    log = []

    for pub in PUBS:
        pid = pub["id"]
        q = query_for(pub)
        url = "https://www.newspapers.com/search/results/?keyword=" + quote_plus(q)
        print("NP", pid, q)
        goto = send({"action": "goto", "url": url, "wait_ms": 4000}, timeout=120)
        if not goto.get("ok"):
            rec = {"id": pid, "query": q, "error": goto}
            log.append(rec)
            src = rows[pid]["sources"]["newspapers_com"]
            src["searched"] = True
            src["notes"] = str(goto.get("error") or "goto failed")
            print("  fail", goto.get("error"))
            continue
        extracted = send({"action": "eval", "js": EXTRACT}, timeout=60)
        data = extracted.get("value") or {}
        cards = data.get("results") or []
        nj = [c for c in cards if is_nj(c.get("text", ""))]
        nj.sort(key=lambda c: year_of(c.get("text", "")))
        src = rows[pid]["sources"]["newspapers_com"]
        src["searched"] = True
        src["notes"] = f"{data.get('count')} matches; {len(nj)} NJ cards on first page"
        src["hits"] = [
            {"kind": "search_card", "title": c["text"], "url": c["href"], "localFile": None}
            for c in nj[:5]
        ]
        rec = {"id": pid, "name": pub["name"], "query": q, "count": data.get("count"), "nj": nj}
        log.append(rec)
        print(f"  {data.get('count')} / NJ {len(nj)}")
        time.sleep(1.1)

    cat["publications"] = [rows[i] for i in sorted(rows)]
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
