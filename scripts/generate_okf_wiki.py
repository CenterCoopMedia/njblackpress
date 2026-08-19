#!/usr/bin/env python3
"""Generate and validate the open knowledge format wiki.

The wiki is a portable directory of markdown files (with YAML frontmatter and
ordinary markdown links) generated from ``data/publications.json``. It gives
people and agents a browsable, file-based map of the NJ Black Press archive
without running the website JavaScript.
"""
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

# Group kinds and their grammatical singular (the source data pluralizes the
# directory names; naive ``kind[:-1]`` turned "cities" into "citie").
GROUP_SINGULAR = {
    "cities": "city",
    "decades": "decade",
    "formats": "format",
    "mediums": "medium",
}

# Short factual context for each founding decade, drawn from the eras the
# archive spans. Keeps decade pages oriented without editorializing the data.
DECADE_CONTEXT = {
    "1880s": "Post-Reconstruction. New Jersey's earliest documented Black newspapers appear.",
    "1900s": "Jim Crow era. A small but persistent Black press serves growing urban communities.",
    "1910s": "The Great Migration begins to reshape Northern Black readerships.",
    "1920s": "The Great Migration and Harlem Renaissance energize Black cultural and civic life.",
    "1930s": "Depression-era community papers proliferate, especially around Newark.",
    "1940s": "Wartime and the Double V campaign sharpen the Black press's civil-rights voice.",
    "1950s": "Early civil-rights organizing; photo magazines and weeklies expand.",
    "1960s": "Civil-rights and Black Power movements; the 1967 Newark uprising reshapes the press.",
    "1970s": "The archive's peak decade — Black Power, Black Arts, and community newsletters flourish.",
    "1980s": "Established weeklies mature alongside cultural and youth publications.",
    "1990s": "Community and cultural periodicals continue; the digital transition looms.",
    "2000s": "Print contraction; few new titles are founded.",
    "2010s": "Digital-native outlets emerge, reviving local Black journalism online.",
    "2020s": "Contemporary multimedia newsrooms and nonprofit models lead the active archive.",
    "Unknown": "Records whose founding year is not yet established.",
}

# Field documentation for the data-model page: (description, origin).
FIELD_DOCS: list[tuple[str, str, str]] = [
    ("id", "Unique integer identifier for the record.", "source"),
    ("name", "Publication name.", "source"),
    ("alternateName", "Other names the publication used.", "source"),
    ("city", "Primary city of operation.", "source"),
    ("publishers", "Publishing entity or individuals.", "source"),
    ("yearFounded", "Year the publication started.", "source"),
    ("yearCeased", "Year it stopped (blank if still active or unknown).", "source"),
    ("frequency", "Cadence such as weekly, monthly, or daily.", "source"),
    ("format", "Self-described format string (newspaper, periodical, magazine, etc.).", "source"),
    ("languages", "Primary language(s); defaults to English.", "source"),
    ("archiveUrl", "Link to a holding archive (Library of Congress, WorldCat, Internet Archive).", "source"),
    ("websiteUrl", "Current website, for active outlets.", "source"),
    ("targetAudience", "Intended readership.", "source"),
    ("primaryFocus", "Subject matter the publication covers.", "source"),
    ("medium", "Print, Digital, or Print/Digital.", "computed"),
    ("missionStatement", "Editorial philosophy or stated mission.", "source"),
    ("keyStaff", "Notable editors, publishers, or contributors.", "source"),
    ("historicalNotes", "Context, significance, and research findings.", "source"),
    ("isActive", "True when the publication is still operating (yearCeased is blank).", "computed"),
    ("decade", "Decade of founding, derived from yearFounded.", "computed"),
    ("isFeaturedHistoric", "Highlighted as a featured historic publication on the site.", "source"),
    ("isFeaturedContemporary", "Highlighted as a featured contemporary publication on the site.", "source"),
]


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


