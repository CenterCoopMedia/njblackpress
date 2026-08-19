from send_cmd import send
import json

send({"action": "goto", "url": "https://www.newspapers.com/image/497174278/", "wait_ms": 5000}, timeout=120)
send({"action": "screenshot", "name": "probe-toolbar.png"}, timeout=60)
info = send({"action": "eval", "js": """() => ({
  title: document.title,
  url: location.href,
  buttons: [...document.querySelectorAll('button')].map(b => ({
    text: (b.innerText||'').replace(/\\s+/g,' ').trim().slice(0,80),
    aria: b.getAttribute('aria-label'),
    title: b.title
  })).slice(0, 40)
})"""}, timeout=60)
print(json.dumps(info.get("value"), indent=2))
