import csv
import json
import re

def parse_year(year_str):
    """Extract year as integer from various formats."""
    if not year_str or year_str.strip() in ['', '?', 'Unknown']:
        return None
    # Extract first 4-digit number
    match = re.search(r'(\d{4})', str(year_str))
    if match:
        return int(match.group(1))
    return None

def get_decade(year):
    """Get decade string from year."""
    if year is None:
        return "Unknown"
    decade_start = (year // 10) * 10
    return f"{decade_start}s"

def determine_medium(medium_str, format_str):
    """Determine if Print, Digital, or Print/Digital."""
    if not medium_str:
        medium_str = ""
    if not format_str:
        format_str = ""

    medium_lower = medium_str.lower()
    format_lower = format_str.lower()

    has_digital = any(x in medium_lower or x in format_lower for x in ['online', 'digital', 'website', 'multimedia'])
    has_print = any(x in medium_lower for x in ['print'])

    if has_digital and has_print:
        return "Print/Digital"
    elif has_digital:
        return "Digital"
    else:
        return "Print"

# Featured publications lists
featured_historic = [
    "The Sentinel", "New Jersey Trumpet", "The New Jersey Guardian",
    "Newark Herald", "Black Newark", "Unity and Struggle", "The Black Voice",
    "Black Women's United Front Newsletter", "The Echo", "New Jersey Afro-American"
]

featured_contemporary = [
    "Trenton Journal", "New Jersey Urban News", "NJ Urban News", "Ark Republic", "The Nubian News", "Black In Jersey"
]

def is_featured_historic(name):
    if not name:
        return False
    name_clean = name.strip()
    for featured in featured_historic:
        if featured.lower() in name_clean.lower() or name_clean.lower() in featured.lower():
            return True
    return False

def is_featured_contemporary(name):
    if not name:
        return False
    name_clean = name.strip()
    for featured in featured_contemporary:
        if featured.lower() in name_clean.lower() or name_clean.lower() in featured.lower():
            return True
    return False

publications = []
cities = set()
decades = set()
formats = set()

with open('publications.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pub_id = row.get('ID', '').strip()
        if not pub_id or not pub_id.isdigit():
            continue

        name = row.get('Publication', '').strip() or None
        if not name:
            continue

        alternate_name = row.get('Alternate Name', '').strip() or None
        city = row.get('Location (City)', '').strip() or None
        publishers = row.get('Owners/Publishers', '').strip() or None
        year_founded = parse_year(row.get('Year founded', ''))
        year_ceased = parse_year(row.get('Year ceased', ''))
        frequency = row.get('Frequency of publication', '').strip() or None
        format_val = row.get('Format', '').strip() or None
        languages = row.get('Languages published', '').strip() or "English"
        archive_url = row.get('Archive/Call Number', '').strip() or None
        website_url = row.get('Website/Archive', '').strip() or None
        target_audience = row.get('HMerge:Target audience', '').strip() or None
        primary_focus = row.get('Primary focus/Content areas', '').strip() or None
        medium_raw = row.get('Medium/Distribution method (e.g. Print, Digital)', '').strip()
        medium = determine_medium(medium_raw, format_val)
        mission_statement = row.get('Mission statement or editorial philosophy', '').strip() or None
        key_staff = row.get('Key staff members', '').strip() or None
        historical_notes = row.get('Historical notes + impact', '').strip() or None

        # Determine if active
        year_ceased_raw = row.get('Year ceased', '').strip()
        is_active = year_ceased_raw in ['', '?', None] or year_ceased is None

        decade = get_decade(year_founded)

        pub = {
            "id": int(pub_id),
            "name": name,
            "alternateName": alternate_name,
            "city": city,
            "publishers": publishers,
            "yearFounded": year_founded,
            "yearCeased": year_ceased,
            "frequency": frequency,
            "format": format_val,
            "languages": languages,
            "archiveUrl": archive_url,
            "websiteUrl": website_url,
            "targetAudience": target_audience,
            "primaryFocus": primary_focus,
            "medium": medium,
            "missionStatement": mission_statement,
            "keyStaff": key_staff,
            "historicalNotes": historical_notes,
            "isActive": is_active,
            "decade": decade,
            "isFeaturedHistoric": is_featured_historic(name),
            "isFeaturedContemporary": is_featured_contemporary(name)
        }

        publications.append(pub)

        if city:
            cities.add(city)
        if decade != "Unknown":
            decades.add(decade)
        if format_val:
            formats.add(format_val)

# Sort publications by ID
publications.sort(key=lambda x: x['id'])

# Calculate counts
active_count = sum(1 for p in publications if p['isActive'])
ceased_count = len(publications) - active_count

# Sort metadata arrays
cities_list = sorted(list(cities))
decades_list = sorted(list(decades), key=lambda x: int(x[:-1]) if x != "Unknown" else 9999)
formats_list = sorted(list(formats))

output = {
    "metadata": {
        "totalCount": len(publications),
        "cities": cities_list,
        "decades": decades_list,
        "formats": formats_list,
        "activeCount": active_count,
        "ceasedCount": ceased_count
    },
    "publications": publications
}

with open('publications.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Generated publications.json with {len(publications)} publications")
print(f"Active: {active_count}, Ceased: {ceased_count}")
print(f"Cities: {len(cities_list)}, Decades: {len(decades_list)}, Formats: {len(formats_list)}")
