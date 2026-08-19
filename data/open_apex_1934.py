"""Open the 1934 Press of Atlantic City Apex News cards and the Danky page."""

from send_cmd import send

PAGES = [
    ("apex-1934-07-28-a", "https://www.newspapers.com/image/918183122/", "Apex News"),
    ("apex-1934-07-28-b", "https://www.newspapers.com/image/918182905/", "Apex News"),
    ("apex-1935-07-19", "https://www.newspapers.com/image/918294217/", "Apex News"),
    ("danky-p46", "https://archive.org/details/africanamericanne00dank/page/46/mode/1up", None),
]

for slug, url, term in PAGES:
    print("OPEN", slug, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 5000 if term else 7000}, timeout=150)
    if term:
        send({
            "action": "fill",
            "selector": 'input[placeholder="Find text on this page"]',
            "text": term,
            "press": "Enter",
            "wait_ms": 2200,
        }, timeout=60)
    send({"action": "screenshot", "name": f"q7j-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
