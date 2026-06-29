#!/usr/bin/env python3
"""Generate the public, browsable HTML wiki under ``docs/wiki/``.

Pre-renders one styled HTML page per publication, city, decade, format, and
medium (plus index, statistics, and featured pages) from
``data/publications.json``. Pages match the main site's look — ink/paper/accent
palette, Fraunces + DM Sans, shared nav and footer — and use real relative URLs
so every record is a crawlable permalink at ``/njblackpress/wiki/``.

Shares data-shaping helpers with ``generate_okf_wiki.py`` so the HTML and the
portable markdown bundle stay in lockstep.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter, defaultdict
from datetime import date
from html import escape as esc
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_okf_wiki import (  # noqa: E402  (local sibling module)
    DECADE_CONTEXT,
    FIELD_DOCS,
    as_link_url,
    clean,
    featured_kind,
    format_category,
    life_span,
    load_publications,
    slugify,
    status_label,
    unique_slug_map,
    year_range,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "wiki"
SITE_BASE = "https://centercoopmedia.github.io/njblackpress/"

GROUP_LABEL = {"cities": "City", "decades": "Decade", "formats": "Format", "mediums": "Medium"}


def pub_html_name(pub: dict[str, Any]) -> str:
    return f"{pub['id']:03d}-{slugify(pub['name'])}.html"


# --- shared chrome -----------------------------------------------------------

def shell(*, title: str, description: str, depth: int, body: str, canonical_rel: str) -> str:
    """Wrap page ``body`` in the site's head, nav, and footer.

    ``depth`` is how many directories below ``docs/wiki/`` the page lives:
    0 for top-level wiki pages, 1 for ``cities/x.html`` etc.
    """
    a = "../" * (depth + 1)  # reach docs/ root for shared assets
    w = "../" * depth        # reach docs/wiki/ root for wiki links
    canonical = SITE_BASE + "wiki/" + canonical_rel
    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{esc(description)}">
    <meta name="author" content="Center for Cooperative Media">
    <meta property="og:title" content="{esc(title)} | NJ Black Press Wiki">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{esc(canonical)}">
    <meta property="og:image" content="{SITE_BASE}og-image.png">
    <meta property="og:site_name" content="NJ Black Press Archive">
    <meta name="twitter:card" content="summary_large_image">
    <title>{esc(title)} | NJ Black Press Wiki</title>
    <link rel="canonical" href="{esc(canonical)}">
    <link rel="icon" type="image/svg+xml" href="{a}favicon.svg">
    <link rel="icon" type="image/png" href="{a}favicon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;400;500;600;700&family=Fraunces:opsz,wght@9..144,300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{ extend: {{
                colors: {{
                    ink: {{ 950: '#050505', 900: '#0a0a0a', 800: '#121212', 700: '#1a1a1a', 600: '#262626' }},
                    paper: {{ 50: '#faf9f6', 100: '#f4f1ea', 200: '#e5e2db', 300: '#d1cdc5' }},
                    accent: {{ DEFAULT: '#ff4d00', hover: '#cc3d00', light: '#ff7a40' }}
                }},
                fontFamily: {{
                    'serif': ['Fraunces', 'serif'],
                    'sans': ['DM Sans', 'sans-serif'],
                    'mono': ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
                }},
                backgroundImage: {{
                    'noise': "url('data:image/svg+xml,%3Csvg viewBox=\\"0 0 200 200\\" xmlns=\\"http://www.w3.org/2000/svg\\"%3E%3Cfilter id=\\"noiseFilter\\"%3E%3CfeTurbulence type=\\"fractalNoise\\" baseFrequency=\\"0.65\\" numOctaves=\\"3\\" stitchTiles=\\"stitch\\"/%3E%3C/filter%3E%3Crect width=\\"100%25\\" height=\\"100%25\\" filter=\\"url(%23noiseFilter)\\" opacity=\\"0.05\\"/%3E%3C/svg%3E')",
                }}
            }} }}
        }}
    </script>
    <link rel="stylesheet" href="{a}css/styles.css">
</head>
<body class="bg-ink-900 text-paper-100 font-sans selection:bg-accent selection:text-white antialiased">
    <div class="fixed inset-0 bg-noise pointer-events-none z-50 opacity-20 mix-blend-overlay"></div>

    <nav class="fixed top-0 w-full z-40 bg-ink-900/90 backdrop-blur-sm border-b border-white/10">
        <div class="max-w-[1400px] mx-auto px-4 md:px-8 h-20 flex items-center justify-between">
            <a href="{w}index.html" class="flex items-center gap-2 group">
                <img src="{a}njblackpress-icon.png" alt="NJ Black Press" class="w-8 h-8 transition-transform group-hover:rotate-12">
                <span class="font-serif font-bold text-lg tracking-tight group-hover:text-accent transition-colors">NJ Black Press <span class="text-accent">Wiki</span></span>
            </a>
            <ul class="hidden md:flex items-center gap-8 font-mono text-xs uppercase tracking-widest">
                <li><a href="{w}index.html" class="hover:text-accent transition-colors">Wiki home</a></li>
                <li><a href="{w}publications.html" class="hover:text-accent transition-colors">Publications</a></li>
                <li><a href="{w}statistics.html" class="hover:text-accent transition-colors">Statistics</a></li>
                <li><a href="{a}archive.html" class="hover:text-accent transition-colors">Archive</a></li>
                <li><a href="{a}index.html" class="hover:text-accent transition-colors">Main site</a></li>
            </ul>
            <a href="{w}index.html" class="md:hidden font-mono text-xs uppercase tracking-widest text-accent">Wiki</a>
        </div>
    </nav>

    <main class="pt-28 md:pt-32 pb-20 px-4 md:px-8">
        <div class="max-w-[1100px] mx-auto">
{body}
        </div>
    </main>

    <footer class="bg-ink-900 border-t border-white/10 pt-12 pb-10 px-4 md:px-8">
        <div class="max-w-[1100px] mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-mono text-paper-300 uppercase tracking-wider">
            <div class="flex items-center gap-4">
                <a href="https://centerforcooperativemedia.org" target="_blank" rel="noopener noreferrer">
                    <img src="{a}favicon.png" alt="CCM" class="h-8 w-auto opacity-70 hover:opacity-100 transition-opacity">
                </a>
                <p>&copy; {date.today().year} Center for Cooperative Media</p>
            </div>
            <div class="flex gap-6">
                <a href="{a}index.html" class="hover:text-accent">Main site</a>
                <a href="{a}archive.html" class="hover:text-accent">Archive</a>
                <a href="https://github.com/CenterCoopMedia/njblackpress" target="_blank" rel="noopener noreferrer" class="hover:text-accent">GitHub</a>
            </div>
        </div>
    </footer>
</body>
</html>
"""


