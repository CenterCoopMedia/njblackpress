"""Issue #34: build docs/data/events.json and docs/data/stories.json for the frontend.

Reads data/research/editorial/events.json and stories.json (editorial source,
not touched by this script), conforms them to site conventions (top-level
array + metadata block like publications.json), and writes:
  - data/events.json, data/stories.json      (pipeline source of truth)
  - docs/data/events.json, docs/data/stories.json  (frontend copies)

Run:
  python data/build_site_events_stories.py
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS_SRC = ROOT / "data" / "research" / "editorial" / "events.json"
STORIES_SRC = ROOT / "data" / "research" / "editorial" / "stories.json"
DATA_EVENTS = ROOT / "data" / "events.json"
DATA_STORIES = ROOT / "data" / "stories.json"
DOCS_EVENTS = ROOT / "docs" / "data" / "events.json"
DOCS_STORIES = ROOT / "docs" / "data" / "stories.json"


def decade_of(date_str):
    """Extract a 'YYYYs' decade label from an event's date string."""
    digits = "".join(c for c in date_str[:4] if c.isdigit())
    if len(digits) == 4:
        return f"{(int(digits) // 10) * 10}s"
    return "Unknown"


def build_events():
    raw = json.loads(EVENTS_SRC.read_text(encoding="utf-8"))
    events = raw["events"]

    decades = {}
    for e in events:
        d = decade_of(e.get("date", ""))
        decades[d] = decades.get(d, 0) + 1
    decades_sorted = dict(
        sorted(decades.items(), key=lambda kv: (kv[0] == "Unknown", kv[0]))
    )

    confidence_counts = {}
    for e in events:
        c = e.get("confidence", "unknown")
        confidence_counts[c] = confidence_counts.get(c, 0) + 1

    metadata = {
        "totalCount": len(events),
        "generated": raw.get("metadata", {}).get("generated"),
        "byDecade": decades_sorted,
        "byConfidence": confidence_counts,
        "sourceFiles": sorted(
            {sf for e in events for sf in e.get("sourceFiles", [])}
        ),
    }
    return {"events": events, "metadata": metadata}


def build_stories():
    raw = json.loads(STORIES_SRC.read_text(encoding="utf-8"))
    stories = raw["stories"]

    eras = {}
    for s in stories:
        era = s.get("era", "Unknown")
        eras[era] = eras.get(era, 0) + 1

    metadata = {
        "totalCount": len(stories),
        "byEra": eras,
    }
    return {"stories": stories, "metadata": metadata}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    events_out = build_events()
    stories_out = build_stories()

    write_json(DATA_EVENTS, events_out)
    write_json(DATA_STORIES, stories_out)
    shutil.copyfile(DATA_EVENTS, DOCS_EVENTS)
    shutil.copyfile(DATA_STORIES, DOCS_STORIES)

    print(
        f"events: {events_out['metadata']['totalCount']} written to data/ and docs/data/"
    )
    print(
        f"stories: {stories_out['metadata']['totalCount']} written to data/ and docs/data/"
    )


if __name__ == "__main__":
    main()
