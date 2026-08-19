"""Corrected Danky pages that were off by one or two leaves."""

from send_cmd import send

PAGES = [
    (72, 280, "hours-after"),
    (66, 313, "jersey-camera"),
    (18, 336, "liberator"),
    (129, 158, "club-world"),
    (21, 426, "nite-lite"),
    (11, 431, "informer"),
]

for pid, page, slug in PAGES:
    url = f"https://archive.org/details/africanamericanne00dank/page/{page}/mode/1up"
    print("OPEN", pid, slug, page, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 6000}, timeout=150)
    send({"action": "screenshot", "name": f"q7r-{slug}-{page}.png"}, timeout=60)
print("done; chrome left open", flush=True)