# --- components --------------------------------------------------------------

def crumbs(items: list[tuple[str, str | None]]) -> str:
    parts = []
    for label, href in items:
        if href:
            parts.append(f'<a href="{esc(href)}" class="hover:text-accent transition-colors">{esc(label)}</a>')
        else:
            parts.append(f'<span class="text-paper-100">{esc(label)}</span>')
    sep = '<span class="text-paper-300/40">/</span>'
    return f'<nav class="font-mono text-xs uppercase tracking-widest text-paper-300 flex flex-wrap items-center gap-3 mb-8">{sep.join(parts)}</nav>'


def kicker(text: str) -> str:
    return f'<p class="font-mono text-accent text-xs uppercase tracking-widest mb-4 border-l-2 border-accent pl-3">{esc(text)}</p>'


def page_title(text: str) -> str:
    return f'<h1 class="font-serif text-4xl md:text-6xl font-black tracking-tighter mb-6 leading-[0.95]">{esc(text)}</h1>'


def section_title(text: str) -> str:
    return f'<h2 class="font-serif text-2xl md:text-3xl font-bold mb-6 mt-12">{esc(text)}</h2>'


def status_pill(pub: dict[str, Any]) -> str:
    if pub.get("isActive"):
        return '<span class="inline-block font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full bg-accent/15 text-accent border border-accent/30">Active</span>'
    return '<span class="inline-block font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/5 text-paper-300 border border-white/10">Ceased</span>'


