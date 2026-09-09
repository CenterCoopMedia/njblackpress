"""
Build the small wall copies the history hall hangs in its frames.

The only input is `docs/data/clippings.json` and the already public, already
cropped files it points at under `docs/`. This builder makes no rights decision
and never crops: a clipping that is not published there is not published here.
The research corpus is never read and never named in the output.

Outputs:
  docs/images/evidence/wall/<stem>.jpg   400 px wide, long edge capped
  docs/data/wall-copies.json             the application's derivative lookup

Usage:
  python3 data/make_wall_copies.py
  python3 data/make_wall_copies.py --check   report what would change, write nothing
"""

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CLIPPINGS_PATH = DOCS / "data" / "clippings.json"
EVIDENCE_DIR = DOCS / "images" / "evidence"
WALL_DIR = EVIDENCE_DIR / "wall"
MANIFEST_PATH = DOCS / "data" / "wall-copies.json"

# Rights decisions come from the clipping index. These three are published on
# the site today; the first two are not, and must never reach a wall.
ELIGIBLE_STATUSES = ("publishable", "publishable_with_credit", "crop_first")
INELIGIBLE_STATUSES = ("metadata_only", "unlisted")

# Encoder settings are part of the contract: the same source bytes and the same
# settings must produce the same output bytes, so a rebuild rewrites nothing.
ENCODER = {
    "format": "JPEG",
    "targetWidth": 400,
    "maxLongEdge": 1200,
    "quality": 78,
    "subsampling": "4:2:0",
    "progressive": False,
    "optimize": True,
    "colorMode": "RGB",
    "orientation": "exif-normalised",
    "metadata": "stripped",
}

SUBSAMPLING_CODE = 2  # Pillow's code for 4:2:0.


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load_clippings():
    with open(CLIPPINGS_PATH, encoding="utf-8") as handle:
        document = json.load(handle)
    return document.get("clippings", document)


def stem_for(web_path):
    return Path(web_path).name.rsplit(".", 1)[0]


def public_source(web_path, errors, stem):
    """Resolve a webPath under docs/ and refuse anything outside the evidence dir."""
    candidate = (DOCS / web_path).resolve()
    try:
        candidate.relative_to(EVIDENCE_DIR.resolve())
    except ValueError:
        errors.append(f"{stem}: source path leaves docs/images/evidence: {web_path}")
        return None
    if candidate.parent.resolve() == WALL_DIR.resolve():
        errors.append(f"{stem}: source path is itself a wall copy: {web_path}")
        return None
    if not candidate.is_file():
        errors.append(f"{stem}: missing public source file {web_path}")
        return None
    return candidate


def scaled_size(width, height):
    """400 px wide, never upscaled, and never longer than the long-edge cap."""
    scale = min(
        1.0,
        ENCODER["targetWidth"] / width,
        ENCODER["maxLongEdge"] / max(width, height),
    )
    return max(1, round(width * scale)), max(1, round(height * scale))


def encode(source_path):
    """Return (jpeg bytes, source size, output size). No timestamps, no profiles."""
    with Image.open(source_path) as opened:
        image = ImageOps.exif_transpose(opened)
        source_size = (image.width, image.height)
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            flat = Image.new("RGB", image.size, (255, 255, 255))
            flat.paste(image, mask=image.split()[-1])
            image = flat
        elif image.mode != "RGB":
            image = image.convert("RGB")
        target = scaled_size(*source_size)
        if target != source_size:
            image = image.resize(target, Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=ENCODER["quality"],
            optimize=ENCODER["optimize"],
            progressive=ENCODER["progressive"],
            subsampling=SUBSAMPLING_CODE,
        )
        return buffer.getvalue(), source_size, target


def build(check_only=False):
    errors = []
    clippings = load_clippings()

    planned = {}
    for clipping in clippings:
        web_path = clipping.get("webPath") or ""
        status = clipping.get("rightsStatus") or clipping.get("status")
        stem = stem_for(web_path)
        if not web_path or not stem:
            errors.append(f"clipping without a webPath: {clipping.get('citation', '(no citation)')}")
            continue
        if status in INELIGIBLE_STATUSES:
            continue
        if status not in ELIGIBLE_STATUSES:
            errors.append(f"{stem}: unknown rights status {status!r}")
            continue
        if stem in planned:
            errors.append(f"{stem}: two clippings share one output name ({planned[stem]['webPath']} and {web_path})")
            continue
        planned[stem] = clipping

    entries = []
    written = []
    unchanged = []
    for stem in sorted(planned):
        clipping = planned[stem]
        web_path = clipping["webPath"]
        source = public_source(web_path, errors, stem)
        if source is None:
            continue
        source_bytes = source.read_bytes()
        try:
            data, source_size, out_size = encode(source)
        except OSError as error:
            errors.append(f"{stem}: source image could not be read ({error})")
            continue

        out_path = WALL_DIR / f"{stem}.jpg"
        digest = sha256_bytes(data)
        current = out_path.read_bytes() if out_path.is_file() else None
        if current is None or sha256_bytes(current) != digest:
            written.append(out_path.name)
            if not check_only:
                WALL_DIR.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(data)
        else:
            unchanged.append(out_path.name)

        entries.append({
            "id": stem,
            "stem": stem,
            "sourcePath": web_path,
            "wallPath": f"images/evidence/wall/{stem}.jpg",
            "sourceSha256": sha256_bytes(source_bytes),
            "outputSha256": digest,
            "sourceWidth": source_size[0],
            "sourceHeight": source_size[1],
            "outputWidth": out_size[0],
            "outputHeight": out_size[1],
            "status": clipping.get("rightsStatus") or clipping.get("status"),
            "citation": clipping.get("citation", ""),
            "caption": clipping.get("caption", ""),
            "altText": clipping.get("altText") or clipping.get("alt") or clipping.get("caption", ""),
            "publicationIds": clipping.get("publicationIds", []),
        })

    if errors:
        for message in errors:
            print(f"ERROR {message}", file=sys.stderr)
        print(f"{len(errors)} problem(s); nothing was written.", file=sys.stderr)
        return 1

    # Obsolete outputs go only through the manifest, and only inside the wall
    # directory. A withdrawn rights decision removes the published file here; it
    # cannot retract a copy a visitor already downloaded.
    keep = {entry["wallPath"].rsplit("/", 1)[-1] for entry in entries}
    removed = []
    if WALL_DIR.is_dir():
        for existing in sorted(WALL_DIR.iterdir()):
            if existing.is_file() and existing.name not in keep:
                removed.append(existing.name)
                if not check_only:
                    existing.unlink()

    manifest = {
        "metadata": {
            "source": "docs/data/clippings.json",
            "builder": "data/make_wall_copies.py",
            "encoder": dict(ENCODER),
            "eligibleStatuses": list(ELIGIBLE_STATUSES),
            "totalCount": len(entries),
        },
        "wallCopies": entries,
    }
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    manifest_changed = (not MANIFEST_PATH.is_file()) or MANIFEST_PATH.read_text(encoding="utf-8") != text
    if manifest_changed and not check_only:
        MANIFEST_PATH.write_text(text, encoding="utf-8")

    print(f"{len(entries)} wall copies: {len(written)} written, {len(unchanged)} unchanged, {len(removed)} removed.")
    if removed:
        print("removed: " + ", ".join(removed))
    if check_only and (written or removed or manifest_changed):
        print("check: the wall copies are out of date.", file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report changes without writing")
    args = parser.parse_args()
    return build(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
