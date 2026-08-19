"""Audit clean-capture coverage for the NJ Black Press source catalog.

Reads data/research/source-catalog.json (never writes it) and checks each
keeper against the clean files produced by the capture agents. Writes
data/research/clean-coverage.json and prints a summary.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "data" / "research"
MIN_BYTES = 20 * 1024


def load(path: Path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def good(path: Path | None) -> Path | None:
    """Return the path if the file exists and is larger than 20 KB."""
    if path is None:
        return None
    if path.is_file() and path.stat().st_size > MIN_BYTES:
        return path
    return None


def first_good(paths) -> Path | None:
    for p in paths:
        hit = good(p)
        if hit:
            return hit
    return None


# ---------------------------------------------------------------- clean indexes

def wayback_index():
    """pub_id + url -> clean png."""
    log = load(RES / "wayback" / "clean-capture-log.json") or {}
    by_url, by_pub = {}, {}
    for cap in log.get("captures", []):
        if not cap.get("ok"):
            continue
        f = good(ROOT / cap["file"])
        if not f:
            continue
        for key in (cap.get("url"), cap.get("original_url")):
            if key:
                by_url[key] = f
        by_pub.setdefault(cap.get("pub_id"), f)
    # fall back to any file in the clean dir, keyed by id prefix
    for f in (RES / "wayback" / "clean").glob("*.png"):
        m = re.match(r"^(\d+)-", f.name)
        if m and good(f):
            by_pub.setdefault(int(m.group(1)), f)
    return by_url, by_pub


def ia_index():
    """archive.org identifier -> clean pdf."""
    log = None
    for cand in (RES / "ia" / "clean" / "ia-download-log.json",
                 RES / "wayback" / "ia-download-log.json"):
        log = log or load(cand)
    idx = {}
    for dl in (log or {}).get("downloads", []):
        f = good(ROOT / dl["file"]) if dl.get("file") else None
        if f and dl.get("identifier"):
            idx[dl["identifier"]] = f
    for f in (RES / "ia" / "clean").glob("*.pdf"):
        if good(f):
            idx.setdefault(f.stem, f)
    return idx


def npcom_index():
    """newspapers.com image id -> clean jpg/pdf; also slug -> file."""
    dl_dir = RES / "newspapers-com" / "downloads"
    log = load(dl_dir / "clean-download-log.json") or {}
    by_image, by_slug = {}, {}
    for slug, rec in log.items():
        if not isinstance(rec, dict):
            continue
        files = []
        for kind in ("jpg", "pdf"):
            part = rec.get(kind) or {}
            if part.get("file"):
                files.append(Path(part["file"]))
        files += [dl_dir / f"{slug}.jpg", dl_dir / f"{slug}.pdf"]
        hit = first_good(files)
        if not hit:
            continue
        by_slug[slug] = hit
        img = rec.get("image_id")
        if not img:
            m = re.search(r"/image/(\d+)", rec.get("url") or "")
            img = m.group(1) if m else None
        if img:
            by_image[str(img)] = hit
    # sweep the directory too, in case another agent added files after the log
    for f in list(dl_dir.glob("*.jpg")) + list(dl_dir.glob("*.pdf")):
        if good(f):
            by_slug.setdefault(f.stem, f)
    return by_image, by_slug


WB_URL, WB_PUB = wayback_index()
IA = ia_index()
NP_IMAGE, NP_SLUG = npcom_index()


# ---------------------------------------------------------------- classification

def clean_file_for(pub, keeper):
    """Return (Path|None, need) for one keeper."""
    kind = keeper.get("kind")
    url = keeper.get("url") or ""
    local = keeper.get("localFile") or ""

    # Danky book-page scans and other locally stored source scans count as clean.
    if local.startswith("data/research/danky/"):
        hit = good(ROOT / local)
        return hit, None if hit else "danky scan missing on disk"

    if kind in ("wayback_snapshot", "website_screenshot"):
        hit = WB_URL.get(url) or WB_PUB.get(pub["id"])
        return hit, None if hit else "needs clean wayback/live capture"

    if kind in ("full_issue", "full_issue_preview"):
        ident = keeper.get("identifier")
        if not ident:
            m = re.search(r"archive\.org/(?:details|embed)/([^/?#]+)", url)
            ident = m.group(1) if m else None
        hit = IA.get(ident) if ident else None
        return hit, None if hit else "needs IA full-issue PDF download"

    if kind in ("clip", "clipping"):
        m = re.search(r"/image/(\d+)", url)
        hit = NP_IMAGE.get(m.group(1)) if m else None
        if not hit and local:
            hit = NP_SLUG.get(Path(local).stem)
        return hit, None if hit else "needs newspapers.com full-page re-export"

    if kind in ("catalog_record", "library_page"):
        hit = good(ROOT / local) if local else None
        if hit:
            return hit, None
        return None, "keeper is text-only catalog record with no danky scan"

    hit = good(ROOT / local) if local else None
    return hit, None if hit else f"unhandled keeper kind {kind}"


def main():
    catalog = load(RES / "source-catalog.json")
    pubs = catalog["publications"]
    rows, gaps = [], []

    for pub in pubs:
        keepers = pub.get("keepers") or []
        clean, sloppy, needs = 0, 0, []
        details = []
        for k in keepers:
            hit, need = clean_file_for(pub, k)
            if hit:
                clean += 1
            else:
                sloppy += 1
                needs.append(need)
            details.append({
                "kind": k.get("kind"),
                "url": k.get("url"),
                "legacyFile": k.get("localFile"),
                "cleanFile": rel(hit) if hit else None,
                "need": need,
            })

        if not keepers:
            status = "none"
        elif sloppy == 0:
            status = "clean"
        elif clean == 0:
            status = "none"
        else:
            status = "partial"

        rows.append({
            "id": pub["id"],
            "name": pub["name"],
            "yearFounded": pub.get("yearFounded"),
            "keeperCount": len(keepers),
            "cleanCount": clean,
            "sloppyOnlyCount": sloppy,
            "status": status,
            "keepers": details,
        })

        if clean == 0:
            gaps.append({
                "id": pub["id"],
                "name": pub["name"],
                "yearFounded": pub.get("yearFounded"),
                "keeperCount": len(keepers),
                "needs": sorted(set(needs)) or ["no keepers in catalog at all"],
            })

    def year(rec):
        y = rec.get("yearFounded")
        try:
            return int(re.search(r"\d{4}", str(y)).group())
        except (AttributeError, TypeError, ValueError):
            return 9999

    rows.sort(key=lambda r: (year(r), r["id"]))
    gaps.sort(key=lambda r: (year(r), r["id"]))

    counts = {s: sum(1 for r in rows if r["status"] == s)
              for s in ("clean", "partial", "none")}
    out = {
        "generated": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "publications": len(rows),
            "fullyClean": counts["clean"],
            "partial": counts["partial"],
            "noCleanCapture": counts["none"],
            "keeperTotal": sum(r["keeperCount"] for r in rows),
            "keeperClean": sum(r["cleanCount"] for r in rows),
            "keeperSloppyOnly": sum(r["sloppyOnlyCount"] for r in rows),
            "cleanFilesOnDisk": {
                "wayback": len(set(map(str, WB_PUB.values()))),
                "iaPdfs": len(set(map(str, IA.values()))),
                "newspapersCom": len(set(map(str, NP_SLUG.values()))),
            },
        },
        "gaps": gaps,
        "publications": rows,
    }
    dest = RES / "clean-coverage.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    s = out["summary"]
    print(f"wrote {rel(dest)}")
    print(f"138-pub audit: clean={s['fullyClean']} partial={s['partial']} none={s['noCleanCapture']}")
    print(f"keepers: {s['keeperClean']}/{s['keeperTotal']} clean, {s['keeperSloppyOnly']} sloppy-only")
    print(f"clean files on disk: {s['cleanFilesOnDisk']}")
    print("\ngaps, oldest first:")
    for g in gaps:
        print(f"  {g['yearFounded']}  #{g['id']:>3} {g['name'][:46]:<46} {'; '.join(g['needs'])}")


if __name__ == "__main__":
    main()
