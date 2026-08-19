"""Screenshot likely Danky pages for Bronze Thrills."""

from send_cmd import send

PAGES = [
    ("danky-bronze-117", "https://archive.org/details/africanamericanne00dank/page/117/mode/1up"),
    ("danky-bronze-118", "https://archive.org/details/africanamericanne00dank/page/118/mode/1up"),
]

for slug, url in PAGES:
    print("OPEN", slug, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 6500}, timeout=150)
    send({"action": "screenshot", "name": f"q7p-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
