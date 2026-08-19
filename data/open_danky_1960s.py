"""Screenshot Danky printed pages and sidebar hits for 1960s civic titles."""

from send_cmd import send

PAGES = [
    ("festival-24", "https://archive.org/details/africanamericanne00dank/page/24/mode/1up", 5500),
    ("festival-25", "https://archive.org/details/africanamericanne00dank/page/25/mode/1up", 5500),
    ("blacknewark-90", "https://archive.org/details/africanamericanne00dank/page/90/mode/1up", 5500),
    ("blacknewark-91", "https://archive.org/details/africanamericanne00dank/page/91/mode/1up", 5500),
    ("blacknewark-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Black+New+Ark%22", 8000),
    ("cricket-179", "https://archive.org/details/africanamericanne00dank/page/179/mode/1up", 5500),
    ("cricket-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22The+Cricket%22", 8000),
    ("deliverance-189", "https://archive.org/details/africanamericanne00dank/page/189/mode/1up", 5500),
    ("deliverance-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Deliverance+Voice%22", 8000),
    ("freedom-240", "https://archive.org/details/africanamericanne00dank/page/240/mode/1up", 5500),
    ("ncup-417", "https://archive.org/details/africanamericanne00dank/page/417/mode/1up", 5500),
    ("ncup-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Newark+Community+Union+Project+News%22", 8000),
    ("utimme-588", "https://archive.org/details/africanamericanne00dank/page/588/mode/1up", 5500),
    ("utimme-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=Utimme", 8000),
    ("voice-595", "https://archive.org/details/africanamericanne00dank/page/595/mode/1up", 5500),
    ("voice-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Voice+Associates%22", 8000),
    ("wait-601", "https://archive.org/details/africanamericanne00dank/page/601/mode/1up", 5500),
]

for slug, url, wait in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": wait}, timeout=150)
    print(" ", goto.get("ok"), (goto.get("url") or "")[-100:], flush=True)
    send({"action": "screenshot", "name": f"q8d-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
