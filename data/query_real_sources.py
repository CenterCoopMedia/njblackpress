"""Actually query IA, Wayback CDX, Chronicling America, and named library pages."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBS = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))["publications"]
CAT_PATH = ROOT / "research" / "source-catalog.json"
UA = {"User-Agent": "njblackpress-research/1.0 (Center for Cooperative Media)"}

LIBRARY_PAGES = {
    "rutgers_newark_black_newspapers": "https://collections.libraries.rutgers.edu/newark-black-newspapers",
    "nj_state_library_ironsides": "https://www.njstatelib.org/ironsides_echo/",
    "red_bank_echo": "http://www.digifind-it.com/redbank/echo.php",
    "npl_ia_collection": "https://archive.org/details/newarkafamnewspapers",
}


def http_json(url: str, timeout: int = 35):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def http_text(url: str, timeout: int = 35) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return exc.code, body
    except Exception as exc:
        return 0, str(exc)


def live_website(url: str | None) -> str | None:
    if not url or not str(url).startswith("http"):
        return None
    skip = ("worldcat.org", "loc.gov", "chroniclingamerica", "archive.org/details")
    if any(s in url for s in skip):
        return None
    return url


def lccn_of(pub: dict) -> str | None:
    blob = " ".join(str(pub.get(k) or "") for k in ("archiveUrl", "websiteUrl", "historicalNotes"))
    m = re.search(r"lccn[:\s/]*((?:sn|sh)\s?\d{7,10})", blob, re.I)
    if m:
        return re.sub(r"\s+", "", m.group(1).lower())
    m = re.search(r"loc\.gov/item/((?:sn|sh)?\d{8,10})", blob, re.I)
    if m:
        return m.group(1).lower()
    return None


def query_cdx(url: str) -> dict:
    host = urllib.parse.urlparse(url).netloc.replace("www.", "")
    q = urllib.parse.urlencode(
        {
            "url": host + "/*",
            "output": "json",
            "filter": "statuscode:200",
            "fl": "timestamp,original,statuscode,mimetype",
            "collapse": "timestamp:8",
            "limit": 5,
        }
    )
    rows = http_json("https://web.archive.org/cdx/search/cdx?" + q)
    if not rows or len(rows) < 2:
        return {"count": 0, "first": None, "last": None}
    _, *data = rows
    first, last = data[0], data[-1]
    return {
        "count": len(data),
        "first": f"https://web.archive.org/web/{first[0]}/{first[1]}",
        "last": f"https://web.archive.org/web/{last[0]}/{last[1]}",
        "first_ts": first[0],
        "last_ts": last[0],
    }


def query_ia(name: str) -> list[dict]:
    q = f'("{name}") AND (mediatype:texts OR collection:newarkafamnewspapers)'
    url = (
        "https://archive.org/advancedsearch.php?"
        + urllib.parse.urlencode({"q": q, "rows": 4, "output": "json"})
        + "&fl[]=identifier&fl[]=title&fl[]=date&fl[]=collection"
    )
    data = http_json(url)
    return ((data.get("response") or {}).get("docs")) or []


def query_ca(lccn: str) -> dict:
    data = http_json(f"https://chroniclingamerica.loc.gov/lccn/{lccn}.json")
    issues = data.get("issues") or []
    return {
        "title": data.get("name") or data.get("title") or lccn,
        "url": f"https://chroniclingamerica.loc.gov/lccn/{lccn}/",
        "issueCount": len(issues),
    }


def main() -> None:
    cat = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in cat["publications"]}

    print("library pages")
    lib_text = {}
    for key, url in LIBRARY_PAGES.items():
        status, text = http_text(url)
        lib_text[key] = {"status": status, "text": text.lower(), "url": url}
        print(" ", key, status, len(text))
        time.sleep(0.4)

    for pub in PUBS:
        row = rows[pub["id"]]
        name = pub["name"].split("|")[0].strip()

        # Wayback
        wb = row["sources"]["wayback"]
        site = live_website(pub.get("websiteUrl"))
        if not site:
            wb["searched"] = True
            wb["notes"] = "no live websiteUrl; CDX not applicable"
        else:
            print("CDX", pub["id"], site)
            try:
                info = query_cdx(site)
                wb["searched"] = True
                wb["hits"] = []
                if info["count"] == 0:
                    wb["notes"] = f"CDX 0 snapshots for {urllib.parse.urlparse(site).netloc}"
                else:
                    wb["notes"] = f"CDX {info['count']} collapsed snapshots"
                    wb["hits"].append(
                        {
                            "kind": "wayback_snapshot",
                            "title": "earliest",
                            "url": info["first"],
                            "localFile": None,
                            "timestamp": info.get("first_ts"),
                        }
                    )
                    if info["last"] != info["first"]:
                        wb["hits"].append(
                            {
                                "kind": "wayback_snapshot",
                                "title": "latest",
                                "url": info["last"],
                                "localFile": None,
                                "timestamp": info.get("last_ts"),
                            }
                        )
            except Exception as exc:
                wb["searched"] = True
                wb["notes"] = f"CDX error: {exc}"
            time.sleep(0.7)

        # Internet Archive — skip if we already have newarkafam keepers
        ia = row["sources"]["internet_archive"]
        already_npl = any(
            "newarkafam" in str(h.get("url") or "") or h.get("kind") in {"full_issue", "full_issue_preview"}
            for h in ia.get("hits") or []
        )
        if already_npl:
            ia["searched"] = True
            ia["notes"] = ia.get("notes") or "newarkafamnewspapers items already attached"
        elif len(name) < 4:
            ia["searched"] = True
            ia["notes"] = "name too short for IA query"
        else:
            print("IA", pub["id"], name)
            try:
                docs = query_ia(name)
                ia["searched"] = True
                ia["hits"] = []
                for d in docs:
                    ident = d.get("identifier")
                    ia["hits"].append(
                        {
                            "kind": "internet_archive_candidate",
                            "title": d.get("title") or ident,
                            "url": f"https://archive.org/details/{ident}" if ident else None,
                            "localFile": None,
                            "date": d.get("date"),
                            "identifier": ident,
                        }
                    )
                ia["notes"] = f"IA texts query returned {len(docs)} docs"
            except Exception as exc:
                ia["searched"] = True
                ia["notes"] = f"IA error: {exc}"
            time.sleep(0.55)

        # Chronicling America
        ca = row["sources"]["chronicling_america"]
        lccn = lccn_of(pub)
        if not lccn:
            ca["searched"] = True
            ca["notes"] = "no LCCN in record; CA JSON not queried"
            ca["hits"] = []
        else:
            print("CA", pub["id"], lccn)
            try:
                info = query_ca(lccn)
                ca["searched"] = True
                ca["hits"] = [
                    {
                        "kind": "chronicling_america",
                        "title": info["title"],
                        "url": info["url"],
                        "localFile": None,
                        "lccn": lccn,
                        "issueCount": info["issueCount"],
                    }
                ]
                ca["notes"] = f"LCCN {lccn}: {info['issueCount']} digitized issues"
            except Exception as exc:
                ca["searched"] = True
                ca["hits"] = []
                ca["notes"] = f"LCCN {lccn} lookup failed: {exc}"
            time.sleep(0.35)

        # Named library catalogs
        other = row["sources"]["other"]
        other["searched"] = True
        lib_hits = []
        nm = name.lower()
        if pub["id"] in (9, 16, 24) or "herald" in nm:
            lib_hits.append(
                {
                    "kind": "library_collection",
                    "title": "newarkafamnewspapers",
                    "url": LIBRARY_PAGES["npl_ia_collection"],
                    "localFile": None,
                }
            )
        if pub["id"] == 128 or "newark black newspapers" in nm:
            page = lib_text["rutgers_newark_black_newspapers"]
            lib_hits.append(
                {
                    "kind": "library_collection",
                    "title": "Rutgers Newark Black Newspapers",
                    "url": page["url"],
                    "localFile": None,
                    "httpStatus": page["status"],
                }
            )
        if pub["id"] == 31 or nm == "the echo":
            page = lib_text["red_bank_echo"]
            found = "echo" in page["text"]
            lib_hits.append(
                {
                    "kind": "library_collection",
                    "title": "Red Bank Public Library Echo",
                    "url": page["url"],
                    "localFile": None,
                    "httpStatus": page["status"],
                    "pageMentionsEcho": found,
                }
            )
        if pub["id"] == 57 or "ironsides" in nm:
            page = lib_text["nj_state_library_ironsides"]
            found = "ironsides" in page["text"]
            lib_hits.append(
                {
                    "kind": "library_collection",
                    "title": "NJ State Library Ironsides Echo",
                    "url": page["url"],
                    "localFile": None,
                    "httpStatus": page["status"],
                    "pageMentionsIronsides": found,
                }
            )
        other["hits"] = lib_hits + [h for h in other.get("hits") or [] if h.get("kind") == "website"]
        if lib_hits:
            other["notes"] = f"{len(lib_hits)} named library page(s) checked"
        else:
            other["notes"] = "named library catalogs checked; no collection match for this title"

        if row["keepers"]:
            row["status"] = "has_keeper"
        else:
            row["status"] = "searched_none"
        row["updated"] = date.today().isoformat()

    cat["publications"] = [rows[i] for i in sorted(rows)]
    cat["counts"] = {
        "has_keeper": sum(1 for r in rows.values() if r["status"] == "has_keeper"),
        "searched_none": sum(1 for r in rows.values() if r["status"] == "searched_none"),
        "not_searched": sum(1 for r in rows.values() if r["status"] == "not_searched"),
    }
    cat["generated"] = date.today().isoformat()
    CAT_PATH.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", CAT_PATH)
    print("counts", cat["counts"])


if __name__ == "__main__":
    main()
