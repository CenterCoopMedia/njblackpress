"""Jump to the on-page highlight and recapture the actual mention."""

from __future__ import annotations

import json
import time
from pathlib import Path

from send_cmd import send

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"

PAGES = [
    ("herbert-1895-tribune", "https://www.newspapers.com/image/78953914/", "Herbert"),
    ("herbert-1909-ny-age", "https://www.newspapers.com/image/33451515/", "Herbert"),
    ("herbert-1895-trenton-advertiser", "https://www.newspapers.com/image/1194116748/", "Herbert"),
    ("trumpet-1888-evening-world", "https://www.newspapers.com/image/50663302/", "Trumpet"),
    ("trumpet-1889-washington-bee", "https://www.newspapers.com/image/46319440/", "Trumpet"),
    ("trumpet-1893-asbury", "https://www.newspapers.com/image/436760060/", "Trumpet"),
    ("murrell-1888-jersey-journal", "https://www.newspapers.com/image/1188257526/", "Murrell"),
    ("echo-1904-monmouth-democrat", "https://www.newspapers.com/image/497174278/", "colored"),
    ("echo-1921-ny-age", "https://www.newspapers.com/image/39621583/", "Echo"),
    ("herald-1932-afro-american", "https://www.newspapers.com/image/1134167020/", "Herald"),
    ("nj-afro-1943", "https://www.newspapers.com/image/1135990484/", "New Jersey Afro-American"),
    ("nj-afro-1991-trenton-times", "https://www.newspapers.com/image/1197044099/", "Afro-American"),
]


def main() -> None:
    notes = []
    for slug, url, term in PAGES:
        print("JUMP", slug, term)
        send({"action": "goto", "url": url, "wait_ms": 3500})
        filled = send({
            "action": "fill",
            "selector": 'input[placeholder="Find text on this page"]',
            "text": term,
            "press": "Enter",
            "wait_ms": 2500,
        })
        send({"action": "screenshot", "name": f"match-{slug}.png"})
        notes.append({"slug": slug, "term": term, "fill_ok": filled.get("ok"), "url": filled.get("url") or url})
        print(" ", filled.get("ok"), filled.get("error"))
        time.sleep(1.4)
    (OUT / "match-jumps.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
    print("done; chrome left open")


if __name__ == "__main__":
    main()
