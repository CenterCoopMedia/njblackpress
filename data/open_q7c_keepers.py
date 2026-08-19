"""Open the 1929 Apex and 1921 C. N. Green pages with unique shot names."""

from send_cmd import send

PAGES = [
    ("apex-1929-press", "https://www.newspapers.com/image/918002449/", "Apex"),
    ("green-1921-courier", "https://www.newspapers.com/image/478769186/", "Green"),
    ("ironsides-1932-courier", "https://www.newspapers.com/image/446292432/", "Ironsides"),
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
    send({"action": "screenshot", "name": f"q7d-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
