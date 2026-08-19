"""Open the two remaining A. P. Smith commemorative pages."""

from send_cmd import send

PAGES = [
    ("landscape-1993-sunday-news", "https://www.newspapers.com/image/634766635/", "Smith"),
    ("landscape-1991-record", "https://www.newspapers.com/image/496517756/", "Smith"),
]

for slug, url, term in PAGES:
    print("OPEN", slug, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 3500}, timeout=120)
    send({
        "action": "fill",
        "selector": 'input[placeholder="Find text on this page"]',
        "text": term,
        "press": "Enter",
        "wait_ms": 2200,
    }, timeout=60)
    send({"action": "screenshot", "name": f"q7more-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
