"""More Danky 1up pages for remaining CCC titles. Leave Chrome open."""

from send_cmd import send

PAGES = [
    ("dias-194", "https://archive.org/details/africanamericanne00dank/page/194/mode/1up", 5000),
    ("ash-chatsworth", "https://archive.org/details/africanamericanne00dank/mode/1up?q=Chatsworth", 7000),
    ("ashcan", "https://archive.org/details/africanamericanne00dank/mode/1up?q=Ashcan", 7000),
    ("ease-glassboro", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Little+Ease+Echo%22", 7000),
    ("rug-point", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Point+Breeze%22", 7000),
    ("sixty-lisbon", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22New+Lisbon%22", 7000),
    ("penn-chat", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Penn+Crusader%22+Chatsworth", 7000),
    ("pine-lisbon", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Pine+Needle%22+Lisbon", 7000),
]

for slug, url, wait in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": wait}, timeout=150)
    print(" ", goto.get("ok"), goto.get("url"), flush=True)
    send({"action": "screenshot", "name": f"q7r-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
