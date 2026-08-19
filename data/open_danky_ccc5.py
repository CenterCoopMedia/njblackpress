"""1up Danky pages now that sidebar gave printed page numbers. Leave Chrome open."""

from send_cmd import send

PAGES = [
    ("ash-51", "https://archive.org/details/africanamericanne00dank/page/51/mode/1up"),
    ("penn-457", "https://archive.org/details/africanamericanne00dank/page/457/mode/1up"),
    ("pine-465", "https://archive.org/details/africanamericanne00dank/page/465/mode/1up"),
    ("rug-467", "https://archive.org/details/africanamericanne00dank/page/467/mode/1up"),
    ("ease-344", "https://archive.org/details/africanamericanne00dank/page/344/mode/1up"),
    ("sixty-518", "https://archive.org/details/africanamericanne00dank/page/518/mode/1up"),
]

for slug, url in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": 5000}, timeout=150)
    print(" ", goto.get("ok"), goto.get("url"), flush=True)
    send({"action": "screenshot", "name": f"q7t-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
