"""Probe one newspapers.com page: login state, network URLs, download UI.

Does not close Chrome.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pw_cdp import disconnect_keep_browser, page  # noqa: E402

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com" / "downloads"
OUT.mkdir(parents=True, exist_ok=True)
URL = "https://www.newspapers.com/image/497174278/"


def main() -> None:
    pg = page()
    seen: list[dict] = []

    def on_resp(resp):
        u = resp.url
        if re.search(r"img\.|image|download|export|tile|dzi|\.jpg|\.jp2|jpeg|pdf", u, re.I):
            seen.append({"url": u[:400], "status": resp.status, "ct": resp.headers.get("content-type", "")})

    pg.on("response", on_resp)
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(6000)

    body = " ".join((pg.inner_text("body") or "").split())
    print("TITLE", pg.title())
    print("LOGGED_HINT", [m for m in ("Sign In", "Sign in", "My Clippings", "Sign Out", "Subscri") if m in body])

    # dump global JS config that may hold the image path
    cfg = pg.evaluate(
        """() => {
      const out = {};
      for (const k of Object.keys(window)) {
        if (/config|viewer|image|page|__NEXT|initial|state/i.test(k)) {
          try {
            const v = window[k];
            if (v && typeof v === 'object') out[k] = JSON.stringify(v).slice(0, 1500);
          } catch (e) {}
        }
      }
      out['__imgs'] = [...document.querySelectorAll('img')].map(i => i.src).filter(s => s && s.length > 20).slice(0, 40);
      out['__canvas'] = [...document.querySelectorAll('canvas')].map(c => c.width + 'x' + c.height);
      return out;
    }"""
    )
    (OUT / "probe-window.json").write_text(json.dumps(cfg, indent=2)[:200000], encoding="utf-8")
    print("IMGS", json.dumps(cfg.get("__imgs", []), indent=1)[:3000])
    print("CANVAS", cfg.get("__canvas"))

    # open the download panel
    try:
        pg.locator('button[title="Print or Download"]').click(timeout=15000)
        pg.wait_for_timeout(2000)
        print("panel opened")
    except Exception as exc:
        print("panel click fail", exc)

    panel = pg.evaluate(
        """() => [...document.querySelectorAll('button,[role=button],a,div,span')]
        .map(e => ({t: (e.innerText||'').trim().slice(0,60), tag: e.tagName, href: e.href||null, cls:(e.className||'').toString().slice(0,60)}))
        .filter(x => /entire page|select portion|save as|print|download/i.test(x.t) && x.t.length < 60)
        .slice(0, 40)"""
    )
    print("PANEL", json.dumps(panel, indent=1)[:4000])

    (OUT / "probe-network.json").write_text(json.dumps(seen, indent=2), encoding="utf-8")
    print("NET count", len(seen))
    for s in seen[:60]:
        print(" ", s["status"], s["ct"][:30], s["url"][:180])

    disconnect_keep_browser()


if __name__ == "__main__":
    main()
