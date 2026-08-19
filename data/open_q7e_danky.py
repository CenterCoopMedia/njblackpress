"""Danky leftover pages and sidebar searches for 1950s titles. Leave Chrome open."""

from send_cmd import send

PAGES = [
    ("club-159", "https://archive.org/details/africanamericanne00dank/page/159/mode/1up", 5000),
    ("jersey-312", "https://archive.org/details/africanamericanne00dank/page/312/mode/1up", 5000),
    ("hours-281", "https://archive.org/details/africanamericanne00dank/page/281/mode/1up", 5000),
    ("nite-427", "https://archive.org/details/africanamericanne00dank/page/427/mode/1up", 5000),
    ("lib-337", "https://archive.org/details/africanamericanne00dank/page/337/mode/1up", 5000),
    ("hours-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Hours+After%22", 8000),
    ("nite-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Nite+Lite%22", 8000),
    ("indep-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22North+Jersey+Independent%22", 8000),
    ("inform-sb", "https://archive.org/details/africanamericanne00dank/page/n80/mode/1up?q=%22Northern+New+Jersey+Informer%22", 8000),
    ("club-1957", "https://www.newspapers.com/image/1108285509/", 4000),
]

for slug, url, wait in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": wait}, timeout=150)
    print(" ", goto.get("ok"), (goto.get("url") or "")[-90:], flush=True)
    if slug == "club-1957":
        send(
            {
                "action": "fill",
                "selector": 'input[placeholder="Find text on this page"]',
                "text": "Club World",
                "press": "Enter",
                "wait_ms": 2200,
            },
            timeout=60,
        )
    send({"action": "screenshot", "name": f"q7v-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
