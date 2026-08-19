from pathlib import Path
import json

scratch = Path(r"C:\Users\JOEAMD~1\AppData\Local\Temp\grok-goal-484f1928529f\implementer")
scratch.mkdir(parents=True, exist_ok=True)
pubs = json.loads(Path("data/publications.json").read_text(encoding="utf-8"))["publications"]
by_id = {p["id"]: p.get("historicalNotes") or "" for p in pubs}
checks = {
    10: ["Bradley", "1194114727", "Republican State Committee", "1194116748"],
    31: ["burned out", "497174278", "143869436"],
    38: ["436807841", "436760060"],
    16: ["newarkafamnewspapers", "NewJerseyHeraldNews19380521a"],
    34: ["Alfred P. Smith", "A. P. Smith's Paper", "1881"],
    37: ["state-wide circulation", "Paterson News"],
    2: ["Melvin B. Johnson", "1946"],
    57: ["Leon Snead", "Frances O. Grant"],
    101: ["After Hours", "Harry B. Webber", "1940s"],
    87: ["Camp Cooper", "A. W. Reed"],
    7: ["WHi", "38227497", "12 March 1909"],
    3: ["NjCaHi", "C. N. Green", "1918"],
    45: ["Archie J. Morgan", "DHU", "quarterly"],
    79: ["Ada Smith", "King Hiram"],
    102: ["1356", "1275-C"],
    67: ["Bronze Thrills", "Sepia"],
    30: ["Albert E. Hart", "4470"],
    62: ["243", "Yusef Iman"],
    28: ["934", "Black New Ark", "WHi"],
    69: ["1867", "Jihad", "Spellman"],
    70: ["1978", "Ralph Michel"],
    133: ["2512", "United Committee"],
    76: ["4335", "Housing", "WHi"],
    73: ["6142", "Utimme", "weekly minority"],
    41: ["6211", "NjPla", "Voice Associates"],
    113: ["6279", "George S. Adams", "WHi"],
    56: ["6026", "U.A.M.E."],
    68: ["3735", "Carolyn Odom"],
    105: ["4920", "Everette T. Christmas"],
    103: ["6003", "William Paterson"],
    95: ["5151", "Cresskill"],
    1: ["2 Hype", "River Edge"],
    114: ["6483", "Kate Ferguson"],
    50: ["4261", "Harry B. Webber"],
    26: ["2786", "Just Us Books"],
}
lines = []
for pid, needles in checks.items():
    note = by_id[pid]
    missing = [n for n in needles if n not in note]
    lines.append(f"id {pid}: {'OK' if not missing else 'MISSING ' + ','.join(missing)}")
(scratch / "notes-check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
Path("docs/data/publications.json").write_bytes(Path("data/publications.json").read_bytes())
Path("docs/data/featured-publications.json").write_bytes(Path("data/featured-publications.json").read_bytes())
print("copied docs data")
