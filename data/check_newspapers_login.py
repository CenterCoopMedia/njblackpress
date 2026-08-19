"""Connect to a local Chrome CDP session and check newspapers.com login."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"
OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"
SHOT = OUT / "login-check.png"


def looks_logged_in(page) -> tuple[bool, str]:
    url = page.url or ""
    title = page.title() or ""
    body = ""
    try:
        body = page.inner_text("body", timeout=8000)
    except Exception:
        body = ""
    snippet = " ".join(body.split())[:1200].lower()

    login_markers = [
        "sign in to newspapers.com",
        "log in to newspapers.com",
        "create a free account",
        "start your free trial",
        "already have an account",
    ]
    if any(m in snippet for m in login_markers):
        return False, f"login wall text on {url}"

    signin = page.locator(
        'a[href*="signin"], a[href*="sign-in"], a[href*="login"], '
        'button:has-text("Sign in"), a:has-text("Sign in"), '
        'button:has-text("Log in"), a:has-text("Log in")'
    )
    try:
        visible_signin = signin.first.is_visible(timeout=2000)
    except Exception:
        visible_signin = False

    member_markers = [
        "my clippings",
        "saved clippings",
        "subscriber",
        "publisher extra",
        "sign out",
        "log out",
        "account settings",
    ]
    if any(m in snippet for m in member_markers):
        return True, f"member UI on {url} ({title})"

    # Account menu / avatar in header is a strong logged-in signal.
    account = page.locator(
        '[aria-label*="Account" i], [data-testid*="account" i], '
        'a[href*="/profile"], a[href*="/account"], img[alt*="profile" i]'
    )
    try:
        if account.first.is_visible(timeout=1500):
            return True, f"account control visible on {url}"
    except Exception:
        pass

    if visible_signin:
        return False, f"sign-in control visible on {url}"

    cookies = {c["name"].lower() for c in page.context.cookies("https://www.newspapers.com")}
    authish = [c for c in cookies if any(k in c for k in ("session", "auth", "token", "member", "user"))]
    if authish and "signin" not in url.lower():
        return True, f"auth cookies present: {authish[:6]}"

    return False, f"no login signal on {url} ({title})"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    last_err = None
    for attempt in range(15):
        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(CDP)
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = next((pg for pg in context.pages if "newspapers.com" in (pg.url or "")), None)
                if page is None:
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto("https://www.newspapers.com/", wait_until="domcontentloaded", timeout=60000)
                else:
                    page.bring_to_front()
                    if "signin" in page.url.lower() or page.url.rstrip("/") == "https://www.newspapers.com":
                        page.goto("https://www.newspapers.com/", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                logged_in, reason = looks_logged_in(page)
                page.screenshot(path=str(SHOT), full_page=False)
                result = {
                    "logged_in": logged_in,
                    "reason": reason,
                    "url": page.url,
                    "title": page.title(),
                    "screenshot": str(SHOT),
                }
                print(json.dumps(result, indent=2))
                return 0 if logged_in else 2
        except Exception as exc:
            last_err = exc
            time.sleep(1)
    print(json.dumps({"logged_in": False, "reason": f"cdp connect failed: {last_err}"}))
    return 3


if __name__ == "__main__":
    sys.exit(main())
