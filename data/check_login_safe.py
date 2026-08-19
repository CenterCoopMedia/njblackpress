"""Check newspapers.com login. Disconnect Playwright without closing Chrome."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pw_cdp import disconnect_keep_browser, page

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    pg = page()
    if "newspapers.com" not in (pg.url or ""):
        pg.goto("https://www.newspapers.com/", wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(2000)
    body = " ".join((pg.inner_text("body") or "").split()).lower()
    signin = False
    try:
        signin = pg.locator(
            'a:has-text("Sign in"), button:has-text("Sign in"), a[href*="signin"]'
        ).first.is_visible(timeout=1500)
    except Exception:
        pass
    logged = (not signin) and (
        "my clippings" in body
        or "subscriber" in body
        or "sign out" in body
        or "publisher extra" in body
        or "try 7 days free" not in body
    )
    shot = OUT / "login-check.png"
    pg.screenshot(path=str(shot))
    result = {
        "logged_in": logged,
        "signin_visible": signin,
        "url": pg.url,
        "title": pg.title(),
        "screenshot": str(shot),
    }
    print(json.dumps(result, indent=2))
    disconnect_keep_browser()
    return 0 if logged else 2


if __name__ == "__main__":
    raise SystemExit(main())
