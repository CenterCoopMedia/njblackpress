"""Capture current homepages for active NJ Black Press publications.

The job is deliberately bounded:

* It reads an explicit source manifest and validates each row against the
  current publication data.
* It processes one source at a time.
* It writes SingleFile HTML only to ``data/research/live-sites``.
* It writes rights-restricted viewport screenshots and their PNG metadata to
  ``data/research/current-sites``.

Run from the repository root:

    python3 data/capture_active_homepages.py

The command keeps successful captures when another source fails. The output
JSON records each failure so a later run can retry it without guessing.
"""

from __future__ import annotations

import argparse
import binascii
import datetime as dt
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
SOURCES_PATH = ROOT / "data" / "active-homepage-sources.json"
CURRENT_HOMEpages_PATH = ROOT / "data" / "current-homepages.json"
DOCS_CURRENT_HOMEpages_PATH = ROOT / "docs" / "data" / "current-homepages.json"
LIVE_SITES_DIR = ROOT / "data" / "research" / "live-sites"
CURRENT_SITES_DIR = ROOT / "data" / "research" / "current-sites"

DEFAULT_WIDTH = 1440
DEFAULT_HEIGHT = 900
DEFAULT_WAIT_MS = 3000
DEFAULT_TIMEOUT_MS = 60000
DEFAULT_SINGLE_FILE_TIMEOUT_S = 120


class CaptureError(RuntimeError):
    """A bounded capture step failed."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture-date",
        default=dt.date.today().isoformat(),
        help="Capture date in YYYY-MM-DD format. Defaults to the local date.",
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=SOURCES_PATH,
        help="Source manifest path.",
    )
    parser.add_argument(
        "--publications",
        type=Path,
        default=PUBLICATIONS_PATH,
        help="Publication data path.",
    )
    parser.add_argument(
        "--single-file",
        default=os.environ.get("SINGLE_FILE_BIN") or shutil.which("single-file") or "single-file",
        help="SingleFile executable. Defaults to single-file on PATH.",
    )
    parser.add_argument(
        "--chromium",
        default=(
            os.environ.get("CHROMIUM_BIN")
            or shutil.which("chromium-browser")
            or shutil.which("chromium")
            or "chromium-browser"
        ),
        help="Chromium executable. Defaults to chromium-browser on PATH.",
    )
    parser.add_argument(
        "--single-file-timeout",
        type=int,
        default=DEFAULT_SINGLE_FILE_TIMEOUT_S,
        help="Maximum seconds for each SingleFile capture.",
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=DEFAULT_WAIT_MS,
        help="Milliseconds to wait before each viewport screenshot.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        help="Maximum milliseconds for each browser navigation.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help="Viewport width in pixels.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help="Viewport height in pixels.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaptureError(f"could not read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CaptureError(f"JSON root must be an object: {path}")
    return value


def is_valid_http_url(value: Any) -> bool:
    """Return true only for an absolute HTTP or HTTPS URL with a host."""

    if not isinstance(value, str) or not value.strip() or value != value.strip():
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return False
    try:
        return bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def active_publications(publications_payload: dict[str, Any]) -> dict[int, dict[str, Any]]:
    rows = publications_payload.get("publications")
    if not isinstance(rows, list):
        raise CaptureError("publications.json has no publications list")
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), int):
            raise CaptureError("each publication must have an integer id")
        result[row["id"]] = row
    return {pid: row for pid, row in result.items() if row.get("isActive") is True}


def validate_sources(
    source_payload: dict[str, Any],
    publications_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Validate the manifest and return source rows enriched from publications."""

    rows = source_payload.get("sources")
    if not isinstance(rows, list) or not rows:
        raise CaptureError("active-homepage-sources.json has no sources")

    active = active_publications(publications_payload)
    seen_ids: set[int] = set()
    seen_urls: set[str] = set()
    validated: list[dict[str, Any]] = []

    for source in rows:
        if not isinstance(source, dict):
            raise CaptureError("each homepage source must be an object")
        publication_id = source.get("publicationId")
        url = source.get("url")
        if not isinstance(publication_id, int):
            raise CaptureError(f"source has an invalid publicationId: {source!r}")
        if publication_id in seen_ids:
            raise CaptureError(f"duplicate publicationId in source manifest: {publication_id}")
        if not is_valid_http_url(url):
            raise CaptureError(f"source {publication_id} has an invalid HTTP URL: {url!r}")
        if url in seen_urls:
            raise CaptureError(f"duplicate URL in source manifest: {url}")
        publication = active.get(publication_id)
        if publication is None:
            raise CaptureError(f"source {publication_id} is not an active publication")
        if publication.get("websiteUrl") != url:
            raise CaptureError(
                f"source {publication_id} URL does not match publications.json: "
                f"{url!r} != {publication.get('websiteUrl')!r}"
            )
        if source.get("name") != publication.get("name"):
            raise CaptureError(
                f"source {publication_id} name does not match publications.json: "
                f"{source.get('name')!r} != {publication.get('name')!r}"
            )
        seen_ids.add(publication_id)
        seen_urls.add(url)
        validated.append(
            {
                "publicationId": publication_id,
                "publication": publication.get("name") or source["name"],
                "sourceUrl": url,
            }
        )

    expected = {
        publication_id
        for publication_id, publication in active.items()
        if is_valid_http_url(publication.get("websiteUrl"))
    }
    if seen_ids != expected:
        missing = sorted(expected - seen_ids)
        extra = sorted(seen_ids - expected)
        raise CaptureError(
            "source manifest does not match active publications with valid HTTP URLs; "
            f"missing={missing}, extra={extra}"
        )
    return validated


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "publication"


