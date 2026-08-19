"""Open hand-picked contemporary clips. Leave Chrome open."""

from __future__ import annotations

import json
import time
from pathlib import Path

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

KEEPERS = [
    {
        "id": "herbert-1895-tribune",
        "pub": "The Sentinel",
        "why": "1895 national profile of R. Henri Herbert as a noted colored leader in Mercer County",
        "url": "https://www.newspapers.com/image/78953914/",
    },
    {
        "id": "herbert-1909-ny-age",
        "pub": "The Sentinel",
        "why": "Black press notice of Herbert, 1909",
        "url": "https://www.newspapers.com/image/33451515/",
    },
    {
        "id": "herbert-1895-trenton-advertiser",
        "pub": "The Sentinel",
        "why": "Local Trenton coverage of Herbert, 1895",
        "url": "https://www.newspapers.com/image/1194116748/",
    },
    {
        "id": "herbert-1909-afro-american",
        "pub": "The Sentinel",
        "why": "Afro-American notice of Herbert, 1909",
        "url": "https://www.newspapers.com/image/1038393954/",
    },
    {
        "id": "trumpet-1888-evening-world",
        "pub": "New Jersey Trumpet",
        "why": "Contemporary 1888 mention, one year after founding",
        "url": "https://www.newspapers.com/image/50663302/",
    },
    {
        "id": "trumpet-1889-washington-bee",
        "pub": "New Jersey Trumpet",
        "why": "Black press mention in the Washington Bee, 1889",
        "url": "https://www.newspapers.com/image/46319440/",
    },
    {
        "id": "trumpet-1893-asbury",
        "pub": "New Jersey Trumpet",
        "why": "Asbury Park Press 1893",
        "url": "https://www.newspapers.com/image/436760060/",
    },
    {
        "id": "murrell-1888-jersey-journal",
        "pub": "New Jersey Trumpet",
        "why": "Jersey Journal Feb 1888, early Murrell/Trumpet window",
        "url": "https://www.newspapers.com/image/1188257526/",
    },
    {
        "id": "echo-1904-monmouth-democrat",
        "pub": "The Echo",
        "why": "Monmouth Democrat Sept 1904, founding year of The Echo",
        "url": "https://www.newspapers.com/image/497174278/",
    },
    {
        "id": "echo-1921-ny-age",
        "pub": "The Echo",
        "why": "New York Age 1921 Red Bank Echo hit",
        "url": "https://www.newspapers.com/image/39621583/",
    },
    {
        "id": "guardian-1940-ny-age",
        "pub": "The New Jersey Guardian",
        "why": "New York Age Feb 1940, inside Guardian years",
        "url": "https://www.newspapers.com/image/40889075/",
    },
    {
        "id": "herald-1932-afro-american",
        "pub": "The Newark Herald",
        "why": "Afro-American July 1932 mention during Herald years",
        "url": "https://www.newspapers.com/image/1134167020/",
    },
    {
        "id": "nj-afro-1943",
        "pub": "New Jersey Afro-American",
        "why": "Baltimore Afro-American Dec 25 1943, possible sister/NJ edition page",
        "url": "https://www.newspapers.com/image/1135990484/",
    },
    {
        "id": "nj-afro-1942",
        "pub": "New Jersey Afro-American",
        "why": "Afro-American Dec 26 1942",
        "url": "https://www.newspapers.com/image/1135986971/",
    },
    {
        "id": "nj-afro-1991-trenton-times",
        "pub": "New Jersey Afro-American",
        "why": "Trenton Times March 16 1991, possible cease-year notice",
        "url": "https://www.newspapers.com/image/1197044099/",
    },
    {
        "id": "nj-afro-2023-masthead-photo",
        "pub": "New Jersey Afro-American",
        "why": "2023 Daily Record with 1947 NJ Afro-American masthead photo and chain history",
        "url": "https://www.newspapers.com/image/962761544/",
    },
]


def main() -> None:
    saved = []
    for item in KEEPERS:
        print("OPEN", item["id"])
        r = send({"action": "goto", "url": item["url"], "wait_ms": 4000})
        shot = f"keeper-{item['id']}.png"
        send({"action": "screenshot", "name": shot})
        text = send({"action": "text", "limit": 2200})
        rec = {
            **item,
            "final_url": r.get("url"),
            "title": r.get("title"),
            "screenshot": str(OUT / "screenshots" / shot),
            "text": (text.get("text") or "")[:2200],
            "ok": r.get("ok"),
            "error": r.get("error"),
        }
        saved.append(rec)
        print(" ", r.get("title"))
        time.sleep(1.8)

    path = OUT / "keepers.json"
    path.write_text(json.dumps(saved, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", path)
    print("done; chrome left open")


if __name__ == "__main__":
    main()