def pub_card(pub: dict[str, Any], depth: int, wiki_root: str) -> str:
    href = f"{wiki_root}publications/{pub_html_name(pub)}"
    city = esc(clean(pub.get("city")) or "Unknown")
    star = ' <span class="text-accent">&#9733;</span>' if featured_kind(pub) else ""
    return (
        f'<a href="{esc(href)}" class="group block border border-white/10 bg-ink-950 p-5 hover:border-accent/60 hover:bg-ink-800 transition-colors">'
        f'<div class="flex items-start justify-between gap-3 mb-2">'
        f'<h3 class="font-serif text-lg font-bold leading-snug group-hover:text-accent transition-colors">{esc(pub["name"])}{star}</h3>'
        f'{status_pill(pub)}</div>'
        f'<p class="font-mono text-xs uppercase tracking-widest text-paper-300">{city} &middot; {esc(life_span(pub))}</p>'
        f'</a>'
    )


def pub_grid(pubs: list[dict[str, Any]], depth: int, wiki_root: str) -> str:
    cards = "\n".join(pub_card(p, depth, wiki_root) for p in pubs)
    return f'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{cards}</div>'


def browse_card(href: str, title: str, sub: str) -> str:
    return (
        f'<a href="{esc(href)}" class="group flex flex-col justify-between border border-white/10 bg-ink-950 p-6 hover:border-accent/60 hover:bg-ink-800 transition-colors min-h-[120px]">'
        f'<span class="font-serif text-xl font-bold group-hover:text-accent transition-colors">{esc(title)}</span>'
        f'<span class="font-mono text-xs uppercase tracking-widest text-paper-300 mt-3">{esc(sub)} <span class="group-hover:translate-x-1 inline-block transition-transform">&rarr;</span></span>'
        f'</a>'
    )


# --- page bodies -------------------------------------------------------------

def landing_body(pubs, by_city, by_decade, by_format, by_medium, slugs, timestamp) -> str:
    active = sum(1 for p in pubs if p.get("isActive"))
    featured = [p for p in pubs if featured_kind(p)]
    b = kicker("Open archive wiki")
    b += page_title("The NJ Black Press archive, page by page")
    b += (
        '<p class="text-lg md:text-xl text-paper-300 font-light leading-relaxed max-w-2xl mb-10 border-l border-white/10 pl-5">'
        'A browsable companion to the database: one page per publication, cross-linked by city, decade, format, and medium, '
        'with statistics and curated highlights. Built for readers, researchers, and machines alike.</p>'
    )
    # snapshot
    stats = [
        ("Publications", str(len(pubs))),
        ("Active today", str(active)),
        ("Cities", str(len(by_city))),
        ("Founding span", year_range(pubs)),
    ]
    cells = "".join(
        f'<div class="border border-white/10 bg-ink-950 p-5"><div class="font-serif text-3xl text-accent">{esc(v)}</div>'
        f'<div class="font-mono text-[11px] uppercase tracking-widest text-paper-300 mt-1">{esc(k)}</div></div>'
        for k, v in stats
    )
    b += f'<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{cells}</div>'

    b += section_title("Browse the archive")
    browse = [
        ("publications.html", "All publications", f"{len(pubs)} records"),
        ("cities.html", "By city", f"{len(by_city)} places"),
        ("decades.html", "By decade", f"{len(by_decade)} decades"),
        ("formats.html", "By format", f"{len(by_format)} formats"),
        ("mediums.html", "By medium", f"{len(by_medium)} mediums"),
        ("statistics.html", "Statistics", "Counts & trends"),
        ("featured.html", "Featured", f"{len(featured)} curated"),
        ("../archive.html", "Search archive", "Full database"),
    ]
    b += '<div class="grid grid-cols-2 md:grid-cols-4 gap-4">'
    b += "".join(browse_card(h, t, s) for h, t, s in browse)
    b += "</div>"

    # featured preview
    if featured:
        b += section_title("Featured publications")
        b += pub_grid(sorted(featured, key=lambda p: p.get("yearFounded") or 9999)[:6], 0, "")
        b += '<p class="mt-4 font-mono text-xs uppercase tracking-widest"><a href="featured.html" class="text-accent hover:text-white transition-colors">See all featured &rarr;</a></p>'

    b += f'<p class="mt-16 font-mono text-[11px] uppercase tracking-widest text-paper-300/60">Generated {esc(timestamp)} from data/publications.json</p>'
    return b


