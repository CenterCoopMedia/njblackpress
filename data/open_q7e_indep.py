"""Danky p.430 for North Jersey Independent. Leave Chrome open."""

from send_cmd import send

print("OPEN independent-430", flush=True)
send(
    {
        "action": "goto",
        "url": "https://archive.org/details/africanamericanne00dank/page/430/mode/1up",
        "wait_ms": 5500,
    },
    timeout=150,
)
send({"action": "screenshot", "name": "q7v-independent-430.png"}, timeout=60)
print("done; chrome left open", flush=True)
