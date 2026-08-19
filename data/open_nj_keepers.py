"""Open known New Jersey newspaper pages only."""

from __future__ import annotations

import json
import time
from pathlib import Path

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

PAGES = [
    ("herbert-1895-trenton-advertiser", "https://www.newspapers.com/image/1194116748/", "Herbert"),
    ("herbert-1909-trenton-times-p1", "https://www.newspapers.com/image/1191362132/", "Herbert"),
    ("herbert-1909-trenton-advertiser", "https://www.newspapers.com/image/1194273522/", "Herbert"),
    ("herbert-1948-trenton-times-team", "https://www.newspapers.com/image/1194316185/", "Herbert"),
    ("trumpet-1893-asbury", "https://www.newspapers.com/image/436760060/", "Trumpet"),
    ("trumpet-1893-shore-press", "https://www.newspapers.com/image/436807841/", "Trumpet"),
    ("murrell-1888-jersey-journal", "https://www.newspapers.com/image/1188257526/", "Murrell"),
]


def main() -> None:
    saved = []
    for slug, url, term in PAGES:
        print("OPEN", slug)
        send({"action": "goto", "url": url, "wait_ms": 3500})
        send({
            "action": "fill",
            "selector": 'input[placeholder="Find text on this page"]',
            "text": term,
            "press": "Enter",
            "wait_ms": 2200,
        })
        shot = f"njonly-{slug}.png"
        send({"action": "screenshot", "name": shot})
        saved.append({"slug": slug, "url": url, "screenshot": shot})
        time.sleep(1.4)
    (OUT / "nj-keepers-opened.json").write_text(json.dumps(saved, indent=2), encoding="utf-8")
    print("done; chrome left open")


if __name__ == "__main__":
    main()
