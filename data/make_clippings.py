"""
Produce web-ready evidence images from archival captures per the rights manifest.

Mechanical driver script. Crop boxes for crop_first / publishable newspapers.com
files were decided interactively (Read image -> decide box -> crop -> Read to
verify) and are hardcoded below in NEWSPAPERS_COM_CROPS.

Usage: python make_clippings.py
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image

# Source PDFs/images are trusted local archival files, not untrusted uploads;
# disable the decompression-bomb guard so oversized page renders don't fail.
Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESEARCH = DATA / "research"
EVIDENCE_DIR = ROOT / "docs" / "images" / "evidence"
MANIFEST_PATH = RESEARCH / "rights" / "rights-manifest.json"
SOURCE_CATALOG_PATH = RESEARCH / "source-catalog.json"
CLIPPINGS_OUT = ROOT / "docs" / "data" / "clippings.json"

MAX_WIDTH_DEFAULT = 1600
JPEG_QUALITY = 85

LOG_LINES = []


def log(msg):
    print(msg)
    LOG_LINES.append(msg)


# ---------------------------------------------------------------------------
# Crop boxes decided interactively for newspapers.com files (crop_first and
# publishable). Box = (left, top, right, bottom) in full-resolution pixels.
# ---------------------------------------------------------------------------
NEWSPAPERS_COM_CROPS = {
    # crop_first
    "afro-american_1932-07-09_p7_newark-herald-folded.jpg": (2340, 2455, 2700, 2945),
    "asbury-park-press_1949-11-06_p2_johnson-montclair-newark.jpg": (425, 91, 1010, 1247),
    "asbury-park-press_1960-05-20_p21_bronze-thrills-july.jpg": (27, 1990, 735, 2280),
    "courier-news_1991-06-24_p8_webber-after-hours.jpg": (580, 3637, 2210, 4180),
    "courier-post_1932-03-22_p14_ironsides-echo-award.jpg": (1656, 1357, 2000, 1900),
    "courier-post_1936-01-06_p3_camp-cooper-paper.jpg": (1099, 2538, 1800, 3228),
    "daily-record-morristown_2023-05-21_pD2_nj-afro-american-described.jpg": (645, 2062, 1720, 2753),
    "ridgewood-news_1987-11-26_p14_landscape-ap-smith.jpg": (41, 150, 2739, 1629),
    "star-ledger_1949-01-19_p14_melvin-johnson-left-papers.jpg": (1980, 2692, 2640, 3088),
    "sunday-news-ridgewood_1993-06-27_p2_smallest-newspaper.jpg": (42, 170, 2838, 1433),
    "the-news-paterson_1939-09-09_p9_nj-guardian-cited.jpg": (1637, 1743, 1970, 2662),
    "the-record-hackensack_1991-02-09_p2_landscape-renamed.jpg": (36, 122, 821, 1226),
    "trenton-times_1940-05-07_p13_ironsides-echo-awards.jpg": (1350, 2735, 1680, 3200),
    "trenton-times_1976-04-23_p8_utimme-umana.jpg": (836, 152, 1647, 760),
    "trenton-times_1993-09-27_p32_utimme-umana.jpg": (24, 2123, 537, 2797),
    # publishable (still cropped to the referenced story per instructions)
    "asbury-park-press_1893-07-22_p1_murrell-speaking.jpg": (37, 558, 583, 1540),
    "asbury-park-press_1909-03-05_p2_echo-moves-red-bank.jpg": (480, 3150, 870, 3520),
    "evening-world_1888-12-11_p2_trumpet-negro-organ.jpg": (1615, 2570, 2020, 2900),
    "monmouth-democrat_1904-09-08_p4_echo-burned-out.jpg": (551, 3414, 1138, 3699),
    "new-york-age_1909-10-21_p1_herbert-obituary.jpg": (1441, 367, 1978, 1328),
    "new-york-age_1921-04-09_p4_red-bank-echo-cited.jpg": (2140, 940, 2572, 1300),
    "new-york-tribune_1895-12-08_p14_herbert-profile.jpg": (1854, 171, 2352, 2804),
    "shore-press_1893-07-28_p6_murrell-asbury-meeting.jpg": (24, 122, 527, 1055),
    "trenton-sunday-advertiser_1893-11-05_p1_herbert-vs-bradley.jpg": (2260, 1950, 2803, 3414),
    "trenton-sunday-advertiser_1895-10-20_p1_herbert-gop-committee.jpg": (1281, 295, 1750, 1126),
    "washington-bee_1889-05-18_p2_murrell-trumpet-editor.jpg": (1197, 1873, 1769, 2290),
}

# ---------------------------------------------------------------------------
# Explicit exclusions -- director rulings. Keyed by source filename (basename).
# A re-run must never reintroduce these even if they still appear in the
# rights manifest.
#
# Ruling 1: Right On! (Hollywood, CA issues) -- excluded. Right On! moved to
# Cresskill, NJ in 1983; the 1971 and 1977 issues predate the NJ move and were
# never keepers.
# Ruling 2: NJ-only policy -- six newspapers.com clippings are out-of-state
# publications with no NJ publicationIds and must not be published as evidence.
# ---------------------------------------------------------------------------
EXCLUDED = {
    # Ruling 1: Right On! pre-1983 Hollywood, CA issues
    "95-right-on-1971-v3n1.pdf",
    "95-right-on-1977-v6n4.pdf",
    # Ruling 2: NJ-only policy -- out-of-state clippings
    "afro-american_1932-07-09_p7_newark-herald-folded.jpg",
    "evening-world_1888-12-11_p2_trumpet-negro-organ.jpg",
    "new-york-age_1909-10-21_p1_herbert-obituary.jpg",
    "new-york-age_1921-04-09_p4_red-bank-echo-cited.jpg",
    "new-york-tribune_1895-12-08_p14_herbert-profile.jpg",
    "washington-bee_1889-05-18_p2_murrell-trumpet-editor.jpg",
}

# depth-hunt crop_first covers: crop boxes decided interactively, max width 1200.
# The three cover/thumb images (112, 121, 135) are already tight covers -- no
# crop needed, just resize/reformat. Left empty intentionally: DEPTH_HUNT_CROPS.get()
# returning None means "use the full image".
DEPTH_HUNT_CROPS = {}

# wayback crop_first: masthead/section crop boxes decided interactively
# (Read image -> decide box -> crop -> Read to verify). Box = (left, top,
# right, bottom) in full-resolution pixels.
WAYBACK_CROPS = {
    "006-front-runner-new-jersey-20180729184443.png": (0, 0, 2880, 700),
    "012-five-wards-media-20250613131129.png": (0, 0, 2880, 700),
    "019-nj-in-color-20220622225425.png": (0, 0, 2914, 1300),
    "020-new-jersey-urban-news-20230307222958.png": (0, 190, 2880, 555),
    "022-ark-republic-20170708221608.png": (0, 0, 2880, 300),
    "023-the-newark-times-20141018093931.png": (0, 0, 2880, 160),
    "025-atlantic-city-focus-20240506145430.png": (0, 300, 2880, 530),
    "029-faithfully-magazine-20151025031224.png": (0, 0, 2880, 240),
    "032-trenton365-stream-with-jacque-howard-20211208013612.png": (0, 0, 2880, 180),
    "033-the-black-observer-20210120065101.png": (0, 0, 2880, 370),
    "071-the-missionary-magazine-20040207205909.png": (0, 100, 2880, 520),
    "084-unity-and-struggle-20200118211629.png": (0, 0, 2880, 530),
    "128-newark-black-newspapers-collection-digital-colle-20190419185835.png": (0, 0, 2880, 270),
}


def ensure_dirs():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    CLIPPINGS_OUT.parent.mkdir(parents=True, exist_ok=True)


def load_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_caption_lookup():
    """localFile path -> list of (pubId, pubName, caption) from source-catalog keepers."""
    lookup = {}
    if not SOURCE_CATALOG_PATH.exists():
        return lookup
    with open(SOURCE_CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)
    for pub in catalog.get("publications", []):
        for k in pub.get("keepers", []):
            lf = k.get("localFile")
            if lf:
                lookup.setdefault(lf.replace("\\", "/"), []).append(
                    (pub["id"], pub["name"], k.get("caption") or k.get("title"))
                )
    return lookup


def save_resized(im, out_path, max_width=MAX_WIDTH_DEFAULT, fmt="JPEG", quality=JPEG_QUALITY):
    w, h = im.size
    if w > max_width:
        scale = max_width / w
        im = im.resize((max_width, int(h * scale)), Image.LANCZOS)
    if fmt == "JPEG" and im.mode in ("RGBA", "P"):
        im = im.convert("RGB")
    im.save(out_path, fmt, quality=quality) if fmt == "JPEG" else im.save(out_path, fmt)
    return im.size


def process_newspapers_com(manifest, caption_lookup, results):
    files = [f for f in manifest["files"] if f["source"] == "newspapers.com"]
    seen_stems = set()
    for entry in files:
        path = entry["path"]
        p = Path(path)
        if p.suffix.lower() != ".jpg":
            continue  # skip duplicate .pdf manifest entries
        basename = p.name
        stem = p.stem
        if stem in seen_stems:
            continue
        seen_stems.add(stem)

        if basename in EXCLUDED:
            log(f"SKIP excluded (director ruling): {basename}")
            continue

        status = entry["status"]
        src_full = ROOT / path

        if status == "metadata_only":
            log(f"SKIP metadata_only: {basename}")
            continue

        if not src_full.exists():
            log(f"FAIL missing source file: {basename}")
            continue

        box = NEWSPAPERS_COM_CROPS.get(basename)
        if not box:
            log(f"FAIL no crop box decided: {basename}")
            continue

        try:
            im = Image.open(src_full)
            crop = im.crop(box)
            out_path = EVIDENCE_DIR / f"{stem}.jpg"
            w, h = save_resized(crop, out_path, max_width=1600)
            log(f"OK {status}: {basename} -> {out_path.name} ({w}x{h})")
        except Exception as e:
            log(f"FAIL {basename}: {e}")
            continue

        caps = caption_lookup.get(path, [])
        pub_ids = entry.get("publicationIds") or [c[0] for c in caps]
        caption = caps[0][2] if caps else entry.get("cropPlan") or entry.get("citation", "")

        results.append({
            "sourcePath": path,
            "webPath": f"images/evidence/{out_path.name}",
            "publicationIds": pub_ids,
            "status": status,
            "citation": entry.get("citation", ""),
            "caption": caption,
            "width": w,
            "height": h,
        })


def process_ia_pdfs(manifest, caption_lookup, results):
    files = [f for f in manifest["files"] if f["source"] == "ia"]
    try:
        import fitz  # PyMuPDF
    except ImportError:
        log("FAIL: PyMuPDF (fitz) not installed; cannot render ia PDFs")
        return

    for entry in files:
        path = entry["path"]
        status = entry["status"]
        if Path(path).name in EXCLUDED:
            log(f"SKIP excluded (director ruling): {Path(path).name}")
            continue
        if Path(path).suffix.lower() != ".pdf":
            log(f"SKIP non-pdf ia manifest entry: {path}")
            continue
        src_full = ROOT / path
        if not src_full.exists():
            log(f"FAIL missing source file: {path}")
            continue
        stem = Path(path).stem
        try:
            doc = fitz.open(src_full)
            page = doc[0]
            # render at 150 dpi
            zoom = 150 / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            out_path = EVIDENCE_DIR / f"{stem}.jpg"
            img_bytes = pix.tobytes("png")
            import io
            im = Image.open(io.BytesIO(img_bytes))
            w, h = save_resized(im, out_path, max_width=1600)
            doc.close()
            log(f"OK {status}: {path} -> {out_path.name} ({w}x{h})")
        except Exception as e:
            log(f"FAIL {path}: {e}")
            continue

        caps = caption_lookup.get(path, [])
        pub_ids = entry.get("publicationIds") or [c[0] for c in caps]
        caption = caps[0][2] if caps else entry.get("citation", "")
        results.append({
            "sourcePath": path,
            "webPath": f"images/evidence/{out_path.name}",
            "publicationIds": pub_ids,
            "status": status,
            "citation": entry.get("citation", ""),
            "caption": caption,
            "width": w,
            "height": h,
        })


def process_wayback(manifest, caption_lookup, results):
    files = [f for f in manifest["files"] if f["source"] == "wayback"]
    for entry in files:
        path = entry["path"]
        status = entry["status"]
        basename = Path(path).name
        if basename in EXCLUDED:
            log(f"SKIP excluded (director ruling): {basename}")
            continue
        src_full = ROOT / path
        if not src_full.exists():
            log(f"FAIL missing source file: {path}")
            continue
        stem = Path(path).stem
        try:
            im = Image.open(src_full)
            box = WAYBACK_CROPS.get(basename)
            if box:
                im = im.crop(box)
            has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            if has_alpha:
                out_path = EVIDENCE_DIR / f"{stem}.png"
                w, h = save_resized(im, out_path, max_width=1600, fmt="PNG")
            else:
                out_path = EVIDENCE_DIR / f"{stem}.jpg"
                w, h = save_resized(im, out_path, max_width=1600, fmt="JPEG")
            log(f"OK {status}: {path} -> {out_path.name} ({w}x{h})")
        except Exception as e:
            log(f"FAIL {path}: {e}")
            continue

        caps = caption_lookup.get(path, [])
        pub_ids = entry.get("publicationIds") or [c[0] for c in caps]
        caption = caps[0][2] if caps else entry.get("cropPlan") or entry.get("citation", "")
        results.append({
            "sourcePath": path,
            "webPath": f"images/evidence/{out_path.name}",
            "publicationIds": pub_ids,
            "status": status,
            "citation": entry.get("citation", ""),
            "caption": caption,
            "width": w,
            "height": h,
        })


def process_depth_hunt(manifest, caption_lookup, results):
    files = [f for f in manifest["files"] if f["source"] == "depth-hunt"]
    for entry in files:
        path = entry["path"]
        status = entry["status"]
        basename = Path(path).name
        if basename in EXCLUDED:
            log(f"SKIP excluded (director ruling): {basename}")
            continue
        if status == "metadata_only":
            log(f"SKIP metadata_only: {path}")
            continue
        src_full = ROOT / path
        if not src_full.exists():
            log(f"FAIL missing source file: {path}")
            continue
        stem = Path(path).stem
        suffix = Path(path).suffix.lower()
        try:
            if suffix == ".pdf":
                # Render page 1 at 150dpi (same approach as ia PDFs), representing
                # the issue per cropPlan ("crop a representative page/article").
                import fitz  # PyMuPDF
                import io
                doc = fitz.open(src_full)
                page = doc[0]
                zoom = 150 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                im = Image.open(io.BytesIO(pix.tobytes("png")))
                doc.close()
            else:
                im = Image.open(src_full)
            box = DEPTH_HUNT_CROPS.get(basename)
            if box:
                im = im.crop(box)
            out_path = EVIDENCE_DIR / f"{stem}.jpg"
            w, h = save_resized(im, out_path, max_width=1200)
            log(f"OK {status}: {path} -> {out_path.name} ({w}x{h})")
        except Exception as e:
            log(f"FAIL {path}: {e}")
            continue

        caps = caption_lookup.get(path, [])
        pub_ids = entry.get("publicationIds") or [c[0] for c in caps]
        caption = caps[0][2] if caps else entry.get("cropPlan") or entry.get("citation", "")
        results.append({
            "sourcePath": path,
            "webPath": f"images/evidence/{out_path.name}",
            "publicationIds": pub_ids,
            "status": status,
            "citation": entry.get("citation", ""),
            "caption": caption,
            "width": w,
            "height": h,
        })


def process_loc(manifest, caption_lookup, results):
    files = [f for f in manifest["files"] if f["source"] == "loc"]
    for entry in files:
        path = entry["path"]
        status = entry["status"]
        if Path(path).name in EXCLUDED:
            log(f"SKIP excluded (director ruling): {Path(path).name}")
            continue
        src_full = ROOT / path
        if not src_full.exists():
            log(f"FAIL missing source file: {path}")
            continue
        stem = Path(path).stem
        try:
            im = Image.open(src_full)
            out_path = EVIDENCE_DIR / f"{stem}.jpg"
            w, h = save_resized(im, out_path, max_width=1600)
            log(f"OK {status}: {path} -> {out_path.name} ({w}x{h})")
        except Exception as e:
            log(f"FAIL {path}: {e}")
            continue

        caps = caption_lookup.get(path, [])
        pub_ids = entry.get("publicationIds") or [c[0] for c in caps]
        caption = caps[0][2] if caps else entry.get("citation", "")
        results.append({
            "sourcePath": path,
            "webPath": f"images/evidence/{out_path.name}",
            "publicationIds": pub_ids,
            "status": status,
            "citation": entry.get("citation", ""),
            "caption": caption,
            "width": w,
            "height": h,
        })


def main():
    ensure_dirs()
    manifest = load_manifest()
    caption_lookup = build_caption_lookup()
    results = []

    process_newspapers_com(manifest, caption_lookup, results)
    process_ia_pdfs(manifest, caption_lookup, results)
    process_wayback(manifest, caption_lookup, results)
    process_depth_hunt(manifest, caption_lookup, results)
    process_loc(manifest, caption_lookup, results)

    out = {
        "clippings": results,
        "metadata": {
            "totalCount": len(results),
            "generated": "2026-08-19",
        },
    }
    with open(CLIPPINGS_OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    log(f"\nTotal clippings produced: {len(results)}")
    log(f"clippings.json written to: {CLIPPINGS_OUT}")


if __name__ == "__main__":
    main()
