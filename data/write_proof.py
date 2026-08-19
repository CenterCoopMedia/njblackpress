from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))
CLIPS = json.loads((ROOT / "data/research/newspapers-com/clips/catalog.json").read_text(encoding="utf-8"))
SHOTS = ROOT / "data/research/wayback/snapshots"
SCRATCH = Path(r"C:\Users\JOEAMD~1\AppData\Local\Temp\grok-goal-484f1928529f\implementer")
SCRATCH.mkdir(parents=True, exist_ok=True)

# Re-attach earliest wayback screenshots as keepers.
rows = {r["id"]: r for r in CAT["publications"]}
OFFLINE_SIZE = 59084
for png in SHOTS.glob("*.png"):
    if png.stat().st_size == OFFLINE_SIZE:
        continue
    try:
        pid = int(png.stem.split("-", 1)[0])
    except ValueError:
        continue
    if pid not in rows:
        continue
    rel = str(png.relative_to(ROOT)).replace("\\", "/")
    already = any(h.get("localFile") == rel for h in rows[pid]["keepers"])
    if already:
        continue
    rows[pid]["keepers"].append(
        {
            "kind": "wayback_snapshot",
            "title": f"earliest Wayback screenshot {png.name}",
            "url": None,
            "localFile": rel,
            "source": "Wayback Machine",
            "date": None,
        }
    )
    # fill url from sources.wayback if present
    for hit in rows[pid]["sources"]["wayback"]["hits"]:
        if (hit.get("title") or "").startswith("earliest"):
            rows[pid]["keepers"][-1]["url"] = hit.get("url")
            rows[pid]["keepers"][-1]["date"] = (hit.get("timestamp") or "")[:8]
            break
    rows[pid]["status"] = "has_keeper"

CAT["publications"] = [rows[i] for i in sorted(rows)]
CAT["counts"] = {
    "has_keeper": sum(1 for r in CAT["publications"] if r["status"] == "has_keeper"),
    "searched_none": sum(1 for r in CAT["publications"] if r["status"] == "searched_none"),
    "not_searched": sum(1 for r in CAT["publications"] if r["status"] == "not_searched"),
}
(ROOT / "data/research/source-catalog.json").write_text(json.dumps(CAT, indent=2, ensure_ascii=False), encoding="utf-8")

lines = []
for r in CAT["publications"]:
    for h in r.get("keepers", []):
        lines.append(f"{r['id']}\t{r['name']}\t{h.get('kind')}\t{h.get('localFile')}\t{h.get('url')}")
(SCRATCH / "keepers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

notes = []
notes.append("New facts written back: Echo 1904 fire and 1909 Red Bank move; Herbert 1893 Bradley letter and 1895 GOP committee; Trumpet/Murrell 1893 Asbury Park; Herald News IA 124-issue run 1938-1945.")
notes.append("Newspapers.com Entire Page download path mapped: button[title=Print or Download] -> Entire Page card -> Save as JPG / Save as PDF*. Automated file save via CDP did not land a file; PNG previews remain the local keepers.")
(SCRATCH / "notes-check.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
print("counts", CAT["counts"], "keeper_lines", len(lines))
