#!/usr/bin/env python3
"""Generate an open knowledge format wiki for the NJ Black Press Archive."""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "publications.json"
OUT_DIR = ROOT / "okf"
TODAY = date.today().isoformat()


def slugify(value: str, fallback: str = "item") -> str:
    text = value.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or fallback


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if value is None:
        return "null"
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'


def frontmatter(**fields: Any) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {yaml_scalar(item)}")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def sentence(text: str) -> str:
    if not text:
        return ""
    return text if text.endswith((".", "!", "?")) else text + "."


def load_publications() -> list[dict[str, Any]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    publications = payload["publications"]
    return sorted(publications, key=lambda p: (p.get("yearFounded") or 9999, p.get("name") or ""))


def link(path: Path, label: str) -> str:
    return f"[{label}]({path.as_posix()})"


def publication_filename(pub: dict[str, Any]) -> str:
    return f"{pub['id']:03d}-{slugify(pub['name'])}.md"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in body.splitlines()) + "\n"
    path.write_text(cleaned, encoding="utf-8")


def table(rows: list[tuple[str, str]]) -> str:
    return "| Field | Value |\n|---|---|\n" + "".join(f"| {k} | {v or 'Unknown'} |\n" for k, v in rows)


def group_links(base: str, names: list[str]) -> str:
    return "\n".join(f"- [{name}]({base}/{slugify(name)}.md)" for name in sorted(set(filter(None, names))))


