"""Build the time map ground from the Census 2023 cartographic boundary KML.

Run with a downloaded archive path, or omit it to fetch the public source.
The cartographic boundary is for orientation, not address or property lookup.
"""
import io
import json
import math
from pathlib import Path
import sys
import urllib.request
import zipfile
from xml.etree import ElementTree as ET

SOURCE = 'https://www2.census.gov/geo/tiger/GENZ2023/kml/cb_2023_us_state_20m.zip'
ROOT = Path(__file__).resolve().parents[1]


def main():
    raw = Path(sys.argv[1]).read_bytes() if len(sys.argv) > 1 else urllib.request.urlopen(SOURCE, timeout=30).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        document = ET.fromstring(archive.read('cb_2023_us_state_20m.kml'))
    ns = {'k': 'http://www.opengis.net/kml/2.2'}
    state = next(p for p in document.findall('.//k:Placemark', ns)
                 if 'New Jersey' in p.findtext('k:name', default='', namespaces=ns))
    rings = []
    for ring in state.findall('.//k:outerBoundaryIs/k:LinearRing/k:coordinates', ns):
        points = []
        for coordinate in ring.text.split():
            lon, lat = map(float, coordinate.split(',')[:2])
            points.append([round((lon + 74.55) * math.cos(math.radians(40.15)) * 24, 5),
                           round(-(lat - 40.15) * 24, 5)])
        rings.append(points)
    # At this mapping scale the largest exterior ring is the state silhouette.
    points = max(rings, key=len)
    output = {'source': SOURCE, 'name': 'New Jersey', 'year': 2023,
              'description': 'Census 1:20 million cartographic boundary; ground orientation only.',
              'projection': 'x=(lon+74.55)*cos(40.15deg)*24; z=-(lat-40.15)*24',
              'coordinates': points}
    (ROOT / 'docs/data/nj-outline.json').write_text(json.dumps(output, indent=2) + '\n')
    print(f'Built NJ outline: {len(points)} vertices')


if __name__ == '__main__':
    main()