def as_link_url(value: Any) -> str | None:
    """Return a usable URL for ``value`` or None.

    Many ``archiveUrl`` fields hold catalog identifiers (``OCLC no. 12345``)
    rather than links; those return None so callers can show them as text.
    Bare domains (``example.com``) are promoted to ``https://``.
    """
    v = clean(value)
    if not v:
        return None
    if v.startswith(("http://", "https://")):
        return v
    if " " not in v and re.match(r"^[\w.-]+\.[a-z]{2,}(/.*)?$", v, re.IGNORECASE):
        return "https://" + v
    return None


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


def page_timestamp(explicit_timestamp: str | None) -> str:
    if explicit_timestamp:
        return explicit_timestamp
    index_path = OUT_DIR / "index.md"
    if index_path.exists():
        match = re.search(r'^timestamp: "([^"]+)"$', index_path.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return match.group(1)
    return date.today().isoformat()


# --- derived helpers ---------------------------------------------------------

def status_label(pub: dict[str, Any]) -> str:
    if pub.get("isActive"):
        return "Active"
    ceased = clean(pub.get("yearCeased"))
    return f"Ceased {ceased}" if ceased else "Ceased (date unknown)"


def life_span(pub: dict[str, Any]) -> str:
    founded = clean(pub.get("yearFounded")) or "?"
    if pub.get("isActive"):
        return f"{founded}–present"
    ceased = clean(pub.get("yearCeased"))
    return f"{founded}–{ceased}" if ceased else f"{founded}–?"


def featured_kind(pub: dict[str, Any]) -> str | None:
    if pub.get("isFeaturedHistoric"):
        return "historic"
    if pub.get("isFeaturedContemporary"):
        return "contemporary"
    return None


def format_category(fmt: str) -> str:
    """Collapse the 40 free-text format strings into broad, browsable groups."""
    f = (fmt or "").lower()
    if "comic" in f:
        return "Comics"
    if "newspaper" in f:
        return "Newspapers"
    if "magazine" in f:
        return "Magazines"
    if "journal" in f:
        return "Journals"
    if "newsletter" in f:
        return "Newsletters"
    if any(k in f for k in ("website", "multimedia", "multi-media", "radio", "stream", "online", "digital")):
        return "Digital & multimedia"
    if any(k in f for k in ("periodical", "serial", "bibliograph", "biograph", "volume", "publication", "print")):
        return "Periodicals & other print"
    return "Other"


def year_range(items: list[dict[str, Any]]) -> str:
    years = sorted(p["yearFounded"] for p in items if p.get("yearFounded"))
    if not years:
        return "Unknown"
    return str(years[0]) if years[0] == years[-1] else f"{years[0]}–{years[-1]}"


# --- page builders -----------------------------------------------------------

def publication_page(
    pub: dict[str, Any],
    timestamp: str,
    city_slugs: dict[str, str],
    decade_slugs: dict[str, str],
    format_slugs: dict[str, str],
    medium_slugs: dict[str, str],
    by_city: dict[str, list[dict[str, Any]]],
    by_decade: dict[str, list[dict[str, Any]]],
) -> str:
    name = clean(pub.get("name"))
    city = clean(pub.get("city")) or "Unknown"
    decade = clean(pub.get("decade")) or "Unknown"
    fmt = clean(pub.get("format")) or "Unknown"
    medium = clean(pub.get("medium")) or "Unknown"
    feat = featured_kind(pub)
    body = frontmatter(
        type="publication",
        title=name,
        description=f"Archive wiki record for {name}.",
        resource=pub.get("websiteUrl") or pub.get("archiveUrl") or "data/publications.json",
        tags=["nj-black-press", "publication", slugify(city), slugify(decade), slugify(fmt)],
        timestamp=timestamp,
        archive_id=pub["id"],
        status="active" if pub.get("isActive") else "inactive-or-historical",
        featured=bool(feat),
    )
    body += f"# {name}\n\n"
    if feat:
        body += f"> ⭐ Featured {feat} publication. See [Featured publications](../featured.md).\n\n"
    body += table([
        ("Archive id", str(pub["id"])),
        ("Alternate name", clean(pub.get("alternateName"))),
        ("City", markdown_link(Path("../cities") / f"{city_slugs[city]}.md", city)),
        ("Publishers or owners", clean(pub.get("publishers"))),
        ("Active years", life_span(pub)),
        ("Status", status_label(pub)),
        ("Decade", markdown_link(Path("../decades") / f"{decade_slugs[decade]}.md", decade)),
        ("Format", markdown_link(Path("../formats") / f"{format_slugs[fmt]}.md", fmt)),
        ("Medium", markdown_link(Path("../mediums") / f"{medium_slugs[medium]}.md", medium)),
        ("Frequency", clean(pub.get("frequency"))),
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

    archive_url = as_link_url(pub.get("archiveUrl"))
    website_url = as_link_url(pub.get("websiteUrl"))
    links = []
    if archive_url:
        links.append(f"- [Archive record]({archive_url})")
    if website_url:
        links.append(f"- [Website]({website_url})")
    if links:
        body += "\n## External links\n\n" + "\n".join(links) + "\n"
    archive_ref = clean(pub.get("archiveUrl"))
    if archive_ref and not archive_url:
        body += f"\n## Archive reference\n\n{sentence(archive_ref)}\n"

    # Related publications: siblings from the same city and the same decade.
    def siblings(group: list[dict[str, Any]], limit: int = 8) -> list[str]:
        others = [p for p in group if p["id"] != pub["id"]]
        others.sort(key=lambda p: p.get("yearFounded") or 9999)
        out = [
            f"- {markdown_link(f'./{publication_filename(p)}', p['name'])} — {life_span(p)}"
            for p in others[:limit]
        ]
        if len(others) > limit:
            out.append(f"- …and {len(others) - limit} more")
        return out

    related = []
    city_siblings = siblings(by_city.get(city, []))
    if city_siblings:
        related.append(f"### Also in {city}\n\n" + "\n".join(city_siblings))
    decade_siblings = siblings(by_decade.get(decade, []))
    if decade_siblings:
        related.append(f"### Also from the {decade}\n\n" + "\n".join(decade_siblings))
    if related:
        body += "\n## Related publications\n\n" + "\n\n".join(related) + "\n"

    body += "\n## Navigate\n\n"
    body += f"- {markdown_link('../index.md', 'Wiki home')}\n"
    body += f"- {markdown_link(Path('../cities') / f'{city_slugs[city]}.md', f'All {city} publications')}\n"
    body += f"- {markdown_link(Path('../decades') / f'{decade_slugs[decade]}.md', f'All {decade} publications')}\n"
    body += f"- {markdown_link('../archive-overview.md', 'Archive overview')}\n"
    body += f"- {markdown_link('../data-model.md', 'Data model')}\n"
    return body


def write_group(kind: str, groups: dict[str, list[dict[str, Any]]], timestamp: str, slugs: dict[str, str]) -> None:
    singular = GROUP_SINGULAR[kind]
    for name, items in sorted(groups.items()):
        active = sum(1 for p in items if p.get("isActive"))
        body = frontmatter(
            type=singular,
            title=name,
            description=f"{singular.capitalize()} page for {name} in the NJ Black Press archive.",
            tags=["nj-black-press", singular, slugify(name)],
            timestamp=timestamp,
            count=len(items),
        )
        body += f"# {name}\n\n"
        if singular == "decade" and name in DECADE_CONTEXT:
            body += f"_{DECADE_CONTEXT[name]}_\n\n"
        noun = "publication" if len(items) == 1 else "publications"
        body += (
            f"**{len(items)}** {noun} in this {singular} grouping · "
            f"**{active}** active · founding years **{year_range(items)}**.\n\n"
        )
        body += "## Publications\n\n| Publication | Years | Status |\n|---|---|---|\n"
        for pub in sorted(items, key=lambda p: (p.get("yearFounded") or 9999, p.get("name") or "")):
            link = markdown_link(f"../publications/{publication_filename(pub)}", pub["name"])
            body += f"| {link} | {markdown_cell(life_span(pub))} | {markdown_cell(status_label(pub))} |\n"
        body += f"\n## Navigate\n\n- {markdown_link('../index.md', 'Wiki home')}\n"
        body += f"- {markdown_link(f'../{kind}.md', f'All {kind}')}\n"
        write(OUT_DIR / kind / f"{slugs[name]}.md", body)


def write_group_index(kind: str, groups: dict[str, list[dict[str, Any]]], timestamp: str, slugs: dict[str, str]) -> None:
    singular = GROUP_SINGULAR[kind]
    body = frontmatter(
        type="index",
        title=f"{kind.capitalize()} index",
        description=f"Index of {kind} in the NJ Black Press archive wiki.",
        tags=["nj-black-press", kind],
        timestamp=timestamp,
        count=len(groups),
    )
    body += f"# {kind.capitalize()} index\n\n"
    body += f"{len(groups)} {kind} group the {sum(len(v) for v in groups.values())} publication records.\n\n"

    if kind == "formats":
        # Group the free-text formats under broad, sorted categories.
        by_cat: dict[str, list[str]] = defaultdict(list)
        for name in groups:
            by_cat[format_category(name)].append(name)
        order = ["Newspapers", "Magazines", "Periodicals & other print", "Journals",
                 "Newsletters", "Digital & multimedia", "Comics", "Other"]
        for cat in sorted(by_cat, key=lambda c: (order.index(c) if c in order else len(order), c)):
            names = sorted(by_cat[cat])
            total = sum(len(groups[n]) for n in names)
            body += f"## {cat} ({total})\n\n"
            for name in sorted(names, key=lambda n: (-len(groups[n]), n)):
                link = markdown_link(f"{kind}/{slugs[name]}.md", name)
                body += f"- {link} — {len(groups[name])}\n"
            body += "\n"
        return write(OUT_DIR / f"{kind}.md", body)

    # Cities/decades/mediums: a single list sorted by size (decades chronologically).
    if kind == "decades":
        names = sorted(groups, key=lambda n: (n == "Unknown", n))
    else:
        names = sorted(groups, key=lambda n: (-len(groups[n]), n))
    for name in names:
        link = markdown_link(f"{kind}/{slugs[name]}.md", name)
        active = sum(1 for p in groups[name] if p.get("isActive"))
        suffix = f" · {active} active" if active else ""
        body += f"- {link} — {len(groups[name])}{suffix}\n"
    write(OUT_DIR / f"{kind}.md", body)


def build_statistics(pubs: list[dict[str, Any]], by_city, by_decade, by_format, by_medium, timestamp: str, city_slugs, decade_slugs) -> str:
    total = len(pubs)
    active = sum(1 for p in pubs if p.get("isActive"))
    ceased = total - active
    body = frontmatter(
        type="statistics",
        title="Archive statistics",
        description="Counts and breakdowns across the NJ Black Press archive.",
        tags=["nj-black-press", "statistics"],
        timestamp=timestamp,
    )
    body += "# Archive statistics\n\n"
    body += (
        f"- Publication records: **{total}**\n"
        f"- Active: **{active}**\n"
        f"- Ceased or historical: **{ceased}**\n"
        f"- Cities: **{len(by_city)}**\n"
        f"- Distinct formats: **{len(by_format)}**\n"
        f"- Founding span: **{year_range(pubs)}**\n\n"
    )

    # Decade timeline with a simple bar chart.
    body += "## Publications by founding decade\n\n"
    decade_order = sorted(by_decade, key=lambda n: (n == "Unknown", n))
    max_count = max((len(v) for v in by_decade.values()), default=1)
    body += "| Decade | Count | Active | |\n|---|---|---|---|\n"
    for dec in decade_order:
        items = by_decade[dec]
        bar = "█" * max(1, round(len(items) / max_count * 24)) if items else ""
        dec_active = sum(1 for p in items if p.get("isActive"))
        link = markdown_link(f"decades/{decade_slugs[dec]}.md", dec)
        body += f"| {link} | {len(items)} | {dec_active} | {bar} |\n"

    # Top cities.
    body += "\n## Cities by publication count\n\n"
    ranked = sorted(by_city.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    body += "| City | Count | Active |\n|---|---|---|\n"
    for name, items in ranked[:15]:
        city_active = sum(1 for p in items if p.get("isActive"))
        link = markdown_link(f"cities/{city_slugs[name]}.md", name)
        body += f"| {link} | {len(items)} | {city_active} |\n"
    singles = sum(1 for v in by_city.values() if len(v) == 1)
    body += f"\n_{singles} cities have a single recorded publication. See the [full city index](cities.md)._\n"

    # Medium breakdown.
    body += "\n## Medium\n\n| Medium | Count |\n|---|---|\n"
    for name, items in sorted(by_medium.items(), key=lambda kv: -len(kv[1])):
        body += f"| {markdown_cell(name)} | {len(items)} |\n"

    # Format categories.
    body += "\n## Format categories\n\n"
    cat_counts: Counter[str] = Counter()
    for pub in pubs:
        cat_counts[format_category(clean(pub.get("format")) or "Unknown")] += 1
    body += "| Category | Count |\n|---|---|\n"
    for cat, count in cat_counts.most_common():
        body += f"| {markdown_cell(cat)} | {count} |\n"

    # Longest-running publications.
    def lifespan_years(p):
        f, c = p.get("yearFounded"), p.get("yearCeased")
        if not f:
            return None
        end = c if c else date.fromisoformat(timestamp).year
        return end - f

    spans = [(lifespan_years(p), p) for p in pubs]
    spans = sorted(((s, p) for s, p in spans if s is not None), key=lambda sp: -sp[0])
    body += "\n## Longest-running publications\n\n"
    body += "| Publication | Years | Span |\n|---|---|---|\n"
    for span, pub in spans[:10]:
        link = markdown_link(f"publications/{publication_filename(pub)}", pub["name"])
        body += f"| {link} | {markdown_cell(life_span(pub))} | {span} yrs |\n"
    body += "\n## Navigate\n\n- [Wiki home](index.md)\n- [Archive overview](archive-overview.md)\n"
    return body


def build_featured(pubs: list[dict[str, Any]], timestamp: str) -> str:
    historic = [p for p in pubs if p.get("isFeaturedHistoric")]
    contemporary = [p for p in pubs if p.get("isFeaturedContemporary")]
    body = frontmatter(
        type="index",
        title="Featured publications",
        description="Publications highlighted on the NJ Black Press archive site.",
        tags=["nj-black-press", "featured"],
        timestamp=timestamp,
        count=len(historic) + len(contemporary),
    )
    body += "# Featured publications\n\n"
    body += "Publications curated as featured records on the archive site.\n\n"

    def section(title: str, items: list[dict[str, Any]]) -> str:
        out = f"## {title} ({len(items)})\n\n| Publication | City | Years |\n|---|---|---|\n"
        for pub in sorted(items, key=lambda p: p.get("yearFounded") or 9999):
            link = markdown_link(f"publications/{publication_filename(pub)}", pub["name"])
            out += f"| {link} | {markdown_cell(clean(pub.get('city')) or 'Unknown')} | {markdown_cell(life_span(pub))} |\n"
        return out + "\n"

    body += section("Historic", historic)
    body += section("Contemporary", contemporary)
    body += "## Navigate\n\n- [Wiki home](index.md)\n- [Publication index](publications.md)\n"
    return body


def build(generated_at: str | None = None) -> None:
    pubs = load_publications()
    timestamp = page_timestamp(generated_at)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "publications").mkdir(parents=True)

    by_city: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_decade: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_format: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_medium: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pub in pubs:
        by_city[clean(pub.get("city")) or "Unknown"].append(pub)
        by_decade[clean(pub.get("decade")) or "Unknown"].append(pub)
        by_format[clean(pub.get("format")) or "Unknown"].append(pub)
        by_medium[clean(pub.get("medium")) or "Unknown"].append(pub)

    city_slugs = unique_slug_map(list(by_city.keys()))
    decade_slugs = unique_slug_map(list(by_decade.keys()))
    format_slugs = unique_slug_map(list(by_format.keys()))
    medium_slugs = unique_slug_map(list(by_medium.keys()))

    for pub in pubs:
        write(
            OUT_DIR / "publications" / publication_filename(pub),
            publication_page(pub, timestamp, city_slugs, decade_slugs, format_slugs, medium_slugs, by_city, by_decade),
        )

    write_group("cities", by_city, timestamp, city_slugs)
    write_group("decades", by_decade, timestamp, decade_slugs)
    write_group("formats", by_format, timestamp, format_slugs)
    write_group("mediums", by_medium, timestamp, medium_slugs)

    write_group_index("cities", by_city, timestamp, city_slugs)
    write_group_index("decades", by_decade, timestamp, decade_slugs)
    write_group_index("formats", by_format, timestamp, format_slugs)
    write_group_index("mediums", by_medium, timestamp, medium_slugs)

    active = sum(1 for p in pubs if p.get("isActive"))

    # Home / index.
    index = frontmatter(type="index", title="NJ Black Press archive wiki", description="Open knowledge format entry point for the archive wiki.", tags=["nj-black-press", "okf", "wiki"], timestamp=timestamp)
    index += "# NJ Black Press archive wiki\n\n"
    index += "This open knowledge format wiki gives humans and agents a file-based map of the NJ Black Press archive. Each page is markdown with YAML frontmatter and standard markdown links, generated from `data/publications.json`.\n\n"
    index += "## Start here\n\n"
    index += "- [Archive overview](archive-overview.md) — scope and how the wiki is built\n"
    index += "- [Archive statistics](statistics.md) — counts, decade timeline, top cities\n"
    index += "- [Featured publications](featured.md) — curated historic and contemporary records\n"
    index += "- [Data model](data-model.md) — field guide for publication pages\n\n"
    index += "## Browse\n\n"
    index += "- [Publication index](publications.md) — every record, with city, years, and status\n"
    index += "- [City index](cities.md)\n- [Decade index](decades.md)\n- [Format index](formats.md)\n- [Medium index](mediums.md)\n- [Change log](log.md)\n\n"
    index += "## Snapshot\n\n"
    index += (
        f"- Publication records: {len(pubs)}\n"
        f"- Active records: {active}\n"
        f"- Cities: {len(by_city)}\n"
        f"- Founding span: {year_range(pubs)}\n"
        f"- Date generated: {timestamp}\n"
    )
    write(OUT_DIR / "index.md", index)

    # Archive overview.
    format_counts = Counter(clean(p.get("format")) or "Unknown" for p in pubs)
    cat_counts: Counter[str] = Counter()
    for pub in pubs:
        cat_counts[format_category(clean(pub.get("format")) or "Unknown")] += 1
    overview = frontmatter(type="overview", title="Archive overview", description="Summary of the NJ Black Press archive scope and wiki structure.", tags=["nj-black-press", "archive"], timestamp=timestamp)
    overview += "# Archive overview\n\nThe archive documents Black-owned and Black-focused publications connected to New Jersey from 1880 to the present. It includes newspapers, magazines, newsletters, journals, and digital outlets.\n\n"
    overview += "## Wiki structure\n\n"
    overview += "- One publication record per file under `publications/`.\n"
    overview += "- City, decade, format, and medium pages group records for browsing.\n"
    overview += "- `statistics.md` summarizes counts and trends; `featured.md` lists curated records.\n"
    overview += "- `data-model.md` explains the fields on each publication page.\n"
    overview += "- `log.md` records generation notes.\n\n"
    overview += "## Format categories\n\n"
    overview += "Records carry a free-text `format`; these collapse into broad categories:\n\n"
    overview += "\n".join(f"- {name}: {count}" for name, count in cat_counts.most_common()) + "\n\n"
    overview += "## Every format string\n\n"
    overview += "\n".join(f"- {name}: {count}" for name, count in sorted(format_counts.items())) + "\n"
    write(OUT_DIR / "archive-overview.md", overview)

    # Data model.
    data_model = frontmatter(type="schema", title="Data model", description="Field guide for the publication records used by the wiki.", tags=["nj-black-press", "schema", "data"], timestamp=timestamp)
    data_model += "# Data model\n\nPublication pages are generated from `data/publications.json`. Source values are preserved as written; empty values render as `Unknown` in tables.\n\n"
    data_model += "## Fields\n\n| Field | Origin | Description |\n|---|---|---|\n"
    for field, desc, origin in FIELD_DOCS:
        data_model += f"| `{field}` | {origin} | {markdown_cell(desc)} |\n"
    data_model += "\n_Origin `source` comes straight from the dataset; `computed` is derived during the data pipeline._\n"
    write(OUT_DIR / "data-model.md", data_model)

    # Statistics + featured.
    write(OUT_DIR / "statistics.md", build_statistics(pubs, by_city, by_decade, by_format, by_medium, timestamp, city_slugs, decade_slugs))
    write(OUT_DIR / "featured.md", build_featured(pubs, timestamp))

    # Publication index as a rich table.
    pub_index = frontmatter(type="index", title="Publication index", description="Index of every publication wiki record with city, years, and status.", tags=["nj-black-press", "publications"], timestamp=timestamp)
    pub_index += "# Publication index\n\n"
    pub_index += f"All {len(pubs)} records, alphabetical. See [statistics](statistics.md) for breakdowns.\n\n"
    pub_index += "| Publication | City | Years | Status |\n|---|---|---|---|\n"
    for pub in sorted(pubs, key=lambda p: (p.get("name") or "").lower()):
        link = markdown_link(f"publications/{publication_filename(pub)}", pub["name"])
        city = clean(pub.get("city")) or "Unknown"
        star = " ⭐" if featured_kind(pub) else ""
        pub_index += f"| {link}{star} | {markdown_cell(city)} | {markdown_cell(life_span(pub))} | {markdown_cell(status_label(pub))} |\n"
    write(OUT_DIR / "publications.md", pub_index)

    # Change log.
    total_files = len(list(OUT_DIR.rglob('*.md'))) + 1
    log = frontmatter(type="log", title="Wiki change log", description="Generation log for the open knowledge format wiki.", tags=["nj-black-press", "okf", "log"], timestamp=timestamp)
    log += "# Wiki change log\n\n"
    log += f"- {timestamp}: Generated the open knowledge format wiki bundle from `data/publications.json` with {len(pubs)} publication pages and {total_files} markdown files in total.\n"
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
    medium_count = len({clean(pub.get("medium")) or "Unknown" for pub in pubs})
    # Fixed top-level pages: index, archive-overview, data-model, statistics,
    # featured, log, publications.md, cities.md, decades.md, formats.md, mediums.md.
    fixed_pages = 11
    expected_total = len(pubs) + city_count + decade_count + format_count + medium_count + fixed_pages

    if len(publication_files) != len(pubs):
        raise SystemExit(f"expected {len(pubs)} publication files, found {len(publication_files)}")
    if len(files) != expected_total:
        raise SystemExit(f"expected {expected_total} markdown files, found {len(files)}")
    if missing_type:
        names = ", ".join(str(path) for path in missing_type[:5])
        raise SystemExit(f"missing type frontmatter: {names}")

    # Guard against the singularization bug regressing.
    bad = [p for p in files if '\ntype: "citie"' in p.read_text(encoding="utf-8")]
    if bad:
        raise SystemExit(f"invalid singular type frontmatter in {len(bad)} files")
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
