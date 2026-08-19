"""Full-page HSP tour shot. Leave Chrome open."""

from send_cmd import send

print("HSP full page", flush=True)
send({"action": "goto", "url": "https://www.princetonhistory.org/tour/40.html", "wait_ms": 3500}, timeout=150)
send({"action": "screenshot", "name": "q7n-hsp-citizen-full.png", "full_page": True}, timeout=60)
print("done; chrome left open", flush=True)
