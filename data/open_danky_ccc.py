"""Screenshot Danky pages for remaining NJ CCC camp papers. Leave Chrome open."""

from send_cmd import send

PAGES = [
    ("ash-can-50", "https://archive.org/details/africanamericanne00dank/page/50/mode/1up", 5500),
    ("rugcuttings", "https://archive.org/details/africanamericanne00dank?q=Rugcuttings", 6500),
    ("sixty-niner", "https://archive.org/details/africanamericanne00dank?q=%22Sixty+Niner%22", 6500),
    ("little-ease", "https://archive.org/details/africanamericanne00dank?q=%22Little+Ease+Echo%22", 6500),
    ("dias-creek", "https://archive.org/details/africanamericanne00dank?q=%22Dias+Creek%22", 6500),
    ("rifle-ranger", "https://archive.org/details/africanamericanne00dank?q=%22Rifle+Ranger%22", 6500),
    ("penn-crusader", "https://archive.org/details/africanamericanne00dank?q=%22Penn+Crusader%22", 6500),
    ("pine-needle", "https://archive.org/details/africanamericanne00dank?q=%22Pine+Needle%22+Lisbon", 6500),
]

for slug, url, wait in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": wait}, timeout=150)
    print(" ", goto.get("ok"), (goto.get("url") or "")[-80:], flush=True)
    send({"action": "screenshot", "name": f"q7p-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
