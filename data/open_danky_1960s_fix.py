"""Adjacent pages plus BookReader scroll for 1960s entries below the fold."""

from send_cmd import send

SCROLL = """() => {
    const cands = [
        document.querySelector('.BRcontainer'),
        document.querySelector('#IABookReaderWrapper'),
        document.querySelector('.BookReader'),
        document.querySelector('#BookReader'),
        document.scrollingElement
    ].filter(Boolean);
    const info = [];
    for (const el of cands) {
        const before = el.scrollTop || 0;
        el.scrollTop = (el.scrollTop || 0) + 520;
        info.push({tag: el.id || el.className.slice(0,40), before, after: el.scrollTop, sh: el.scrollHeight, ch: el.clientHeight});
    }
    window.scrollBy(0, 420);
    return {info, y: window.scrollY};
}"""

PAGES = [
    ("festival-24b", "https://archive.org/details/africanamericanne00dank/page/24/mode/1up", True),
    ("blacknewark-91b", "https://archive.org/details/africanamericanne00dank/page/91/mode/1up", True),
    ("cricket-179b", "https://archive.org/details/africanamericanne00dank/page/179/mode/1up", True),
    ("deliverance-190", "https://archive.org/details/africanamericanne00dank/page/190/mode/1up", False),
    ("deliverance-191", "https://archive.org/details/africanamericanne00dank/page/191/mode/1up", False),
    ("ncup-417b", "https://archive.org/details/africanamericanne00dank/page/417/mode/1up", True),
    ("ncup-418", "https://archive.org/details/africanamericanne00dank/page/418/mode/1up", False),
    ("utimme-587", "https://archive.org/details/africanamericanne00dank/page/587/mode/1up", False),
    ("utimme-587b", "https://archive.org/details/africanamericanne00dank/page/587/mode/1up", True),
    ("voice-594", "https://archive.org/details/africanamericanne00dank/page/594/mode/1up", False),
    ("voice-594b", "https://archive.org/details/africanamericanne00dank/page/594/mode/1up", True),
]

for slug, url, do_scroll in PAGES:
    print("OPEN", slug, flush=True)
    goto = send({"action": "goto", "url": url, "wait_ms": 5500}, timeout=150)
    print(" ", goto.get("ok"), flush=True)
    if do_scroll:
        sc = send({"action": "eval", "js": SCROLL}, timeout=30)
        print("  scroll", sc.get("value"), flush=True)
    send({"action": "screenshot", "name": f"q8e-{slug}.png"}, timeout=60)

print("done; chrome left open", flush=True)