def detail_body(pub, depth, wiki_root, city_slugs, decade_slugs, format_slugs, medium_slugs, by_city, by_decade) -> str:
    name = clean(pub.get("name"))
    city = clean(pub.get("city")) or "Unknown"
    decade = clean(pub.get("decade")) or "Unknown"
    fmt = clean(pub.get("format")) or "Unknown"
    medium = clean(pub.get("medium")) or "Unknown"
    feat = featured_kind(pub)

    b = crumbs([("Wiki", f"{wiki_root}index.html"), ("Publications", f"{wiki_root}publications.html"), (name, None)])
    b += kicker(f"{city} · {decade}")
    b += f'<h1 class="font-serif text-4xl md:text-6xl font-black tracking-tighter mb-4 leading-[0.95]">{esc(name)}</h1>'
    b += f'<div class="flex flex-wrap items-center gap-3 mb-8">{status_pill(pub)}'
    if feat:
        b += f'<span class="inline-block font-mono text-[10px] uppercase tracking-widest px-2 py-0.5 rounded-full bg-accent/15 text-accent border border-accent/30">Featured {esc(feat)}</span>'
    b += "</div>"

    rows = [
        ("Alternate name", esc(clean(pub.get("alternateName")) or "—")),
        ("City", f'<a href="{wiki_root}cities/{city_slugs[city]}.html" class="text-accent hover:text-white transition-colors">{esc(city)}</a>'),
        ("Publishers / owners", esc(clean(pub.get("publishers")) or "—")),
        ("Active years", esc(life_span(pub))),
        ("Status", esc(status_label(pub))),
        ("Decade", f'<a href="{wiki_root}decades/{decade_slugs[decade]}.html" class="text-accent hover:text-white transition-colors">{esc(decade)}</a>'),
        ("Format", f'<a href="{wiki_root}formats/{format_slugs[fmt]}.html" class="text-accent hover:text-white transition-colors">{esc(fmt)}</a>'),
        ("Medium", f'<a href="{wiki_root}mediums/{medium_slugs[medium]}.html" class="text-accent hover:text-white transition-colors">{esc(medium)}</a>'),
        ("Frequency", esc(clean(pub.get("frequency")) or "—")),
        ("Languages", esc(clean(pub.get("languages")) or "—")),
        ("Primary focus", esc(clean(pub.get("primaryFocus")) or "—")),
        ("Target audience", esc(clean(pub.get("targetAudience")) or "—")),
    ]
    row_html = "".join(
        f'<div class="grid grid-cols-3 gap-4 py-3 border-b border-white/10">'
        f'<dt class="font-mono text-[11px] uppercase tracking-widest text-paper-300 pt-1">{k}</dt>'
        f'<dd class="col-span-2 text-paper-100">{v}</dd></div>'
        for k, v in rows
    )
    b += f'<dl class="mb-4">{row_html}</dl>'

    for heading, key in [("Mission statement", "missionStatement"), ("Key staff", "keyStaff"), ("Historical notes", "historicalNotes")]:
        value = clean(pub.get(key))
        if value:
            b += section_title(heading)
            b += f'<p class="text-lg text-paper-200 font-light leading-relaxed max-w-3xl">{esc(value)}</p>'

    archive_url = as_link_url(pub.get("archiveUrl"))
    website_url = as_link_url(pub.get("websiteUrl"))
    archive_ref = clean(pub.get("archiveUrl"))
    links = []
    if archive_url:
        links.append((archive_url, "Archive record"))
    if website_url:
        links.append((website_url, "Website"))
    if links or (archive_ref and not archive_url):
        b += section_title("Archive & links")
        b += '<div class="flex flex-wrap items-center gap-3">'
        for url, label in links:
            b += (f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer" '
                  f'class="inline-flex items-center gap-2 border border-white/15 px-4 py-2 font-mono text-xs uppercase tracking-widest hover:border-accent hover:text-accent transition-colors">{esc(label)} &nearr;</a>')
        if archive_ref and not archive_url:
            b += (f'<span class="inline-flex items-center gap-2 border border-white/10 bg-ink-950 px-4 py-2 font-mono text-xs text-paper-300">'
                  f'<span class="uppercase tracking-widest text-paper-300/60">Catalog</span> {esc(archive_ref)}</span>')
        b += "</div>"

    def siblings(group, limit=6):
        others = sorted((p for p in group if p["id"] != pub["id"]), key=lambda p: p.get("yearFounded") or 9999)
        return others[:limit]

    city_sib = siblings(by_city.get(city, []))
    decade_sib = siblings(by_decade.get(decade, []))
    if city_sib or decade_sib:
        b += section_title("Related publications")
        if city_sib:
            b += f'<h3 class="font-mono text-xs uppercase tracking-widest text-paper-300 mb-3 mt-2">Also in {esc(city)}</h3>'
            b += pub_grid(city_sib, depth, wiki_root)
        if decade_sib:
            b += f'<h3 class="font-mono text-xs uppercase tracking-widest text-paper-300 mb-3 mt-6">Also from the {esc(decade)}</h3>'
            b += pub_grid(decade_sib, depth, wiki_root)
    return b


