"""Drive the logged-in newspapers.com Chrome session and collect NJ Black press hits.

Does not close the browser.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "research" / "newspapers-com"
SHOTS = OUT / "screenshots"
CLIPS = OUT / "clips"
CDP = "http://127.0.0.1:9222"

PRIORITY = [
    ("The Sentinel", "Trenton"),
    ("New Jersey Trumpet", "Newark"),
    ("The Landscape", "Saddle River"),
    ("The Echo", "Red Bank"),
    ("The Echo", "Long Branch"),
    ("The Newark Herald", "Newark"),
    ("New Jersey Herald News", "Newark"),
    ("The New Jersey Guardian", "Newark"),
    ("New Jersey Afro-American", "Newark"),
    ("The Jersey Express", "Montclair"),
    ("The Citizen", "Princeton"),
    ("The Camden News", "Camden"),
    ("Apex News", "Atlantic City"),
    ("New Jersey Record", "Newark"),
    ("Black Newark", "Newark"),
    ("The Nubian News", "Trenton"),
    ("The Connection", "Teaneck"),
    ("North Jersey Independent", "Paterson"),
    ("The Liberator", "Paterson"),
]


def looks_logged_in(page) -> tuple[bool, str]:
    url = page.url or ""
    try:
        body = page.inner_text("body", timeout=8000)
    except Exception:
        body = ""
    text = " ".join(body.split()).lower()
    if any(m in text for m in ("sign in to newspapers.com", "start your free trial", "create a free account")):
        return False, f"login wall on {url}"
    signin = page.locator('a:has-text("Sign in"), button:has-text("Sign in"), a[href*="signin"]')
    try:
        if signin.first.is_visible(timeout=1500):
            return False, f"sign-in visible on {url}"
    except Exception:
        pass
    if any(m in text for m in ("my clippings", "subscriber", "sign out", "log out", "publisher extra")):
        return True, f"member UI on {url}"
    cookies = {c["name"].lower() for c in page.context.cookies("https://www.newspapers.com")}
    if any("session" in c or "auth" in c or "token" in c for c in cookies):
        return True, f"auth cookies on {url}"
    return False, f"no login signal on {url}"


def collect_links(page, pattern: str) -> list[dict]:
    return page.evaluate(
        """(pattern) => {
            const re = new RegExp(pattern, 'i');
            const out = [];
            for (const a of document.querySelectorAll('a[href]')) {
                const href = a.href || '';
                if (!re.test(href)) continue;
                const text = (a.innerText || a.getAttribute('title') || '').trim();
                if (!text && !href) continue;
                out.push({text: text.slice(0, 200), href});
            }
            const seen = new Set();
            return out.filter(x => {
                if (seen.has(x.href)) return false;
                seen.add(x.href);
                return true;
            }).slice(0, 40);
        }""",
        pattern,
    )


def save_json(name: str, payload) -> Path:
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    CLIPS.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        page = next((pg for pg in context.pages if "newspapers.com" in (pg.url or "")), None)
        if page is None:
            page = context.pages[0] if context.pages else context.new_page()
        page.bring_to_front()
        page.goto("https://www.newspapers.com/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        logged_in, reason = looks_logged_in(page)
        page.screenshot(path=str(SHOTS / "home.png"))
        print(json.dumps({"logged_in": logged_in, "reason": reason, "url": page.url}))
        if not logged_in:
            save_json("login-status.json", {"logged_in": False, "reason": reason, "url": page.url})
            print("STOP: not logged in. Browser left open.")
            return 2

        findings = {
            "logged_in": True,
            "home_url": page.url,
            "paper_directory": {},
            "title_searches": [],
            "opened_pages": [],
        }

        # Browse NJ papers in the directory.
        dir_url = "https://www.newspapers.com/papers/?state=nj"
        page.goto(dir_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        page.screenshot(path=str(SHOTS / "papers-nj.png"), full_page=True)
        findings["paper_directory"] = {
            "url": page.url,
            "title": page.title(),
            "links": collect_links(page, r"/paper/|/browse/|/image/"),
            "text_sample": " ".join((page.inner_text("body") or "").split())[:2500],
        }

        # Also try the keyword search for African American / Black press in NJ.
        for label, url in [
            ("black-new-jersey", "https://www.newspapers.com/search/results/?keyword=%22New%20Jersey%22%20%22colored%22%20newspaper&date-year=1880&date-year-end=1970"),
            ("afro-american-nj", "https://www.newspapers.com/search/results/?keyword=%22Afro-American%22%20Newark"),
            ("papers-search-echo", "https://www.newspapers.com/papers/search/?query=echo%20new%20jersey"),
        ]:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3500)
                page.screenshot(path=str(SHOTS / f"{label}.png"))
                findings.setdefault("extra_searches", []).append({
                    "label": label,
                    "url": page.url,
                    "title": page.title(),
                    "links": collect_links(page, r"/paper/|/image/|/clip/|/article/|/search/"),
                    "text_sample": " ".join((page.inner_text("body") or "").split())[:1800],
                })
            except Exception as exc:
                findings.setdefault("extra_searches", []).append({"label": label, "error": str(exc)})

        for title, city in PRIORITY:
            query = f'"{title}" {city}'
            url = (
                "https://www.newspapers.com/search/results/?"
                f"keyword={quote_plus(query)}"
            )
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3500)
                slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                page.screenshot(path=str(SHOTS / f"search-{slug}.png"))
                body = " ".join((page.inner_text("body") or "").split())
                rec = {
                    "title": title,
                    "city": city,
                    "url": page.url,
                    "page_title": page.title(),
                    "links": collect_links(page, r"/paper/|/image/|/clip/|/article/"),
                    "result_hint": None,
                    "text_sample": body[:1800],
                }
                m = re.search(r"([\d,]+)\s+results?", body, re.I)
                if m:
                    rec["result_hint"] = m.group(1)
                findings["title_searches"].append(rec)
                print(f"search {title}: {rec.get('result_hint')} results, {len(rec['links'])} links")
                time.sleep(1.2)
            except Exception as exc:
                findings["title_searches"].append({
                    "title": title,
                    "city": city,
                    "error": str(exc),
                })
                print(f"search {title} failed: {exc}")

        # Open the first real paper/image hit from the strongest searches.
        opened = 0
        for rec in findings["title_searches"]:
            if opened >= 8:
                break
            for link in rec.get("links") or []:
                href = link.get("href") or ""
                if not any(x in href for x in ("/paper/", "/image/", "/clip/")):
                    continue
                if "search" in href and "/image/" not in href and "/paper/" not in href:
                    continue
                try:
                    page.goto(href, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(3500)
                    slug = re.sub(r"[^a-z0-9]+", "-", rec["title"].lower()).strip("-")
                    shot = SHOTS / f"open-{opened:02d}-{slug}.png"
                    page.screenshot(path=str(shot), full_page=False)
                    img_url = None
                    try:
                        img = page.locator("img").first
                        if img.count():
                            img_url = img.get_attribute("src")
                    except Exception:
                        pass
                    findings["opened_pages"].append({
                        "from_title": rec["title"],
                        "href": page.url,
                        "link_text": link.get("text"),
                        "screenshot": str(shot),
                        "img_url": img_url,
                        "page_title": page.title(),
                        "text_sample": " ".join((page.inner_text("body") or "").split())[:1500],
                    })
                    opened += 1
                    print(f"opened {page.url}")
                    time.sleep(1.5)
                    break
                except Exception as exc:
                    findings["opened_pages"].append({
                        "from_title": rec["title"],
                        "href": href,
                        "error": str(exc),
                    })

        save_json("findings.json", findings)
        print(f"saved {OUT / 'findings.json'}")
        print("browser left open")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
