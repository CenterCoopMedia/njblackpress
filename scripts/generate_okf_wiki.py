#!/usr/bin/env python3
"""Generate and validate the open knowledge format wiki."""
from __future__ import annotations

import argparse
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
    return json.dumps(str(value), ensure_ascii=False)


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
    return text if text.endswith((".", "!", "?", "]")) else text + "."


def markdown_cell(value: str) -> str:
    text = clean(value) or "Unknown"
    text = text.replace("\\", "\\\\").replace("|", "\\|")
    return "<br>".join(part.strip() for part in text.splitlines() if part.strip()) or "Unknown"


def markdown_link(path: Path | str, label: str) -> str:
    safe_label = clean(label).replace("[", "\\[").replace("]", "\\]")
    return f"[{safe_label}]({Path(path).as_posix()})"


def load_payload() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def load_publications() -> list[dict[str, Any]]:
    payload = load_payload()
    publications = payload["publications"]
    return sorted(publications, key=lambda p: (p.get("yearFounded") or 9999, p.get("name") or ""))


def publication_filename(pub: dict[str, Any]) -> str:
    return f"{pub['id']:03d}-{slugify(pub['name'])}.md"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = "\n".join(line.rstrip() for line in body.splitlines()) + "\n"
    path.write_text(cleaned, encoding="utf-8")


def table(rows: list[tuple[str, str]]) -> str:
    header = "| Field | Value |\n|---|---|\n"
    return header + "".join(f"| {markdown_cell(key)} | {markdown_cell(value)} |\n" for key, value in rows)


def unique_slug_map(names: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    used: set[str] = set()
    for name in sorted(set(filter(None, names))):
        base = slugify(name)
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}-{suffix}"
            suffix += 1
        used.add(candidate)
        result[name] = candidate
    return result


def group_links(base: str, names: list[str], slugs: dict[str, str]) -> str:
    items = sorted(set(filter(None, names)))
    return "\n".join(f"- {markdown_link(f'{base}/{slugs[name]}.md', name)}" for name in items)