def group_detail_body(kind, name, items, depth, wiki_root, slug) -> str:
    singular = GROUP_LABEL[kind]
    active = sum(1 for p in items if p.get("isActive"))
    b = crumbs([("Wiki", f"{wiki_root}index.html"), (f"{singular} index", f"{wiki_root}{kind}.html"), (name, None)])
    b += kicker(f"{singular} grouping")
    b += page_title(name)
    if kind == "decades" and name in DECADE_CONTEXT:
        b += f'<p class="text-lg text-paper-300 font-light italic mb-6 max-w-2xl">{esc(DECADE_CONTEXT[name])}</p>'
    b += (f'<p class="font-mono text-xs uppercase tracking-widest text-paper-300 mb-10">'
          f'{len(items)} publications &middot; {active} active &middot; founding years {esc(year_range(items))}</p>')
    ordered = sorted(items, key=lambda p: (p.get("yearFounded") or 9999, p.get("name") or ""))
    b += pub_grid(ordered, depth, wiki_root)
    return b


def group_index_body(kind, groups, slugs, depth) -> str:
    singular = GROUP_LABEL[kind]
    total = sum(len(v) for v in groups.values())
    b = crumbs([("Wiki", "index.html"), (f"{singular} index", None)])
    b += kicker("Browse")
    b += page_title(f"{singular} index")
    b += f'<p class="font-mono text-xs uppercase tracking-widest text-paper-300 mb-10">{len(groups)} {kind} &middot; {total} records</p>'

    if kind == "decades":
        names = sorted(groups, key=lambda n: (n == "Unknown", n))
    else:
        names = sorted(groups, key=lambda n: (-len(groups[n]), n))

    items = ""
    for name in names:
        active = sum(1 for p in groups[name] if p.get("isActive"))
        sub = f"{len(groups[name])} records" + (f" · {active} active" if active else "")
        items += browse_card(f"{kind}/{slugs[name]}.html", name, sub)
    b += f'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{items}</div>'
    return b


def publications_index_body(pubs, depth) -> str:
    b = crumbs([("Wiki", "index.html"), ("Publications", None)])
    b += kicker("Browse")
    b += page_title("All publications")
    b += f'<p class="font-mono text-xs uppercase tracking-widest text-paper-300 mb-10">{len(pubs)} records, alphabetical</p>'
    rows = ""
    for pub in sorted(pubs, key=lambda p: (p.get("name") or "").lower()):
        star = ' <span class="text-accent">&#9733;</span>' if featured_kind(pub) else ""
        city = esc(clean(pub.get("city")) or "Unknown")
        rows += (
            f'<tr class="border-b border-white/10 hover:bg-ink-800 transition-colors">'
            f'<td class="py-3 pr-4"><a href="publications/{pub_html_name(pub)}" class="font-serif text-base hover:text-accent transition-colors">{esc(pub["name"])}{star}</a></td>'
            f'<td class="py-3 pr-4 text-paper-300 text-sm">{city}</td>'
            f'<td class="py-3 pr-4 font-mono text-xs text-paper-300 whitespace-nowrap">{esc(life_span(pub))}</td>'
            f'<td class="py-3 text-right">{status_pill(pub)}</td>'
            f'</tr>'
        )
    b += ('<div class="overflow-x-auto border border-white/10 bg-ink-950"><table class="w-full text-left">'
          '<thead><tr class="font-mono text-[10px] uppercase tracking-widest text-paper-300 border-b border-white/15">'
          '<th class="py-3 px-4">Publication</th><th class="py-3 pr-4">City</th><th class="py-3 pr-4">Years</th><th class="py-3 px-4 text-right">Status</th></tr></thead>'
          f'<tbody class="px-4">{rows}</tbody></table></div>')
    # offset table cell padding (thead has px-4, body uses py-3 pr-4) — wrap in padded container
    return b.replace('<tbody class="px-4">', '<tbody>')


