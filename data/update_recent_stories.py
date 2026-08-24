"""Fetch recent items from official feeds for active publications."""

from __future__ import annotations

import html
import json
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FEEDS = ROOT / "data" / "recent-story-feeds.json"
PUBLICATIONS = ROOT / "data" / "publications.json"
OUTPUT = ROOT / "data" / "recent-stories.json"
DOCS_OUTPUT = ROOT / "docs" / "data" / "recent-stories.json"
ATOM = "{http://www.w3.org/2005/Atom}"


def text(node: ET.Element, name: str) -> str:
    child = node.find(name)
    return (child.text or "").strip() if child is not None else ""


def clean_title(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def iso_date(value: str) -> str:
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return ""


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "njblackpress-feed-reader/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def parse_feed(raw: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(raw)
    items = root.findall(".//item")
    atom = False
    if not items:
        items = root.findall(f".//{ATOM}entry")
        atom = True

    results = []
    for item in items:
        if atom:
            title = text(item, f"{ATOM}title")
            published = text(item, f"{ATOM}published") or text(item, f"{ATOM}updated")
            link_node = item.find(f"{ATOM}link")
            url = link_node.get("href", "") if link_node is not None else ""
        else:
            title = text(item, "title")
            published = text(item, "pubDate") or text(item, "{http://purl.org/dc/elements/1.1/}date")
            url = text(item, "link")
        title = clean_title(title)
        published = iso_date(published)
        if title and url.startswith("http") and published:
            results.append({"title": title, "url": url, "published": published})
        if len(results) == 5:
            break
    return results


def load_previous_rows() -> dict[int, dict]:
    if not OUTPUT.is_file():
        return {}
    try:
        payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        row["publicationId"]: row
        for row in payload.get("publications", [])
        if isinstance(row, dict) and isinstance(row.get("publicationId"), int)
    }


def retain_previous(rows: list[dict], previous: dict[int, dict], publication_id: int) -> bool:
    row = previous.get(publication_id)
    if not row:
        return False
    rows.append(row)
    return True


def main() -> None:
    feeds = json.loads(FEEDS.read_text(encoding="utf-8"))
    publications = json.loads(PUBLICATIONS.read_text(encoding="utf-8"))["publications"]
    by_id = {publication["id"]: publication for publication in publications}
    previous = load_previous_rows()
    rows = []
    errors = []
    retained = []

    for raw_id, feed_url in feeds.items():
        publication_id = int(raw_id)
        publication = by_id.get(publication_id)
        if not publication or not publication.get("isActive"):
            errors.append(f"{publication_id}: source is not an active publication")
            continue
        try:
            items = parse_feed(fetch(feed_url))
        except Exception as error:
            errors.append(f"{publication_id}: {error}")
            if retain_previous(rows, previous, publication_id):
                retained.append(publication_id)
            continue
        if not items:
            errors.append(f"{publication_id}: feed returned no dated items")
            if retain_previous(rows, previous, publication_id):
                retained.append(publication_id)
            continue
        rows.append({
            "publicationId": publication_id,
            "publication": publication["name"],
            "feedUrl": feed_url,
            "items": items,
        })

    rows.sort(key=lambda row: row["publicationId"])
    payload = {
        "metadata": {
            "updated": date.today().isoformat(),
            "publicationCount": len(rows),
            "retainedPublicationIds": retained,
        },
        "publications": rows,
        "errors": errors,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.copyfile(OUTPUT, DOCS_OUTPUT)
    print(f"wrote {len(rows)} publication feeds; {len(errors)} errors")
    for error in errors:
        print("WARN", error)


if __name__ == "__main__":
    main()
