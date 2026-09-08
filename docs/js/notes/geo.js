// Historical notes geography and time coordinates.

export const YEAR_MIN = 1880;
export const YEAR_MAX = 2026;
export const YEAR_SCALE = 0.12;
export const Y_NOW = (YEAR_MAX - YEAR_MIN) * YEAR_SCALE;

const ORIGIN_LATITUDE = 40.15;
const ORIGIN_LONGITUDE = -74.55;
const MAP_SCALE = 24;
const EARTH_LATITUDE_COSINE = Math.cos((ORIGIN_LATITUDE * Math.PI) / 180);
const GOLDEN_ANGLE = (137.508 * Math.PI) / 180;
const CLUSTER_RADIUS_BASE = 0.3;
const MEMBER_RADIUS_SCALE = 0.34;
const DISPLACEMENT_NOTICE_DISTANCE = 0.5;

export const ERA_COLORS = Object.freeze([
  '#cb7857',
  '#d59c59',
  '#cfb37c',
  '#b1a0b8',
  '#83a69b',
  '#91b7c2',
  '#ead5af'
]);

export const UNKNOWN_ERA_COLOR = '#a89c85';

const ERA_RANGES = Object.freeze([
  [1880, 1899],
  [1900, 1929],
  [1930, 1949],
  [1950, 1969],
  [1970, 1989],
  [1990, 2009],
  [2010, 2026]
]);

// These records are outside the state footprint or have no single town. They
// remain in the keyboard and text order on shelves beside the map.
const SHELF_LAYOUT = Object.freeze([
  {
    id: 'chicago-il',
    cityValues: Object.freeze(['Chicago/National']),
    label: 'Chicago / National',
    placedXZ: Object.freeze({ x: 19, z: 8 }),
    group: 'beyond-town'
  },
  {
    id: 'fort-wayne-in',
    cityValues: Object.freeze(['Fort Wayne']),
    label: 'Fort Wayne',
    placedXZ: Object.freeze({ x: 22, z: 8 }),
    group: 'beyond-town'
  },
  {
    id: 'new-jersey-statewide',
    cityValues: Object.freeze(['Statewide (New Jersey)']),
    label: 'Statewide (New Jersey)',
    placedXZ: Object.freeze({ x: 25, z: 8 }),
    group: 'beyond-town'
  },
  {
    id: 'place-not-recorded',
    cityValues: Object.freeze(['Unknown', null]),
    label: 'Place not recorded',
    placedXZ: Object.freeze({ x: 22, z: 13 }),
    group: 'place-not-recorded'
  }
]);

/** Return a copy so callers cannot change the fixed shelf layout. */
export function shelfClusters() {
  return SHELF_LAYOUT.map((shelf) => ({
    id: shelf.id,
    cityValues: [...shelf.cityValues],
    label: shelf.label,
    placedXZ: { ...shelf.placedXZ },
    group: shelf.group,
    shelf: true
  }));
}

