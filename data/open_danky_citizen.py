"""Screenshot Danky printed page 153 for The Citizen start."""

from send_cmd import send

print("OPEN danky-citizen-153", flush=True)
send({"action": "goto", "url": "https://archive.org/details/africanamericanne00dank/page/153/mode/1up", "wait_ms": 6500}, timeout=150)
send({"action": "screenshot", "name": "q7m-danky-citizen-153.png"}, timeout=60)
print("done; chrome left open", flush=True)
