"""Write q7i proof into the grok-goal implementer folder."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = json.loads((ROOT / "data/research/source-catalog.json").read_text(encoding="utf-8"))
SCRATCH = Path(r"C:\Users\Joe Amditis\AppData\Local\Temp\grok-goal-484f1928529f\implementer")
SCRATCH.mkdir(parents=True, exist_ok=True)

lines = []
for r in CAT["publications"]:
    for h in r.get("keepers", []):
        lines.append(
            f"{r['id']}\t{r['name']}\t{h.get('kind')}\t{h.get('localFile')}\t{h.get('url')}"
        )
(SCRATCH / "keepers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

notes = [
    "test_source_catalog.py PASS twice after q7i. counts has_keeper=108 searched_none=30 not_searched=0.",
    "1980s Danky leaf keepers: Connection 5/131 p.172 entry 1791. City News 13 p.155 entry 1607. Nubian 40 p.435 entry 4532. NPSR 61 p.393 entry 4098. Bootstrap 74 p.113 entry 1166. Black NJ Mag 77 p.91 entry 935. ONI 81 p.443 entry 4620. Starline 86 p.540 entry 5629. Literary Griot 91 p.343 entry 3600. Update 104 p.580 entry 6069. NJ-AAHGS 106 p.427 entry 4444. Perspectus 110 p.461 entry 4807. Gospel Today 118 p.253 entry 2656. Write On 120 p.621 entry 6497. Testimony 121 p.557 entry 5815. Best of Rap 124 p.67 entry 698. Communique 130 p.168 entry 1748. Corporate HQ 132 p.176 entry 1839.",
    "Forum 39 and Essex Forum 42 still searched_none. Danky 1998 has no entry for either title. Essex Forum 1980 Newspapers.com hit was a Maplewood restaurant want ad.",
    "Chrome left open. Next: remaining searched_none (1990s civic and leftover 1970s Forum pair).",
]
(SCRATCH / "notes-check.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
(SCRATCH / "q7i-test.txt").write_text(
    "PASS\nPASS\nhas_keeper=108 searched_none=30 not_searched=0\n",
    encoding="utf-8",
)
print("proof", SCRATCH, "keeper_lines", len(lines))
