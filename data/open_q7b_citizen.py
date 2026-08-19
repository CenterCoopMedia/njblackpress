"""Scroll HSP caption and open Danky 1up page 153 for The Citizen start."""

from send_cmd import send

print("HSP scroll", flush=True)
send({"action": "goto", "url": "https://www.princetonhistory.org/tour/40.html", "wait_ms": 3500}, timeout=150)
send({"action": "eval", "js": "() => { window.scrollTo(0, document.body.scrollHeight); return document.body.innerText.slice(0, 1200); }"}, timeout=30)
send({"action": "screenshot", "name": "q7n-hsp-citizen-caption.png"}, timeout=60)

print("Danky p153 1up", flush=True)
send(
    {
        "action": "goto",
        "url": "https://archive.org/details/africanamericanne00dank/page/153/mode/1up?q=Auston",
        "wait_ms": 6500,
    },
    timeout=150,
)
send({"action": "screenshot", "name": "q7n-danky-citizen-153-auston.png"}, timeout=60)
print("done; chrome left open", flush=True)
