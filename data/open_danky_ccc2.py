"""1up Danky pages for remaining CCC titles. Leave Chrome open."""

from send_cmd import send

PAGES = [
    ("dias-195", "https://archive.org/details/africanamericanne00dank/page/195/mode/1up", 5500),
    ("ash-search", "https://archive.org/details/africanamericanne00dank/page/49/mode/1up?q=%22Ash+Can%22", 7000),
    ("rug-search", "https://archive.org/details/africanamericanne00dank/mode/1up?q=Rugcuttings", 7000),
    ("ease-search", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Little+Ease%22", 7000),
    ("sixty-search", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Sixty+Niner%22", 7000),
    ("penn-search", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Penn+Crusader%22", 7000),
    ("pine-search", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Pine+Needle%22", 7000),
    ("rifle-search", "https://archive.org/details/africanamericanne00dank/mode/1up?q=%22Rifle+Ranger%22", 7000),
]

for slug, url, wait in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": wait}, timeout=150)
    print(" ", goto.get("ok"), goto.get("url"), flush=True)
    send({"action": "screenshot", "name": f"q7q-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