/** Project a saved WGS84 point into the scene's ground plane. */
export function project(latitude, longitude) {
  if (latitude === null || latitude === undefined || longitude === null || longitude === undefined) return null;
  const lat = Number(latitude);
  const lon = Number(longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  return {
    x: (lon - ORIGIN_LONGITUDE) * EARTH_LATITUDE_COSINE * MAP_SCALE,
    z: -(lat - ORIGIN_LATITUDE) * MAP_SCALE
  };
}

/** Convert a recorded year, including a fractional event year, to height. */
export function yearToY(year) {
  if (year === null || year === undefined || String(year).trim() === '') return null;
  const value = Number(year);
  return Number.isFinite(value) ? (value - YEAR_MIN) * YEAR_SCALE : null;
}

/** Color a title by its recorded founding era. */
export function eraColorFor(year) {
  if (year === null || year === undefined || String(year).trim() === '') return UNKNOWN_ERA_COLOR;
  const value = Number(year);
  if (!Number.isFinite(value)) return UNKNOWN_ERA_COLOR;
  const index = ERA_RANGES.findIndex(([from, to]) => value >= from && value <= to);
  return index < 0 ? UNKNOWN_ERA_COLOR : ERA_COLORS[index];
}

/**
 * Group publications at their saved map locations and lay out each group.
 * The input records receive their derived `x`, `z`, and `clusterId` fields.
 */
export function buildClusters(publications, mapData = {}) {
  const records = Array.isArray(publications) ? publications : [];
  const locations = Array.isArray(mapData?.locations) ? mapData.locations : [];
  const locationByPublicationId = new Map();
  const locationByCity = new Map();
  const locationIds = new Map();

  locations.forEach((location, index) => {
    const locationId = location.id ?? `location-${index + 1}`;
    locationIds.set(location, locationId);
    const locationCities = new Set([
      ...(Array.isArray(location.cityValues) ? location.cityValues : []),
      ...(Array.isArray(location.publications)
        ? location.publications.map((publication) => publication?.city)
        : [])
    ]);
    for (const city of locationCities) locationByCity.set(cityKey(city), location);
    for (const publication of location.publications || []) {
      const id = normaliseId(publication?.id);
      if (id !== null) locationByPublicationId.set(id, location);
    }
  });

  const groups = new Map();
  for (const publication of records) {
    const id = normaliseId(publication?.id);
    const location = locationByPublicationId.get(id) || locationByCity.get(cityKey(publication?.city));
    const key = location ? `location:${locationIds.get(location)}` : 'place-not-recorded';
    let group = groups.get(key);
    if (!group) {
      group = {
        key,
        location: location || null,
        members: [],
        cityValues: new Set()
      };
      groups.set(key, group);
    }
    group.members.push(publication);
    group.cityValues.add(publication?.city ?? null);
  }

  const shelves = shelfClusters();
  const shelfByCity = new Map();
  for (const shelf of shelves) {
    for (const city of shelf.cityValues) shelfByCity.set(cityKey(city), shelf);
  }

  const clusters = [];
  for (const group of groups.values()) {
    const location = group.location;
    const shelf = [...group.cityValues]
      .map((city) => shelfByCity.get(cityKey(city)))
      .find(Boolean) || (location ? shelfForLocation(location, shelfByCity) : shelves.find((item) => item.id === 'place-not-recorded'));
    const locationId = (location && locationIds.get(location)) || shelf?.id || 'place-not-recorded';
    // Shelf records keep their saved coordinates in the source map data, but
    // the scene intentionally gives them no ground point or leader line.
    const trueXZ = location && !shelf ? project(location.latitude, location.longitude) : null;
    const cityValue = firstCityValue(group.members);
    const label = location?.label || shelf?.label || cityValue || 'Place not recorded';
    const initialPlaced = shelf
      ? { ...shelf.placedXZ }
      : trueXZ
        ? { ...trueXZ }
        : { ...shelves.find((item) => item.id === 'place-not-recorded').placedXZ };

    const members = [...group.members].sort(comparePublications);
    clusters.push({
      id: shelf?.id === 'place-not-recorded' && !location ? 'place-not-recorded' : locationId,
      cityValue: cityValue ?? 'Unknown',
      label,
      precision: location?.precision || null,
      trueXZ,
      placedXZ: initialPlaced,
      radius: clusterRadius(members.length),
      members: members.map((publication) => normaliseId(publication.id)).filter((id) => id !== null),
      shelf: Boolean(shelf),
      displaced: false,
      _members: members
    });
  }

  settleClusters(clusters.filter((cluster) => !cluster.shelf));

  for (const cluster of clusters) {
    cluster.displaced = !cluster.shelf && Boolean(
      cluster.trueXZ && distance(cluster.trueXZ, cluster.placedXZ) > DISPLACEMENT_NOTICE_DISTANCE
    );
    cluster._members.forEach((publication, index) => {
      const radius = MEMBER_RADIUS_SCALE * Math.sqrt(index);
      const angle = index * GOLDEN_ANGLE;
      publication.x = cluster.placedXZ.x + radius * Math.cos(angle);
      publication.z = cluster.placedXZ.z + radius * Math.sin(angle);
      publication.clusterId = cluster.id;
    });
    delete cluster._members;
  }

  return clusters;
}

function shelfForLocation(location, shelfByCity) {
  const values = [
    ...(Array.isArray(location.cityValues) ? location.cityValues : []),
    ...(Array.isArray(location.publications) ? location.publications.map((publication) => publication?.city) : [])
  ];
  return values.map((value) => shelfByCity.get(cityKey(value))).find(Boolean) || null;
}

function settleClusters(clusters) {
  // Ten passes are the specified first settling step. A bounded continuation
  // handles dense chains while retaining the same deterministic pairwise rule.
  for (let iteration = 0; iteration < 10; iteration += 1) {
    resolveOverlaps(clusters);
  }
  for (let iteration = 0; iteration < 160 && hasOverlap(clusters); iteration += 1) {
    resolveOverlaps(clusters);
  }
}

function resolveOverlaps(clusters) {
  for (let leftIndex = 0; leftIndex < clusters.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < clusters.length; rightIndex += 1) {
      const left = clusters[leftIndex];
      const right = clusters[rightIndex];
      const dx = right.placedXZ.x - left.placedXZ.x;
      const dz = right.placedXZ.z - left.placedXZ.z;
      const actualDistance = Math.hypot(dx, dz);
      const minimumDistance = left.radius + right.radius;
      if (actualDistance >= minimumDistance) continue;

      const direction = actualDistance > 1e-9
        ? { x: dx / actualDistance, z: dz / actualDistance }
        : collisionDirection(left.id, right.id);
      const push = minimumDistance - actualDistance + 0.0001;
      left.placedXZ.x -= direction.x * push / 2;
      left.placedXZ.z -= direction.z * push / 2;
      right.placedXZ.x += direction.x * push / 2;
      right.placedXZ.z += direction.z * push / 2;
    }
  }
}

