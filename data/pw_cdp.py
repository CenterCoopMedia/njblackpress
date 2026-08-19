"""Connect to the already-running headed Chrome without owning it.

Playwright's default teardown sends Browser.close over CDP. That is what
kept killing the window. Call disconnect_keep_browser() instead of
browser.close() / playwright.stop().
"""

from __future__ import annotations

import atexit

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"

_playwright = None
_browser = None


def connect():
    global _playwright, _browser
    if _browser is not None:
        return _browser
    _playwright = sync_playwright().start()
    _browser = _playwright.chromium.connect_over_cdp(CDP)

    def _keep_open(*_args, **_kwargs):
        return None

    _browser.close = _keep_open
    try:
        _browser._impl_obj.close = _keep_open
    except Exception:
        pass
    return _browser


def page():
    browser = connect()
    context = browser.contexts[0]
    for pg in context.pages:
        if "newspapers.com" in (pg.url or ""):
            pg.bring_to_front()
            return pg
    if context.pages:
        pg = context.pages[0]
        pg.bring_to_front()
        return pg
    return context.new_page()


def disconnect_keep_browser() -> None:
    """Drop the Playwright socket. Do not send Browser.close."""
    global _playwright, _browser
    try:
        if _browser is not None:
            impl = getattr(_browser, "_impl_obj", None)
            conn = getattr(impl, "_connection", None)
            transport = getattr(conn, "_transport", None)
            ws = getattr(transport, "_ws", None)
            if ws is not None:
                ws.close()
    except Exception:
        pass
    _browser = None
    _playwright = None


atexit.register(disconnect_keep_browser)