def build() -> None:
    pubs = load_publications()
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "publications").mkdir(parents=True)

    by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_decade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_format: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pub in pubs:
        by_city[clean(pub.get("city")) or "Unknown"].append(pub)
        by_decade[clean(pub.get("decade")) or "Unknown"].append(pub)
        by_format[clean(pub.get("format")) or "Unknown"].append(pub)

    # Publication pages.
    for pub in pubs:
        name = clean(pub.get("name"))
        filename = publication_filename(pub)
        city = clean(pub.get("city")) or "Unknown"
        decade = clean(pub.get("decade")) or "Unknown"
        fmt = clean(pub.get("format")) or "Unknown"
        body = frontmatter(
            type="publication",
            title=name,
            description=f"Archive wiki record for {name}.",
            resource=pub.get("websiteUrl") or pub.get("archiveUrl") or "data/publications.json",
            tags=["nj-black-press", "publication", slugify(city), slugify(decade), slugify(fmt)],
            timestamp=TODAY,
            archive_id=pub["id"],
            status="active" if pub.get("isActive") else "inactive-or-historical",
        )
        body += f"# {name}\n\n"
        body += table([
            ("Archive id", str(pub["id"])),
            ("Alternate name", clean(pub.get("alternateName"))),
            ("City", link(Path("../cities") / f"{slugify(city)}.md", city)),
            ("Publishers or owners", clean(pub.get("publishers"))),
            ("Founded", clean(pub.get("yearFounded"))),
            ("Ceased", clean(pub.get("yearCeased")) or ("Active" if pub.get("isActive") else "Unknown")),
            ("Decade", link(Path("../decades") / f"{slugify(decade)}.md", decade)),
            ("Format", link(Path("../formats") / f"{slugify(fmt)}.md", fmt)),
            ("Frequency", clean(pub.get("frequency"))),
            ("Medium", clean(pub.get("medium"))),
            ("Languages", clean(pub.get("languages"))),
            ("Primary focus", clean(pub.get("primaryFocus"))),
            ("Target audience", clean(pub.get("targetAudience"))),
        ])
        for heading, key in [
            ("Mission statement", "missionStatement"),
            ("Key staff", "keyStaff"),
            ("Historical notes", "historicalNotes"),
        ]:
            value = clean(pub.get(key))
            if value:
                body += f"\n## {heading}\n\n{sentence(value)}\n"
        links = []
        if pub.get("archiveUrl"):
            links.append(f"- [Archive record]({pub['archiveUrl']})")
        if pub.get("websiteUrl"):
            links.append(f"- [Website]({pub['websiteUrl']})")
        if links:
            body += "\n## External links\n\n" + "\n".join(links) + "\n"
        body += "\n## Related wiki pages\n\n"
        body += f"- {link(Path('../archive-overview.md'), 'Archive overview')}\n"
        body += f"- {link(Path('../data-model.md'), 'Data model')}\n"
        write(OUT_DIR / "publications" / filename, body)

    # Group pages.
    def write_group(kind: str, groups: dict[str, list[dict[str, Any]]]) -> None:
        for name, items in sorted(groups.items()):
            desc = f"{kind[:-1].capitalize()} page for {name} in the NJ Black Press Archive."
            body = frontmatter(type=kind[:-1], title=name, description=desc, tags=["nj-black-press", kind[:-1]], timestamp=TODAY)
            body += f"# {name}\n\nThis page links {len(items)} publication records in this {kind[:-1]} grouping.\n\n"
            body += "## Publications\n\n"
            for pub in sorted(items, key=lambda p: p.get("name") or ""):
                years = str(pub.get("yearFounded") or "Unknown")
                body += f"- [{pub['name']}](../publications/{publication_filename(pub)}) — {years}\n"
            write(OUT_DIR / kind / f"{slugify(name)}.md", body)

    write_group("cities", by_city)
    write_group("decades", by_decade)
    write_group("formats", by_format)

    active = sum(1 for p in pubs if p.get("isActive"))
    format_counts = Counter(clean(p.get("format")) or "Unknown" for p in pubs)
    city_count = len(by_city)
    index = frontmatter(type="index", title="NJ Black Press Archive wiki", description="Open knowledge format entry point for the archive wiki.", tags=["nj-black-press", "okf", "wiki"], timestamp=TODAY)
    index += "# NJ Black Press Archive wiki\n\n"
    index += "This open knowledge format wiki gives humans and agents a file-based map of the NJ Black Press Archive. Each page is markdown with YAML frontmatter and standard markdown links.\n\n"
    index += "## Start here\n\n- [Archive overview](archive-overview.md)\n- [Data model](data-model.md)\n- [Publication index](publications.md)\n- [City index](cities.md)\n- [Decade index](decades.md)\n- [Format index](formats.md)\n- [Change log](log.md)\n\n"
    index += f"## Snapshot\n\n- Publication records: {len(pubs)}\n- Active records: {active}\n- City groupings: {city_count}\n- Date generated: {TODAY}\n"
    write(OUT_DIR / "index.md", index)

    overview = frontmatter(type="overview", title="Archive overview", description="Summary of the NJ Black Press Archive scope and wiki structure.", tags=["nj-black-press", "archive"], timestamp=TODAY)
    overview += "# Archive overview\n\nThe archive documents Black-owned and Black-focused publications connected to New Jersey from 1880 to the present. It includes newspapers, magazines, newsletters, journals, and digital outlets.\n\n"
    overview += "## Wiki structure\n\n- One publication record per file under `publications/`.\n- City, decade, and format pages group records for browsing.\n- `data-model.md` explains the fields used in each publication page.\n- `log.md` records generation notes.\n\n"
    overview += "## Format counts\n\n" + "\n".join(f"- {name}: {count}" for name, count in sorted(format_counts.items())) + "\n"
    write(OUT_DIR / "archive-overview.md", overview)

    data_model = frontmatter(type="schema", title="Data model", description="Field guide for the publication records used by the wiki.", tags=["nj-black-press", "schema", "data"], timestamp=TODAY)
    data_model += "# Data model\n\nPublication pages are generated from `data/publications.json`. The source values are preserved as written except for empty values, which are shown as unknown in tables.\n\n"
    fields = ["id", "name", "alternateName", "city", "publishers", "yearFounded", "yearCeased", "frequency", "format", "languages", "archiveUrl", "websiteUrl", "targetAudience", "primaryFocus", "medium", "missionStatement", "keyStaff", "historicalNotes", "isActive", "decade"]
    data_model += "## Fields\n\n" + "\n".join(f"- `{f}`" for f in fields) + "\n"
    write(OUT_DIR / "data-model.md", data_model)

    for kind, groups in [("cities", by_city), ("decades", by_decade), ("formats", by_format)]:
        body = frontmatter(type="index", title=f"{kind} index", description=f"Index of {kind} in the archive wiki.", tags=["nj-black-press", kind], timestamp=TODAY)
        body += f"# {kind} index\n\n" + group_links(kind, list(groups.keys())) + "\n"
        write(OUT_DIR / f"{kind}.md", body)

    pub_index = frontmatter(type="index", title="Publication index", description="Alphabetical index of publication wiki records.", tags=["nj-black-press", "publications"], timestamp=TODAY)
    pub_index += "# Publication index\n\n"
    for pub in sorted(pubs, key=lambda p: p.get("name") or ""):
        pub_index += f"- [{pub['name']}](publications/{publication_filename(pub)})\n"
    write(OUT_DIR / "publications.md", pub_index)

    log = frontmatter(type="log", title="Wiki change log", description="Generation log for the open knowledge format wiki.", tags=["nj-black-press", "okf", "log"], timestamp=TODAY)
    log += f"# Wiki change log\n\n- {TODAY}: Generated the first open knowledge format wiki bundle from `data/publications.json` with {len(pubs)} publication pages.\n"
    write(OUT_DIR / "log.md", log)


if __name__ == "__main__":
    build()