def page_timestamp(explicit_timestamp: str | None) -> str:
    if explicit_timestamp:
        return explicit_timestamp
    index_path = OUT_DIR / "index.md"
    if index_path.exists():
        match = re.search(r'^timestamp: "([^"]+)"$', index_path.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return match.group(1)
    return date.today().isoformat()


def publication_page(pub: dict[str, Any], timestamp: str, city_slugs: dict[str, str], decade_slugs: dict[str, str], format_slugs: dict[str, str]) -> str:
    name = clean(pub.get("name"))
    city = clean(pub.get("city")) or "Unknown"
    decade = clean(pub.get("decade")) or "Unknown"
    fmt = clean(pub.get("format")) or "Unknown"
    body = frontmatter(
        type="publication",
        title=name,
        description=f"Archive wiki record for {name}.",
        resource=pub.get("websiteUrl") or pub.get("archiveUrl") or "data/publications.json",
        tags=["nj-black-press", "publication", slugify(city), slugify(decade), slugify(fmt)],
        timestamp=timestamp,
        archive_id=pub["id"],
        status="active" if pub.get("isActive") else "inactive-or-historical",
    )
    body += f"# {name}\n\n"
    body += table([
        ("Archive id", str(pub["id"])),
        ("Alternate name", clean(pub.get("alternateName"))),
        ("City", markdown_link(Path("../cities") / f"{city_slugs[city]}.md", city)),
        ("Publishers or owners", clean(pub.get("publishers"))),
        ("Founded", clean(pub.get("yearFounded"))),
        ("Ceased", clean(pub.get("yearCeased")) or ("Active" if pub.get("isActive") else "Unknown")),
        ("Decade", markdown_link(Path("../decades") / f"{decade_slugs[decade]}.md", decade)),
        ("Format", markdown_link(Path("../formats") / f"{format_slugs[fmt]}.md", fmt)),
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
    body += f"- {markdown_link('../archive-overview.md', 'Archive overview')}\n"
    body += f"- {markdown_link('../data-model.md', 'Data model')}\n"
    return body


def write_group(kind: str, groups: dict[str, list[dict[str, Any]]], timestamp: str, slugs: dict[str, str]) -> None:
    page_type = kind[:-1]
    for name, items in sorted(groups.items()):
        desc = f"{page_type} page for {name} in the NJ Black Press archive."
        body = frontmatter(type=page_type, title=name, description=desc, tags=["nj-black-press", page_type], timestamp=timestamp)
        noun = "record" if len(items) == 1 else "records"
        body += f"# {name}\n\nThis page links {len(items)} publication {noun} in this {page_type} grouping.\n\n"
        body += "## Publications\n\n"
        for pub in sorted(items, key=lambda p: p.get("name") or ""):
            years = str(pub.get("yearFounded") or "Unknown")
            body += f"- {markdown_link(f'../publications/{publication_filename(pub)}', pub['name'])} — {years}\n"
        write(OUT_DIR / kind / f"{slugs[name]}.md", body)


def build(generated_at: str | None = None) -> None:
    pubs = load_publications()
    timestamp = page_timestamp(generated_at)
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

    city_slugs = unique_slug_map(list(by_city.keys()))
    decade_slugs = unique_slug_map(list(by_decade.keys()))
    format_slugs = unique_slug_map(list(by_format.keys()))

    for pub in pubs:
        write(OUT_DIR / "publications" / publication_filename(pub), publication_page(pub, timestamp, city_slugs, decade_slugs, format_slugs))

    write_group("cities", by_city, timestamp, city_slugs)
    write_group("decades", by_decade, timestamp, decade_slugs)
    write_group("formats", by_format, timestamp, format_slugs)

    active = sum(1 for p in pubs if p.get("isActive"))
    format_counts = Counter(clean(p.get("format")) or "Unknown" for p in pubs)
    index = frontmatter(type="index", title="NJ Black Press archive wiki", description="Open knowledge format entry point for the archive wiki.", tags=["nj-black-press", "okf", "wiki"], timestamp=timestamp)
    index += "# NJ Black Press archive wiki\n\n"
    index += "This open knowledge format wiki gives humans and agents a file-based map of the NJ Black Press archive. Each page is markdown with YAML frontmatter and standard markdown links.\n\n"
    index += "## Start here\n\n- [Archive overview](archive-overview.md)\n- [Data model](data-model.md)\n- [Publication index](publications.md)\n- [City index](cities.md)\n- [Decade index](decades.md)\n- [Format index](formats.md)\n- [Change log](log.md)\n\n"
    index += f"## Snapshot\n\n- Publication records: {len(pubs)}\n- Active records: {active}\n- City groupings: {len(by_city)}\n- Date generated: {timestamp}\n"
    write(OUT_DIR / "index.md", index)

    overview = frontmatter(type="overview", title="Archive overview", description="Summary of the NJ Black Press archive scope and wiki structure.", tags=["nj-black-press", "archive"], timestamp=timestamp)
    overview += "# Archive overview\n\nThe archive documents Black-owned and Black-focused publications connected to New Jersey from 1880 to the present. It includes newspapers, magazines, newsletters, journals, and digital outlets.\n\n"
    overview += "## Wiki structure\n\n- One publication record per file under `publications/`.\n- City, decade, and format pages group records for browsing.\n- `data-model.md` explains the fields used in each publication page.\n- `log.md` records generation notes.\n\n"
    overview += "## Format counts\n\n" + "\n".join(f"- {name}: {count}" for name, count in sorted(format_counts.items())) + "\n"
    write(OUT_DIR / "archive-overview.md", overview)

    data_model = frontmatter(type="schema", title="Data model", description="Field guide for the publication records used by the wiki.", tags=["nj-black-press", "schema", "data"], timestamp=timestamp)
    data_model += "# Data model\n\nPublication pages are generated from `data/publications.json`. The source values are preserved as written except for empty values, which are shown as unknown in tables.\n\n"
    fields = ["id", "name", "alternateName", "city", "publishers", "yearFounded", "yearCeased", "frequency", "format", "languages", "archiveUrl", "websiteUrl", "targetAudience", "primaryFocus", "medium", "missionStatement", "keyStaff", "historicalNotes", "isActive", "decade"]
    data_model += "## Fields\n\n" + "\n".join(f"- `{field}`" for field in fields) + "\n"
    write(OUT_DIR / "data-model.md", data_model)

    for kind, groups in [("cities", by_city), ("decades", by_decade), ("formats", by_format)]:
        body = frontmatter(type="index", title=f"{kind} index", description=f"Index of {kind} in the archive wiki.", tags=["nj-black-press", kind], timestamp=timestamp)
        slug_lookup = {"cities": city_slugs, "decades": decade_slugs, "formats": format_slugs}[kind]
        body += f"# {kind} index\n\n" + group_links(kind, list(groups.keys()), slug_lookup) + "\n"
        write(OUT_DIR / f"{kind}.md", body)

    pub_index = frontmatter(type="index", title="Publication index", description="Alphabetical index of publication wiki records.", tags=["nj-black-press", "publications"], timestamp=timestamp)
    pub_index += "# Publication index\n\n"
    for pub in sorted(pubs, key=lambda p: p.get("name") or ""):
        pub_index += f"- {markdown_link(f'publications/{publication_filename(pub)}', pub['name'])}\n"
    write(OUT_DIR / "publications.md", pub_index)

    log = frontmatter(type="log", title="Wiki change log", description="Generation log for the open knowledge format wiki.", tags=["nj-black-press", "okf", "log"], timestamp=timestamp)
    log += f"# Wiki change log\n\n- {timestamp}: Generated the open knowledge format wiki bundle from `data/publications.json` with {len(pubs)} publication pages and {len(list(OUT_DIR.rglob('*.md'))) + 1} markdown files.\n"
    write(OUT_DIR / "log.md", log)


def validate() -> None:
    pubs = load_publications()
    files = list(OUT_DIR.rglob("*.md"))
    missing_type = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        frontmatter_block = text.split("---", 2)[1] if text.startswith("---\n") else ""
        if "\ntype:" not in frontmatter_block and not frontmatter_block.startswith("type:"):
            missing_type.append(path)
    publication_files = list((OUT_DIR / "publications").glob("*.md"))
    city_count = len({clean(pub.get("city")) or "Unknown" for pub in pubs})
    decade_count = len({clean(pub.get("decade")) or "Unknown" for pub in pubs})
    format_count = len({clean(pub.get("format")) or "Unknown" for pub in pubs})
    expected_total = len(pubs) + city_count + decade_count + format_count + 8
    if len(publication_files) != len(pubs):
        raise SystemExit(f"expected {len(pubs)} publication files, found {len(publication_files)}")
    if len(files) != expected_total:
        raise SystemExit(f"expected {expected_total} markdown files, found {len(files)}")
    if missing_type:
        names = ", ".join(str(path) for path in missing_type[:5])
        raise SystemExit(f"missing type frontmatter: {names}")
    print(f"validated {len(files)} markdown files")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or validate the open knowledge format wiki.")
    parser.add_argument("--check", action="store_true", help="validate the generated wiki without writing files")
    parser.add_argument("--generated-at", help="date to write into wiki frontmatter, for reproducible output")
    args = parser.parse_args()
    if args.check:
        validate()
    else:
        build(args.generated_at)


if __name__ == "__main__":
    main()
