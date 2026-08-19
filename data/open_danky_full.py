"""Full-page Danky shots for entries that sit below the fold."""

from send_cmd import send

PAGES = [
    (72, 280, "hours-after"),
    (66, 312, "jersey-camera"),
    (18, 337, "liberator"),
    (11, 431, "informer"),
]

for pid, page, slug in PAGES:
    url = f"https://archive.org/details/africanamericanne00dank/page/{page}/mode/1up"
    print("OPEN", pid, slug, page, flush=True)
    send({"action": "goto", "url": url, "wait_ms": 6000}, timeout=150)
    send({"action": "screenshot", "name": f"q7s-{slug}-{page}-full.png", "full_page": True}, timeout=90)
print("done; chrome left open", flush=True)