def statistics_body(pubs, by_city, by_decade, by_format, by_medium, slugs, timestamp) -> str:
    total = len(pubs)
    active = sum(1 for p in pubs if p.get("isActive"))
    b = crumbs([("Wiki", "index.html"), ("Statistics", None)])
    b += kicker("By the numbers")
    b += page_title("Archive statistics")

    stats = [("Records", str(total)), ("Active", str(active)), ("Ceased", str(total - active)),
             ("Cities", str(len(by_city))), ("Formats", str(len(by_format))), ("Span", year_range(pubs))]
    cells = "".join(
        f'<div class="border border-white/10 bg-ink-950 p-4"><div class="font-serif text-2xl text-accent">{esc(v)}</div>'
        f'<div class="font-mono text-[10px] uppercase tracking-widest text-paper-300 mt-1">{esc(k)}</div></div>'
        for k, v in stats
    )
    b += f'<div class="grid grid-cols-3 lg:grid-cols-6 gap-3 mb-4">{cells}</div>'

    # decade bar chart
    b += section_title("Publications by founding decade")
    order = sorted(by_decade, key=lambda n: (n == "Unknown", n))
    mx = max((len(v) for v in by_decade.values()), default=1)
    bars = ""
    for dec in order:
        items = by_decade[dec]
        pct = round(len(items) / mx * 100)
        bars += (
            f'<a href="decades/{slugs["decades"][dec]}.html" class="group block">'
            f'<div class="flex items-center gap-3 py-1">'
            f'<span class="w-16 shrink-0 font-mono text-xs text-paper-300 group-hover:text-accent transition-colors text-right">{esc(dec)}</span>'
            f'<span class="flex-1 h-5 bg-white/5 relative">'
            f'<span class="absolute inset-y-0 left-0 bg-accent/70 group-hover:bg-accent transition-colors" style="width:{pct}%"></span></span>'
            f'<span class="w-8 shrink-0 font-mono text-xs text-paper-300 text-right">{len(items)}</span>'
            f'</div></a>'
        )
    b += f'<div class="border border-white/10 bg-ink-950 p-5">{bars}</div>'

    # top cities
    b += section_title("Cities by publication count")
    ranked = sorted(by_city.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:15]
    rows = ""
    for name, items in ranked:
        ca = sum(1 for p in items if p.get("isActive"))
        rows += (f'<tr class="border-b border-white/10 hover:bg-ink-800 transition-colors">'
                 f'<td class="py-2.5 pr-4"><a href="cities/{slugs["cities"][name]}.html" class="hover:text-accent transition-colors">{esc(name)}</a></td>'
                 f'<td class="py-2.5 pr-4 font-mono text-sm text-right">{len(items)}</td>'
                 f'<td class="py-2.5 font-mono text-sm text-right text-paper-300">{ca}</td></tr>')
    b += ('<div class="border border-white/10 bg-ink-950 p-2"><table class="w-full text-left">'
          '<thead><tr class="font-mono text-[10px] uppercase tracking-widest text-paper-300 border-b border-white/15">'
          '<th class="py-2 px-2">City</th><th class="py-2 pr-4 text-right">Records</th><th class="py-2 text-right">Active</th></tr></thead>'
          f'<tbody class="px-2">{rows}</tbody></table></div>')
    singles = sum(1 for v in by_city.values() if len(v) == 1)
    b += f'<p class="mt-3 font-mono text-xs text-paper-300">{singles} cities have a single recorded publication. <a href="cities.html" class="text-accent hover:text-white transition-colors">Full city index &rarr;</a></p>'

    # medium + format categories side by side
    b += section_title("Medium & format")
    med = "".join(
        f'<div class="flex justify-between py-2 border-b border-white/10"><span>{esc(name)}</span><span class="font-mono text-paper-300">{len(items)}</span></div>'
        for name, items in sorted(by_medium.items(), key=lambda kv: -len(kv[1]))
    )
    cat_counts: Counter[str] = Counter()
    for pub in pubs:
        cat_counts[format_category(clean(pub.get("format")) or "Unknown")] += 1
    cats = "".join(
        f'<div class="flex justify-between py-2 border-b border-white/10"><span>{esc(name)}</span><span class="font-mono text-paper-300">{count}</span></div>'
        for name, count in cat_counts.most_common()
    )
    b += ('<div class="grid grid-cols-1 md:grid-cols-2 gap-8">'
          f'<div><h3 class="font-mono text-xs uppercase tracking-widest text-accent mb-2">Medium</h3>{med}</div>'
          f'<div><h3 class="font-mono text-xs uppercase tracking-widest text-accent mb-2">Format category</h3>{cats}</div></div>')

    # longest running
    def span_years(p):
        f, c = p.get("yearFounded"), p.get("yearCeased")
        if not f:
            return None
        end = c if c else date.fromisoformat(timestamp).year
        return end - f
    spans = sorted(((span_years(p), p) for p in pubs if span_years(p) is not None), key=lambda sp: -sp[0])[:10]
    b += section_title("Longest-running publications")
    rows = ""
    for span, pub in spans:
        rows += (f'<tr class="border-b border-white/10 hover:bg-ink-800 transition-colors">'
                 f'<td class="py-2.5 pr-4"><a href="publications/{pub_html_name(pub)}" class="hover:text-accent transition-colors">{esc(pub["name"])}</a></td>'
                 f'<td class="py-2.5 pr-4 font-mono text-xs text-paper-300 whitespace-nowrap">{esc(life_span(pub))}</td>'
                 f'<td class="py-2.5 font-mono text-sm text-right">{span} yrs</td></tr>')
    b += ('<div class="border border-white/10 bg-ink-950 p-2"><table class="w-full text-left">'
          f'<tbody>{rows}</tbody></table></div>')
    return b


