"""Open Harry B. Webber 1991 NJ pages that were overwritten."""

from send_cmd import send

PAGES = [
    ("webber-1991-06-23-ledger", "https://www.newspapers.com/image/1114841380/", "Webber"),
    ("webber-1991-06-24-courier", "https://www.newspapers.com/image/223216862/", "Webber"),
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
    send({"action": "screenshot", "name": f"q7f-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
