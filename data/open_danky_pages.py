"""Screenshot the correct Danky printed pages."""

from send_cmd import send

PAGES = [
    ("danky-camden-131", "https://archive.org/details/africanamericanne00dank/page/131/mode/1up"),
    ("danky-citizen-154", "https://archive.org/details/africanamericanne00dank/page/154/mode/1up"),
    ("danky-hiram-277", "https://archive.org/details/africanamericanne00dank/page/277/mode/1up"),
]

for slug, url in PAGES:
    print("OPEN", slug, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 6500}, timeout=150)
    send({"action": "screenshot", "name": f"q7m-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
