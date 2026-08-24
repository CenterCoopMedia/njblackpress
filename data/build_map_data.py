"""Build the browser map data from publication records and saved coordinates.

Run ``python3 data/build_map_data.py`` after changing either input file.
Use ``--check`` in tests or CI to confirm both generated copies are current.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "data" / "publications.json"
CENTERS_PATH = ROOT / "data" / "municipality-centers.json"
OUTPUT_PATHS = (
    ROOT / "data" / "map-publications.json",
    ROOT / "docs" / "data" / "map-publications.json",
)


def city_key(city: Any) -> str:
    """Give null city values a stable dictionary key."""
    return "__null__" if city is None else str(city)


def visible_in_decade(publication: dict[str, Any], start: int, end: int, as_of_year: int) -> bool:
    """Return true when the publication existed during any part of a decade."""
    founded = publication.get("yearFounded")
    ceased = publication.get("yearCeased")
    if not isinstance(founded, int):
        return False
    record_end = ceased if isinstance(ceased, int) else as_of_year
    return founded <= end and record_end >= start


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(publications_payload: dict[str, Any], centers_payload: dict[str, Any]) -> dict[str, Any]:
    metadata = centers_payload.get("metadata", {})
    as_of_year = metadata.get("asOfYear")
    if not isinstance(as_of_year, int):
        raise ValueError("municipality-centers.json metadata.asOfYear must be an integer")

    locations = centers_payload.get("locations", [])
    unmapped_values = centers_payload.get("unmappedCityValues", [])
    city_to_location: dict[str, dict[str, Any]] = {}
    city_to_unmapped: dict[str, dict[str, Any]] = {}
    ids: set[str] = set()

    for location in locations:
        location_id = location.get("id")
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        if not isinstance(location_id, str) or not location_id or location_id in ids:
            raise ValueError(f"Invalid or duplicate location id: {location_id!r}")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError(f"Location {location_id} needs numeric latitude and longitude")
        if not 38 <= latitude <= 42 or not -89 <= longitude <= -73:
            raise ValueError(f"Location {location_id} falls outside the supported map bounds")
        ids.add(location_id)
        for city in location.get("cityValues", []):
            key = city_key(city)
            if key in city_to_location:
                raise ValueError(f"City value is mapped twice: {city!r}")
            city_to_location[key] = location

    for item in unmapped_values:
        key = city_key(item.get("city"))
        if key in city_to_location or key in city_to_unmapped:
            raise ValueError(f"City value has conflicting map rules: {item.get('city')!r}")
        if not item.get("reason"):
            raise ValueError(f"Unmapped city value needs a reason: {item.get('city')!r}")
        city_to_unmapped[key] = item

    grouped: dict[str, list[dict[str, Any]]] = {location["id"]: [] for location in locations}
    unmapped: list[dict[str, Any]] = []
    source_publications = publications_payload.get("publications", [])
    for publication in source_publications:
        city = publication.get("city")
        key = city_key(city)
        record = {
            "id": publication["id"],
            "name": publication["name"],
            "city": city,
            "yearFounded": publication.get("yearFounded"),
            "yearCeased": publication.get("yearCeased"),
            "isActive": publication.get("isActive") is True,
        }
        location = city_to_location.get(key)
        if location:
            grouped[location["id"]].append(record)
            continue
        rule = city_to_unmapped.get(key)
        if not rule:
            raise ValueError(f"No map rule for publication city value: {city!r}")
        unmapped.append({**record, "reason": rule["reason"]})

    def publication_sort_key(publication: dict[str, Any]) -> tuple[int, str]:
        year = publication.get("yearFounded")
        return (year if isinstance(year, int) else 9999, publication["name"].casefold())

    rendered_locations = []
    for location in locations:
        publications = sorted(grouped[location["id"]], key=publication_sort_key)
        if publications:
            rendered_locations.append({
                "id": location["id"],
                "label": location["label"],
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "precision": location.get("precision", "municipality_center"),
                "publications": publications,
            })

    known_years = [
        publication["yearFounded"]
        for publication in source_publications
        if isinstance(publication.get("yearFounded"), int)
    ]
    if not known_years:
        raise ValueError("No publication has a known founding year")
    first_decade = min(known_years) // 10 * 10
    last_decade = max(max(known_years), as_of_year) // 10 * 10

    return {
        "metadata": {
            "asOfYear": as_of_year,
            "coordinateSystem": metadata.get("coordinateSystem", "WGS84"),
            "coordinateSource": metadata.get("coordinateSource"),
            "firstDecade": first_decade,
            "lastDecade": last_decade,
            "publicationCount": len(source_publications),
            "mappedPublicationCount": len(source_publications) - len(unmapped),
            "unmappedPublicationCount": len(unmapped),
        },
        "locations": sorted(rendered_locations, key=lambda location: location["label"].casefold()),
        "unmapped": sorted(unmapped, key=publication_sort_key),
    }


def serialize(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when generated data is out of date")
    args = parser.parse_args()

    payload = build_payload(load_json(PUBLICATIONS_PATH), load_json(CENTERS_PATH))
    rendered = serialize(payload)
    stale = [path for path in OUTPUT_PATHS if not path.exists() or path.read_text(encoding="utf-8") != rendered]
    if args.check:
        if stale:
            print("Map data is stale: " + ", ".join(str(path.relative_to(ROOT)) for path in stale), file=sys.stderr)
            return 1
        print("PASS: generated map data is current")
        return 0

    for path in OUTPUT_PATHS:
        path.write_text(rendered, encoding="utf-8")
    print("Wrote " + ", ".join(str(path.relative_to(ROOT)) for path in OUTPUT_PATHS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