def artifact_stem(source: dict[str, Any]) -> str:
    return f"{source['publicationId']:03d}-{slugify(source['publication'])}"


def command_preview(command: list[str]) -> str:
    """Keep errors useful without printing a full URL or shell command."""

    if not command:
        return "capture command"
    return Path(command[0]).name


def run_single_file(
    source: dict[str, Any],
    output_path: Path,
    single_file_bin: str,
    chromium_bin: str,
    width: int,
    height: int,
    wait_ms: int,
    timeout_s: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        single_file_bin,
        f"--browser-executable-path={chromium_bin}",
        "--browser-headless=true",
        f"--browser-width={width}",
        f"--browser-height={height}",
        f"--browser-wait-delay={wait_ms}",
        f"--browser-load-max-time={DEFAULT_TIMEOUT_MS}",
        f"--browser-capture-max-time={DEFAULT_TIMEOUT_MS}",
        "--browser-wait-until=networkIdle",
        "--browser-wait-until-fallback=true",
        "--block-scripts=false",
        "--load-deferred-images=true",
        "--filename-conflict-action=overwrite",
        "--insert-single-file-comment=true",
        "--save-original-URLs=true",
        "--resolve-links=true",
        "--browser-arg=--no-sandbox",
        "--browser-arg=--disable-dev-shm-usage",
        source["sourceUrl"],
        str(output_path),
    ]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CaptureError(f"{command_preview(command)} is not installed: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CaptureError(f"{command_preview(command)} timed out after {timeout_s}s") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        message = detail[-1][:300] if detail else f"exit code {result.returncode}"
        raise CaptureError(f"{command_preview(command)} failed: {message}")
    if not output_path.is_file() or output_path.stat().st_size < 512:
        raise CaptureError(f"{command_preview(command)} produced no usable HTML file")


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", binascii.crc32(chunk_type + payload) & 0xFFFFFFFF)
    )


