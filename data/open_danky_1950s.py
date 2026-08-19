"""Screenshot Danky pages for 1950s civic titles."""

from send_cmd import send

PAGES = [
    (129, 160, "club-world"),
    (72, 281, "hours-after"),
    (66, 315, "jersey-camera"),
    (18, 339, "liberator"),
    (21, 427, "nite-lite"),
    (30, 430, "independent"),
    (11, 432, "informer"),
]

for pid, page, slug in PAGES:
    url = f"https://archive.org/details/africanamericanne00dank/page/{page}/mode/1up"
    print("OPEN", pid, slug, page, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 6000}, timeout=150)
    send({"action": "screenshot", "name": f"q7q-{slug}-{page}.png"}, timeout=60)
print("done; chrome left open", flush=True)
