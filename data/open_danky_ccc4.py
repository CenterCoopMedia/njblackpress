"""Open known Danky pages and wait for search sidebar. Leave Chrome open."""

from send_cmd import send

PAGES = [
    ("pine-464", "https://archive.org/details/africanamericanne00dank/page/464/mode/1up", 5500),
    ("sixty-223", "https://archive.org/details/africanamericanne00dank/page/223/mode/1up", 5000),
    ("ash-sidebar", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Ash+Can%22", 9000),
    ("penn-sidebar", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Penn+Crusader%22", 9000),
    ("sixty-sidebar", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Sixty+Niner%22", 9000),
    ("rug-sidebar", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=Rugcuttings", 9000),
    ("ease-sidebar", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Little+Ease+Echo%22", 9000),
]

for slug, url, wait in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": wait}, timeout=150)
    print(" ", goto.get("ok"), goto.get("url"), flush=True)
    send({"action": "screenshot", "name": f"q7s-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