def add_png_metadata(path: Path, metadata: dict[str, str]) -> None:
    """Add PNG ``tEXt`` entries without requiring an image library."""

    signature = b"\x89PNG\r\n\x1a\n"
    raw = path.read_bytes()
    if not raw.startswith(signature):
        raise CaptureError(f"Chromium did not produce a PNG: {path}")

    chunks: list[tuple[bytes, bytes]] = []
    offset = len(signature)
    while offset < len(raw):
        if offset + 12 > len(raw):
            raise CaptureError(f"truncated PNG: {path}")
        length = struct.unpack(">I", raw[offset : offset + 4])[0]
        end = offset + 12 + length
        if end > len(raw):
            raise CaptureError(f"truncated PNG chunk: {path}")
        chunk_type = raw[offset + 4 : offset + 8]
        payload = raw[offset + 8 : offset + 8 + length]
        if chunk_type != b"tEXt":
            chunks.append((chunk_type, payload))
        offset = end
        if chunk_type == b"IEND":
            break
    if not chunks or chunks[-1][0] != b"IEND":
        raise CaptureError(f"PNG has no IEND chunk: {path}")

    text_chunks = [
        (b"tEXt", f"{key}\0{value}".encode("latin-1", errors="replace"))
        for key, value in metadata.items()
    ]
    output = bytearray(signature)
    for index, (chunk_type, payload) in enumerate(chunks):
        output.extend(_png_chunk(chunk_type, payload))
        if index == 0 and chunk_type == b"IHDR":
            for text_type, text_payload in text_chunks:
                output.extend(_png_chunk(text_type, text_payload))
    path.write_bytes(output)


