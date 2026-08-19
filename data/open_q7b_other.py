"""Screenshot HSP Citizen tour and Danky Princeton search. Leave Chrome open."""

from send_cmd import send

PAGES = [
    (
        "hsp-citizen-tour",
        "https://www.princetonhistory.org/tour/40.html",
        4000,
    ),
    (
        "danky-search-princeton",
        "https://archive.org/details/africanamericanne00dank?q=Princeton",
        6000,
    ),
    (
        "danky-citizen-154-again",
        "https://archive.org/details/africanamericanne00dank/page/154/mode/1up",
        5500,
    ),
]

for slug, url, wait in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": wait}, timeout=150)
    print(" ", goto.get("ok"), goto.get("url"), flush=True)
    send({"action": "screenshot", "name": f"q7n-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
