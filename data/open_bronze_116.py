"""Screenshot Danky p.116 for the start of Bronze Thrills."""

from send_cmd import send

print("OPEN danky-bronze-116", flush=True)
send({"action": "goto", "url": "https://archive.org/details/africanamericanne00dank/page/116/mode/1up", "wait_ms": 6500}, timeout=150)
send({"action": "screenshot", "name": "q7p-danky-bronze-116.png"}, timeout=60)
print("done; chrome left open", flush=True)