def featured_body(pubs, depth) -> str:
    historic = [p for p in pubs if p.get("isFeaturedHistoric")]
    contemporary = [p for p in pubs if p.get("isFeaturedContemporary")]
    b = crumbs([("Wiki", "index.html"), ("Featured", None)])
    b += kicker("Curated")
    b += page_title("Featured publications")
    b += '<p class="text-lg text-paper-300 font-light max-w-2xl mb-8">Publications highlighted on the archive site for their historical or contemporary significance.</p>'
    b += section_title(f"Historic ({len(historic)})")
    b += pub_grid(sorted(historic, key=lambda p: p.get("yearFounded") or 9999), depth, "")
    b += section_title(f"Contemporary ({len(contemporary)})")
    b += pub_grid(sorted(contemporary, key=lambda p: p.get("yearFounded") or 9999), depth, "")
    return b


def data_model_body() -> str:
    b = crumbs([("Wiki", "index.html"), ("Data model", None)])
    b += kicker("Reference")
    b += page_title("Data model")
    b += '<p class="text-lg text-paper-300 font-light max-w-2xl mb-8">Every publication page is generated from <code class="font-mono text-paper-100">data/publications.json</code>. Source values are preserved as written; empty values render as a dash.</p>'
    rows = ""
    for field, desc, origin in FIELD_DOCS:
        pill = ('<span class="font-mono text-[10px] uppercase px-2 py-0.5 rounded-full bg-accent/15 text-accent border border-accent/30">computed</span>'
                if origin == "computed" else '<span class="font-mono text-[10px] uppercase px-2 py-0.5 rounded-full bg-white/5 text-paper-300 border border-white/10">source</span>')
        rows += (f'<tr class="border-b border-white/10">'
                 f'<td class="py-3 pr-4 font-mono text-sm text-accent whitespace-nowrap">{esc(field)}</td>'
                 f'<td class="py-3 pr-4">{pill}</td>'
                 f'<td class="py-3 text-paper-200">{esc(desc)}</td></tr>')
    b += ('<div class="overflow-x-auto border border-white/10 bg-ink-950 p-2"><table class="w-full text-left">'
          f'<tbody>{rows}</tbody></table></div>')
    return b


