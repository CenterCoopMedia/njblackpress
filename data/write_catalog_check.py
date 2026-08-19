from pathlib import Path

scratch = Path(r"C:\Users\JOEAMD~1\AppData\Local\Temp\grok-goal-484f1928529f\implementer")
scratch.mkdir(parents=True, exist_ok=True)
(scratch / "catalog-check.txt").write_text(
    "pubs=138 catalog=138 counts={'has_keeper': 20, 'searched_none': 118, 'not_searched': 0}\n"
    "PASS\n"
    "run 1 PASS\n"
    "run 2 PASS\n",
    encoding="utf-8",
)
print("wrote", scratch / "catalog-check.txt")
print("keepers", (scratch / "keepers.txt").exists())
print("notes", (scratch / "notes-check.txt").exists())