def capture_screenshot(
    browser: Any,
    source: dict[str, Any],
    output_path: Path,
    capture_date: str,
    width: int,
    height: int,
    wait_ms: int,
    timeout_ms: int,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
    try:
        response = page.goto(source["sourceUrl"], wait_until="domcontentloaded", timeout=timeout_ms)
        if response is None:
            raise CaptureError("Chromium returned no document response")
        status = response.status
        if status < 200 or status >= 400:
            raise CaptureError(f"HTTP status {status}")
        page.wait_for_timeout(wait_ms)
        page.screenshot(path=str(output_path), full_page=False)
        add_png_metadata(
            output_path,
            {
                "Source URL": source["sourceUrl"],
                "Capture date": capture_date,
                "Viewport": f"{width}x{height}",
                "Rights status": "crop_first",
                "Publication ID": str(source["publicationId"]),
            },
        )
        return {
            "httpStatus": status,
            "finalUrl": page.url,
            "pageTitle": page.title(),
        }
    except Exception as exc:
        if isinstance(exc, CaptureError):
            raise
        raise CaptureError(f"Chromium screenshot failed: {exc}") from exc
    finally:
        page.close()


def failure_record(
    source: dict[str, Any],
    capture_date: str,
    stages: list[dict[str, str]],
    single_file_path: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "publicationId": source["publicationId"],
        "publication": source["publication"],
        "sourceUrl": source["sourceUrl"],
        "captureDate": capture_date,
        "stages": stages,
    }
    if single_file_path:
        result["singleFilePath"] = single_file_path
    return result


def write_output(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    CURRENT_HOMEpages_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_CURRENT_HOMEpages_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_HOMEpages_PATH.write_text(text, encoding="utf-8")
    DOCS_CURRENT_HOMEpages_PATH.write_text(text, encoding="utf-8")


def build_output(
    sources: list[dict[str, Any]],
    captures: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    capture_date: str,
    width: int,
    height: int,
) -> dict[str, Any]:
    return {
        "metadata": {
            "updated": capture_date,
            "attemptedCount": len(sources),
            "captureCount": len(captures),
            "failureCount": len(failures),
            "viewport": {"width": width, "height": height},
            "concurrency": 1,
            "tool": "SingleFile CLI and Chromium",
            "rights": {
                "status": "crop_first",
                "cropPlan": "Crop a representative masthead or story area before public reuse.",
            },
        },
        "homepages": captures,
        "failures": failures,
    }


def capture_all(args: argparse.Namespace) -> dict[str, Any]:
    try:
        capture_date = dt.date.fromisoformat(args.capture_date).isoformat()
    except ValueError as exc:
        raise CaptureError(f"invalid capture date: {args.capture_date!r}") from exc
    if args.width < 1 or args.height < 1 or args.wait_ms < 0 or args.timeout_ms < 1:
        raise CaptureError("viewport and timeout values must be positive")
    source_payload = load_json(args.sources)
    publications_payload = load_json(args.publications)
    sources = validate_sources(source_payload, publications_payload)

    LIVE_SITES_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_SITES_DIR.mkdir(parents=True, exist_ok=True)
    captures: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CaptureError("Python Playwright is required for Chromium screenshots") from exc

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=args.chromium,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
            )
        except Exception as exc:
            raise CaptureError(f"could not launch Chromium: {exc}") from exc
        try:
            for source in sources:
                stem = artifact_stem(source)
                html_path = LIVE_SITES_DIR / f"{stem}.html"
                screenshot_path = CURRENT_SITES_DIR / f"{stem}.png"
                stages: list[dict[str, str]] = []
                # Remove this source's previous outputs before retrying it.
                # A failed retry must not leave an older capture published.
                for stale_path in (html_path, screenshot_path):
                    if stale_path.is_file():
                        stale_path.unlink()
                print(f"capture {source['publicationId']}: {source['sourceUrl']}", flush=True)

                # Probe and save the viewport first. Rights-restricted source
                # captures stay outside the public docs directory.
                browser_result: dict[str, Any] | None = None
                try:
                    browser_result = capture_screenshot(
                        browser,
                        source,
                        screenshot_path,
                        capture_date,
                        args.width,
                        args.height,
                        args.wait_ms,
                        args.timeout_ms,
                    )
                except CaptureError as exc:
                    stages.append({"stage": "screenshot", "error": str(exc)})

                single_file_ok = False
                if browser_result is not None:
                    try:
                        run_single_file(
                            source,
                            html_path,
                            args.single_file,
                            args.chromium,
                            args.width,
                            args.height,
                            args.wait_ms,
                            args.single_file_timeout,
                        )
                        single_file_ok = True
                    except CaptureError as exc:
                        stages.append({"stage": "single-file", "error": str(exc)})

                if browser_result is not None:
                    capture: dict[str, Any] = {
                        "publicationId": source["publicationId"],
                        "publication": source["publication"],
                        "sourceUrl": source["sourceUrl"],
                        "captureDate": capture_date,
                        "status": "captured",
                        "httpStatus": browser_result["httpStatus"],
                        "finalUrl": browser_result["finalUrl"],
                        "pageTitle": browser_result["pageTitle"],
                        "screenshotPath": f"data/research/current-sites/{stem}.png",
                        "viewport": {"width": args.width, "height": args.height},
                        "rights": {
                            "status": "crop_first",
                            "cropPlan": "Crop a representative masthead or story area before public reuse.",
                        },
                        "singleFileCaptured": single_file_ok,
                        "singleFilePath": (
                            f"data/research/live-sites/{stem}.html" if single_file_ok else None
                        ),
                    }
                    captures.append(capture)

                if stages:
                    failures.append(
                        failure_record(
                            source,
                            capture_date,
                            stages,
                            f"data/research/live-sites/{stem}.html"
                            if html_path.is_file()
                            else None,
                        )
                    )
                    print(
                        f"  failed: {', '.join(stage['stage'] for stage in stages)}",
                        file=sys.stderr,
                        flush=True,
                    )
                else:
                    print("  captured", flush=True)
        finally:
            browser.close()

    payload = build_output(sources, captures, failures, capture_date, args.width, args.height)
    write_output(payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = capture_all(args)
    except CaptureError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        f"captured {payload['metadata']['captureCount']}/{payload['metadata']['attemptedCount']} "
        f"homepages; failures={payload['metadata']['failureCount']}",
        flush=True,
    )
    return 0 if not payload["failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
