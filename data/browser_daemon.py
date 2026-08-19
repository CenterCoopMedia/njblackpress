"""Long-lived headed Chrome driver.

Launch Chrome yourself or let this script start it. This process stays
alive and owns the Playwright CDP connection so Chrome is not closed.
Commands are one JSON object in cmd.json. Results go to cmd-result.json.
"""

from __future__ import annotations

import json
import subprocess
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HOME = Path.home()
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PROFILE = Path(__file__).resolve().parents[1] / ".chrome-cdp"
CDP = "http://127.0.0.1:9222"
OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"
CMD = OUT / "cmd.json"
RESULT = OUT / "cmd-result.json"
SHOTS = OUT / "screenshots"


def cdp_ready() -> bool:
    try:
        with urllib.request.urlopen(CDP + "/json/version", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def launch_chrome() -> None:
    if cdp_ready():
        print("chrome already up", flush=True)
        return
    args = [
        str(CHROME),
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={PROFILE}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        "https://www.newspapers.com/",
    ]
    print("launching headed chrome", flush=True)
    subprocess.Popen(args)
    for i in range(30):
        time.sleep(1)
        if cdp_ready():
            print(f"cdp ready after {i + 1}s", flush=True)
            return
    raise RuntimeError("Chrome CDP did not come up")


def write_result(payload: dict) -> None:
    RESULT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("RESULT", payload.get("ok"), payload.get("action"), flush=True)


def handle(page, cmd: dict) -> dict:
    action = cmd.get("action")
    if action == "ping":
        return {"ok": True, "action": action, "url": page.url, "title": page.title()}

    if action == "goto":
        page.goto(cmd["url"], wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(int(cmd.get("wait_ms", 2500)))
        return {"ok": True, "action": action, "url": page.url, "title": page.title()}

    if action == "login_check":
        if "newspapers.com" not in (page.url or ""):
            page.goto("https://www.newspapers.com/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
        body = " ".join((page.inner_text("body") or "").split()).lower()
        signin = False
        try:
            signin = page.locator(
                'a:has-text("Sign in"), button:has-text("Sign in")'
            ).first.is_visible(timeout=1500)
        except Exception:
            pass
        logged = (not signin) and any(
            m in body for m in ("my clippings", "subscriber", "sign out", "publisher extra")
        )
        if not logged and not signin and "try 7 days free" not in body:
            logged = True
        shot = SHOTS / "login-check.png"
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(shot))
        return {
            "ok": True,
            "action": action,
            "logged_in": logged,
            "signin_visible": signin,
            "url": page.url,
            "title": page.title(),
            "screenshot": str(shot),
        }

    if action == "screenshot":
        SHOTS.mkdir(parents=True, exist_ok=True)
        name = cmd.get("name") or "shot.png"
        path = SHOTS / name
        page.screenshot(path=str(path), full_page=bool(cmd.get("full_page")))
        return {"ok": True, "action": action, "path": str(path), "url": page.url}

    if action == "eval":
        value = page.evaluate(cmd["js"])
        return {"ok": True, "action": action, "value": value, "url": page.url}

    if action == "fill":
        page.fill(cmd["selector"], cmd["text"])
        if cmd.get("press"):
            page.press(cmd["selector"], cmd["press"])
        page.wait_for_timeout(int(cmd.get("wait_ms", 2000)))
        return {"ok": True, "action": action, "url": page.url, "title": page.title()}

    if action == "click":
        page.click(cmd["selector"], timeout=10000)
        page.wait_for_timeout(int(cmd.get("wait_ms", 2000)))
        return {"ok": True, "action": action, "url": page.url, "title": page.title()}

    if action == "text":
        limit = int(cmd.get("limit", 2500))
        body = " ".join((page.inner_text("body") or "").split())[:limit]
        return {"ok": True, "action": action, "url": page.url, "title": page.title(), "text": body}

    if action == "stop":
        return {"ok": True, "action": "stop"}

    return {"ok": False, "action": action, "error": "unknown action"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    launch_chrome()
    print("connecting playwright; this process will stay alive", flush=True)
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(CDP)
    context = browser.contexts[0]
    page = next((pg for pg in context.pages if "newspapers.com" in (pg.url or "")), None)
    if page is None:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.newspapers.com/", wait_until="domcontentloaded", timeout=60000)
    page.bring_to_front()
    write_result({"ok": True, "action": "ready", "url": page.url, "title": page.title()})
    print("ready", page.url, flush=True)
    last_mtime = CMD.stat().st_mtime if CMD.exists() else 0
    while True:
        time.sleep(0.4)
        if not CMD.exists():
            continue
        mtime = CMD.stat().st_mtime
        if mtime <= last_mtime:
            continue
        last_mtime = mtime
        try:
            cmd = json.loads(CMD.read_text(encoding="utf-8"))
        except Exception as exc:
            write_result({"ok": False, "error": f"bad cmd json: {exc}"})
            continue
        print("CMD", cmd.get("action"), flush=True)
        try:
            payload = handle(page, cmd)
        except Exception as exc:
            payload = {"ok": False, "action": cmd.get("action"), "error": str(exc)}
        write_result(payload)
        if cmd.get("action") == "stop":
            print("stop requested; leaving chrome open", flush=True)
            return


if __name__ == "__main__":
    main()