function hasOverlap(clusters) {
  for (let leftIndex = 0; leftIndex < clusters.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < clusters.length; rightIndex += 1) {
      const left = clusters[leftIndex];
      const right = clusters[rightIndex];
      if (distance(left.placedXZ, right.placedXZ) + 1e-7 < left.radius + right.radius) return true;
    }
  }
  return false;
}

function collisionDirection(leftId, rightId) {
  let hash = 2166136261;
  for (const character of `${leftId}|${rightId}`) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  const angle = ((hash >>> 0) % 360) * Math.PI / 180;
  return { x: Math.cos(angle), z: Math.sin(angle) };
}

function clusterRadius(count) {
  return CLUSTER_RADIUS_BASE + MEMBER_RADIUS_SCALE * Math.sqrt(count);
}

function distance(left, right) {
  return Math.hypot(left.x - right.x, left.z - right.z);
}

function cityKey(city) {
  return city == null ? '__missing_city__' : String(city);
}

function firstCityValue(publications) {
  const record = publications.find((publication) => publication?.city != null);
  return record?.city ?? 'Unknown';
}

function comparePublications(left, right) {
  const leftYear = knownYear(left?.yearFounded) ? Number(left.yearFounded) : Number.POSITIVE_INFINITY;
  const rightYear = knownYear(right?.yearFounded) ? Number(right.yearFounded) : Number.POSITIVE_INFINITY;
  return leftYear - rightYear
    || String(left?.name || '').localeCompare(String(right?.name || ''))
    || (normaliseId(left?.id) ?? 0) - (normaliseId(right?.id) ?? 0);
}

function normaliseId(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null;
  const id = Number(value);
  return Number.isInteger(id) ? id : null;
}

function knownYear(value) {
  if (value === null || value === undefined || String(value).trim() === '') return false;
  const year = Number(value);
  return Number.isInteger(year) && Number.isFinite(year);
}