# --- build -------------------------------------------------------------------

def build(generated_at: str | None = None) -> None:
    pubs = load_publications()
    timestamp = generated_at or date.today().isoformat()
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    by_city: dict[str, list] = defaultdict(list)
    by_decade: dict[str, list] = defaultdict(list)
    by_format: dict[str, list] = defaultdict(list)
    by_medium: dict[str, list] = defaultdict(list)
    for pub in pubs:
        by_city[clean(pub.get("city")) or "Unknown"].append(pub)
        by_decade[clean(pub.get("decade")) or "Unknown"].append(pub)
        by_format[clean(pub.get("format")) or "Unknown"].append(pub)
        by_medium[clean(pub.get("medium")) or "Unknown"].append(pub)

    slugs = {
        "cities": unique_slug_map(list(by_city)),
        "decades": unique_slug_map(list(by_decade)),
        "formats": unique_slug_map(list(by_format)),
        "mediums": unique_slug_map(list(by_medium)),
    }
    groups = {"cities": by_city, "decades": by_decade, "formats": by_format, "mediums": by_medium}

    emitted: list[str] = []

    def emit(rel: str, title: str, desc: str, depth: int, body: str) -> None:
        path = OUT_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(shell(title=title, description=desc, depth=depth, body=body, canonical_rel=rel), encoding="utf-8")
        emitted.append(rel)

    # Landing + top-level pages (depth 0).
    emit("index.html", "Archive wiki", "Browsable wiki for the NJ Black Press archive — publications, cities, decades, and statistics.",
         0, landing_body(pubs, by_city, by_decade, by_format, by_medium, slugs, timestamp))
    emit("publications.html", "All publications", f"Index of all {len(pubs)} publications in the NJ Black Press archive.",
         0, publications_index_body(pubs, 0))
    emit("statistics.html", "Archive statistics", "Counts, decade timeline, and top cities for the NJ Black Press archive.",
         0, statistics_body(pubs, by_city, by_decade, by_format, by_medium, slugs, timestamp))
    emit("featured.html", "Featured publications", "Curated historic and contemporary publications from the NJ Black Press archive.",
         0, featured_body(pubs, 0))
    emit("data-model.html", "Data model", "Field guide for the NJ Black Press archive publication records.",
         0, data_model_body())

    # Group index pages (depth 0).
    for kind in ("cities", "decades", "formats", "mediums"):
        emit(f"{kind}.html", f"{GROUP_LABEL[kind]} index", f"Browse NJ Black Press publications by {GROUP_LABEL[kind].lower()}.",
             0, group_index_body(kind, groups[kind], slugs[kind], 0))

    # Group detail pages (depth 1).
    for kind in ("cities", "decades", "formats", "mediums"):
        for name, items in groups[kind].items():
            rel = f"{kind}/{slugs[kind][name]}.html"
            emit(rel, name, f"{len(items)} NJ Black Press publications in {name} ({GROUP_LABEL[kind].lower()}).",
                 1, group_detail_body(kind, name, items, 1, "../", "../"))

    # Publication detail pages (depth 1).
    for pub in pubs:
        rel = f"publications/{pub_html_name(pub)}"
        desc = clean(pub.get("historicalNotes")) or clean(pub.get("missionStatement")) or f"{clean(pub.get('name'))} — NJ Black Press archive record."
        emit(rel, clean(pub.get("name")), desc[:200], 1,
             detail_body(pub, 1, "../", slugs["cities"], slugs["decades"], slugs["formats"], slugs["mediums"], by_city, by_decade))

    # Wiki sitemap covering every generated page.
    base = SITE_BASE + "wiki/"
    urls = []
    for rel in sorted(emitted):
        loc = base if rel == "index.html" else base + rel
        urls.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{timestamp}</lastmod>\n    <changefreq>monthly</changefreq>\n  </url>")
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "\n".join(urls) + "\n</urlset>\n")
    (OUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    count = len(list(OUT_DIR.rglob("*.html")))
    print(f"generated {count} html wiki pages + sitemap in {OUT_DIR.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the public HTML wiki.")
    parser.add_argument("--generated-at", help="date string for reproducible output")
    args = parser.parse_args()
    build(args.generated_at)


if __name__ == "__main__":
    main()
