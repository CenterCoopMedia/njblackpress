"""Leftover Danky pages for entries cut at the bottom. Leave Chrome open."""

from send_cmd import send

PAGES = [
    ("ease-345", "https://archive.org/details/africanamericanne00dank/page/345/mode/1up"),
    ("rug-468", "https://archive.org/details/africanamericanne00dank/page/468/mode/1up"),
    ("sixty-519", "https://archive.org/details/africanamericanne00dank/page/519/mode/1up"),
]

for slug, url in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": 5000}, timeout=150)
    print(" ", goto.get("ok"), goto.get("url"), flush=True)
    send({"action": "screenshot", "name": f"q7u-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
