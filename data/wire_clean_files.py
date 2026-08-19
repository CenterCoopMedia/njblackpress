"""Repoint source-catalog keepers at clean full-resolution files and add depth-hunt finds.

Dry run (default): writes data/research/wiring-dryrun.json, changes nothing.
Apply: python wire_clean_files.py --apply  (backs up the catalog first)
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data" / "research"
CAT = RES / "source-catalog.json"
BACKUP = RES / "source-catalog.backup-2026-08-19.json"
DRYRUN = RES / "wiring-dryrun.json"
MIN_BYTES = 20 * 1024

RIGHT_ON_NOTE = (
    "Right On! 1971/1977 full issues found (data/research/depth-hunt/files/95-*.pdf) "
    "but excluded: Hollywood-era mastheads predate the 1983 move to Cresskill NJ."
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def repo_rel(p: str) -> str:
    """Normalise a log path to the repo-relative forward-slash form the catalog uses."""
    path = Path(p)
    if path.is_absolute():
        path = path.relative_to(ROOT)
    return path.as_posix()


def check_file(rel: str, problems: list[str], label: str) -> None:
    f = ROOT / rel
    if not f.exists():
        problems.append(f"{label}: missing {rel}")
    elif f.stat().st_size < MIN_BYTES:
        problems.append(f"{label}: too small ({f.stat().st_size} B) {rel}")


def build():
    cat = load(CAT)
    rows = {p["id"]: p for p in cat["publications"]}

    np_log = load(RES / "newspapers-com" / "downloads" / "clean-download-log.json")
    np_by_image = {v["image_id"]: repo_rel(v["jpg"]["file"]) for v in np_log.values()}

    wb_log = load(RES / "wayback" / "clean-capture-log.json")
    wb_by_old = {c["old_file"]: repo_rel(c["file"]) for c in wb_log["captures"] if c.get("ok")}
    wb_by_url = {c["url"]: repo_rel(c["file"]) for c in wb_log["captures"] if c.get("ok")}

    ia_log = load(RES / "ia" / "clean" / "ia-download-log.json")
    ia_by_id = {d["identifier"]: repo_rel(d["file"]) for d in ia_log["downloads"] if d.get("ok")}

    changes: list[dict] = []
    new_keepers: list[dict] = []
    notes: list[dict] = []
    unmatched: list[dict] = []
    problems: list[str] = []
    counts = {"newspapers_com": 0, "wayback": 0, "ia": 0, "danky_untouched": 0, "other_untouched": 0}

    for pid in sorted(rows):
        row = rows[pid]
        for idx, keeper in enumerate(row.get("keepers", [])):
            old = keeper.get("localFile") or ""
            url = keeper.get("url") or ""
            new = None
            bucket = None

            if "/danky/" in old:
                counts["danky_untouched"] += 1
                continue

            if "newspapers-com" in old:
                m = re.search(r"/image/(\d+)", url)
                new = np_by_image.get(m.group(1)) if m else None
                bucket = "newspapers_com"
            elif "/ia-issues/" in old:
                m = re.search(r"archive\.org/details/([^/?#]+)", url)
                new = ia_by_id.get(m.group(1)) if m else None
                bucket = "ia"
            elif old in wb_by_old or url in wb_by_url:
                new = wb_by_old.get(old) or wb_by_url.get(url)
                bucket = "wayback"
            else:
                counts["other_untouched"] += 1
                continue

            if not new:
                unmatched.append({"pubId": pid, "keeperIndex": idx, "bucket": bucket,
                                  "old": old, "url": url})
                continue
            if new == old:
                continue
            check_file(new, problems, f"{pid}[{idx}]")
            counts[bucket] += 1
            changes.append({"pubId": pid, "keeperIndex": idx, "field": "localFile",
                            "old": old, "new": new})

    findings = load(RES / "depth-hunt" / "findings.json")
    kind_for = {40: "full_issue", 68: "full_issue", 112: "cover_image",
                114: "auction_photo", 121: "cover_image", 135: "cover_image"}
    for find in findings["confirmed"]:
        pid = find["pubId"]
        if pid == 95:
            continue
        rel = repo_rel(find["localFile"])
        check_file(rel, problems, f"new keeper {pid}")
        new_keepers.append({
            "pubId": pid,
            "keeper": {
                "kind": kind_for.get(pid, "cover_image"),
                "title": f"{find['name']} — {find['caption']}",
                "url": find["url"],
                "localFile": rel,
                "source": find["source"],
                "date": find["date"],
                "caption": find["caption"],
            },
        })

    notes.append({"pubId": 95, "field": "sources.other.notes", "append": RIGHT_ON_NOTE})

    report = {
        "generated": "2026-08-19",
        "counts": {
            "repoints": len(changes),
            "byBucket": counts,
            "newKeepers": len(new_keepers),
            "notesAppended": len(notes),
            "unmatched": len(unmatched),
            "keeperTotalBefore": sum(len(r.get("keepers", [])) for r in rows.values()),
            "keeperTotalAfter": sum(len(r.get("keepers", [])) for r in rows.values()) + len(new_keepers),
        },
        "problems": problems,
        "changes": changes,
        "newKeepers": new_keepers,
        "notes": notes,
        "unmatched": unmatched,
    }
    return cat, rows, report


def apply(cat, rows, report):
    for ch in report["changes"]:
        rows[ch["pubId"]]["keepers"][ch["keeperIndex"]]["localFile"] = ch["new"]
    for nk in report["newKeepers"]:
        row = rows[nk["pubId"]]
        row["keepers"].append(nk["keeper"])
        row["status"] = "has_keeper"
    for note in report["notes"]:
        other = rows[note["pubId"]]["sources"]["other"]
        text = other.get("notes") or ""
        if note["append"] not in text:
            other["notes"] = (text + " " + note["append"]).strip()
    status_counts = {"has_keeper": 0, "searched_none": 0, "not_searched": 0}
    for row in rows.values():
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
    cat["counts"] = status_counts
    cat["counts"]["keeper_total"] = sum(len(r.get("keepers", [])) for r in rows.values())
    CAT.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    do_apply = "--apply" in sys.argv
    cat, rows, report = build()
    DRYRUN.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], indent=1))
    if report["problems"]:
        print("PROBLEMS:")
        for p in report["problems"]:
            print(" -", p)
        return 1
    if report["unmatched"]:
        print("UNMATCHED:")
        for u in report["unmatched"]:
            print(" -", u)
    if do_apply:
        shutil.copy2(CAT, BACKUP)
        print("backup ->", BACKUP)
        apply(cat, rows, report)
        print("applied; counts =", cat["counts"])
    else:
        print("dry run only ->", DRYRUN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
