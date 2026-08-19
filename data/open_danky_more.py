"""Screenshot Danky pages for The Citizen and Hiram Star-News."""

from send_cmd import send

PAGES = [
    ("danky-camden", "https://archive.org/details/africanamericanne00dank/page/133/mode/1up"),
    ("danky-citizen", "https://archive.org/details/africanamericanne00dank/page/157/mode/1up"),
    ("danky-hiram", "https://archive.org/details/africanamericanne00dank/page/286/mode/1up"),
]

for slug, url in PAGES:
    print("OPEN", slug, url, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 7000}, timeout=150)
    send({"action": "screenshot", "name": f"q7k-{slug}.png"}, timeout=60)
print("done; chrome left open", flush=True)
