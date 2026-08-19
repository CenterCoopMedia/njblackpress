"""Re-open the 1936 Camden CCC pages and jump to Camp Cooper."""

from send_cmd import send

PAGES = [
    ("camp-cooper-1936-courier-post", "https://www.newspapers.com/image/447571125/", "Camp Cooper"),
    ("camp-cooper-1936-evening-courier", "https://www.newspapers.com/image/479485272/", "Camp Cooper"),
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
    send({"action": "screenshot", "name": f"q7h-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
