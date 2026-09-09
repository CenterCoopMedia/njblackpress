// History hall — deterministic layout. No renderer, no Three.js, no DOM.
//
// The hall is a corridor. Time runs along z from the entrance to the far end,
// one labelled section per decade and one more for publications whose founding
// date is unrecorded. Publications hang as framed sheets on the two walls at a
// single reading height. Guided stories rest as bound volumes on reading tables
// in shallow side bays, outside the corridor the visitor walks along.
//
// Spacing is ordered, not measured: a section is as long as the sheets and
// tables it holds. The flat timeline remains the view for precise date
// comparison, which is why nothing here maps a year to a distance.
//
// The woven model calls a publication a thread. That word stops at this
// boundary: everything below says publication.

import { YEAR_MIN, YEAR_MAX } from '../woven/layout.js';

// Every size, clearance, and pose constant in one place, so the scene modules
// and the tests read the same numbers. Units are metres at visitor scale.
export const HALL_CONFIG = {
  chronology: { firstYear: YEAR_MIN, lastYear: YEAR_MAX },

  eyeHeight: 1.6,
  ceilingHeight: 4.2,

  // Prototype frame size from the specification. Depth is the frame's stand-off
  // from the wall face, not a passe-partout measurement.
  frame: { width: 1.4, height: 1.9, depth: 0.12, centreHeight: 1.55 },
  // Clear wall between two frames on the same wall.
  frameGap: 0.6,

  // Inner face of each wall, and the walkable corridor between the side bays.
  wallX: 3,
  wallThickness: 0.4,
  corridorHalfWidth: 1.6,

  // Decade marker plate, mounted above the frames on both walls.
  marker: { length: 0.9, height: 0.8, bottom: 2.7, depth: 0.06, offset: 0.3 },

  // Closed volume proportions from the specification: width across the spine,
  // height down the page, thickness through the block.
  book: { width: 0.9, height: 1.2, thickness: 0.12 },
  bookGap: 0.25,
  booksPerBay: 2,

  table: { width: 1.2, height: 0.78, endPad: 0.45, wallGap: 0.15 },
  bayGap: 1,

  section: { entryPad: 1.6, exitPad: 1.6, minLength: 6, entryAnchorOffset: 1 },

  // Standing distance from the wall face for a framed sheet, and from the
  // corridor edge for a reading table. Both keep the visitor in the corridor.
  readDistance: 2.2,
  tableStandX: 1.2,

  // Positive overlap smaller than this is contact, not collision.
  epsilon: 1e-6
};

const CLEARED_RIGHTS = new Set(['publishable', 'publishable_with_credit', 'crop_first']);
const UNDATED_SECTION_ID = 'undated';
const UNDATED_SECTION_LABEL = 'Date unrecorded';

// ---------------------------------------------------------------------------
// Shared display helpers
// ---------------------------------------------------------------------------

/**
 * Which date case a record falls into. Kept separate from the wording so the
 * scene, the DOM, and the tests can branch on the case without matching text.
 */
export function dateCase(publication) {
  const founded = publication.yearFounded ?? null;
  const ceased = publication.yearCeased ?? null;
  const active = publication.isActive ?? publication.endState === 'still';
  if (founded == null) {
    if (active) return 'undated-active';
    if (ceased != null) return 'undated-ceased';
    return 'undated';
  }
  if (active) return 'active';
  if (ceased == null) return 'end-unrecorded';
  if (ceased === founded) return 'single-year';
  return 'range';
}

/**
 * The one date sentence for scene labels and DOM text. It never invents
 * precision and never drops a recorded year: a title with no founding date but
 * a recorded ending still shows that ending.
 */
export function formatDates(publication) {
  const founded = publication.yearFounded ?? null;
  const ceased = publication.yearCeased ?? null;
  switch (dateCase(publication)) {
    case 'range': return `${founded}–${ceased}`;
    case 'single-year': return `${founded}`;
    case 'active': return `${founded}–present`;
    case 'end-unrecorded': return `${founded}, end unrecorded`;
    case 'undated-active': return 'Date unrecorded, still publishing';
    case 'undated-ceased': return `Date unrecorded, ceased ${ceased}`;
    default: return 'Date unrecorded';
  }
}

/** The archive counts every attached source record, cleared for display or not. */
export function recordCount(publication) {
  return Array.isArray(publication.evidence) ? publication.evidence.length : 0;
}

/** Records whose rights allow the image itself to be shown. */
export function clearedRecordCount(publication) {
  if (!Array.isArray(publication.evidence)) return 0;
  return publication.evidence.filter((item) => CLEARED_RIGHTS.has(item && item.rightsStatus)).length;
}

/**
 * "1 record", "3 records". A count is a count of what the archive holds; it is
 * never a score of a publication's importance.
 */
export function recordsLabel(publication) {
  const n = recordCount(publication);
  if (n === 0) return 'No records';
  return n === 1 ? '1 record' : `${n} records`;
}

/** The first decade named in a story's era wording, for example 1860 from "1860s-1900s". */
export function storyFirstDecade(story) {
  const match = /(\d{4})s/.exec(String((story && story.era) || ''));
  return match ? Math.floor(Number(match[1]) / 10) * 10 : null;
}

/** A story can begin earlier than the hall does. Say so rather than moving its date. */
export function beginsBefore1880(story) {
  const decade = storyFirstDecade(story);
  return decade != null && decade < HALL_CONFIG.chronology.firstYear;
}

export function storyEraNote(story) {
  return beginsBefore1880(story) ? `Begins before ${HALL_CONFIG.chronology.firstYear}` : '';
}

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

const round = (n) => Math.round(n * 1e6) / 1e6;

function box(minX, maxX, minY, maxY, minZ, maxZ) {
  return {
    minX: round(minX), maxX: round(maxX),
    minY: round(minY), maxY: round(maxY),
    minZ: round(minZ), maxZ: round(maxZ)
  };
}

/** Two boxes collide when they share volume, not when they merely touch. */
export function boxesOverlap(a, b, epsilon = HALL_CONFIG.epsilon) {
  return (
    Math.min(a.maxX, b.maxX) - Math.max(a.minX, b.minX) > epsilon &&
    Math.min(a.maxY, b.maxY) - Math.max(a.minY, b.minY) > epsilon &&
    Math.min(a.maxZ, b.maxZ) - Math.max(a.minZ, b.minZ) > epsilon
  );
}

/** Is a point inside a box? Used to keep camera anchors out of the furniture. */
export function pointInBox(point, b, epsilon = HALL_CONFIG.epsilon) {
  return (
    point.x > b.minX + epsilon && point.x < b.maxX - epsilon &&
    point.y > b.minY + epsilon && point.y < b.maxY - epsilon &&
    point.z > b.minZ + epsilon && point.z < b.maxZ - epsilon
  );
}

// Heading in radians toward a target with +z as forward. The scene turns this
// into whatever rotation its camera wants; the layout stays renderer free.
function pose(position, lookAt) {
  return {
    position: { x: round(position.x), y: round(position.y), z: round(position.z) },
    lookAt: { x: round(lookAt.x), y: round(lookAt.y), z: round(lookAt.z) },
    yaw: round(Math.atan2(lookAt.x - position.x, lookAt.z - position.z))
  };
}

function decadeIdFor(year) {
  return `${Math.floor(year / 10) * 10}s`;
}

function decadeIds(config) {
  const first = Math.floor(config.chronology.firstYear / 10) * 10;
  const last = Math.floor(config.chronology.lastYear / 10) * 10;
  const ids = [];
  for (let decade = first; decade <= last; decade += 10) ids.push(`${decade}s`);
  return ids;
}

/**
 * Build the hall from the complete, unfiltered model. Filtering never changes a
 * slot, so the layout is computed once and reused.
 *
 * @param {{threads?: Array, publications?: Array, tours?: Array, byId?: Map}} model
 * @returns {object} sections, publication slots, book slots, bays, corridor,
 *   collision bounds, and the warnings a data decision still owes an answer to.
 */
export function buildHallLayout(model, options = {}) {
  const config = { ...HALL_CONFIG, ...(options.config || {}) };
  const publications = (model && (model.publications || model.threads)) || [];
  const stories = (model && (model.stories || model.tours)) || [];
  const warnings = [];

  const sectionIds = [...decadeIds(config), UNDATED_SECTION_ID];
  const bySection = new Map(sectionIds.map((id) => [id, []]));

  // Sorted by founding year, then by publication id. Two titles founded in the
  // same year keep their own slots; the shared date is shown on both.
  const dated = publications
    .filter((p) => p.yearFounded != null)
    .sort((a, b) => a.yearFounded - b.yearFounded || compareIds(a.id, b.id));
  const undated = publications
    .filter((p) => p.yearFounded == null)
    .sort((a, b) => compareIds(a.id, b.id));

  for (const publication of dated) {
    let id = decadeIdFor(publication.yearFounded);
    if (!bySection.has(id)) {
      // A date outside the hall's configured range is a data question, not a
      // reason to hide the record. Place it at the nearest end and report it.
      const clamped = publication.yearFounded < config.chronology.firstYear
        ? sectionIds[0] : sectionIds[sectionIds.length - 2];
      warnings.push({
        kind: 'year-out-of-range',
        publicationId: publication.id,
        year: publication.yearFounded,
        placedIn: clamped
      });
      id = clamped;
    }
    bySection.get(id).push(publication);
  }
  for (const publication of undated) bySection.get(UNDATED_SECTION_ID).push(publication);

  // Each story becomes one volume. Its section comes from its approved era
  // wording, clamped forward to the first section when the story starts before
  // the hall does; the cover keeps the real era.
  const storiesBySection = new Map(sectionIds.map((id) => [id, []]));
  for (const story of [...stories].sort((a, b) => compareIds(a.id, b.id))) {
    const decade = storyFirstDecade(story);
    let id = decade == null ? null : `${Math.max(decade, Math.floor(config.chronology.firstYear / 10) * 10)}s`;
    if (id == null || !storiesBySection.has(id)) {
      warnings.push({ kind: 'story-era-unreadable', storyId: story.id, era: story && story.era, placedIn: sectionIds[0] });
      id = sectionIds[0];
    }
    storiesBySection.get(id).push(story);
  }

  const sections = [];
  const slots = [];
  const bays = [];
  const bookSlots = [];
  const collisions = [];

  let cursor = 0;
  let bayTurn = 0;

  for (const sectionId of sectionIds) {
    const members = bySection.get(sectionId);
    const sectionStories = storiesBySection.get(sectionId);
    const startZ = round(cursor);
    let z = startZ + config.section.entryPad;

    const markerBoxes = ['left', 'right'].map((wall) => markerBox(config, wall, startZ));
    markerBoxes.forEach((b, i) => collisions.push({ kind: 'marker', id: `${sectionId}-marker-${i === 0 ? 'left' : 'right'}`, sectionId, box: b }));

    // Reading bays sit at the head of the section, so a visitor arriving at a
    // decade sees a route into a guided story before the wall of sheets.
    const sectionBays = [];
    for (let i = 0; i < sectionStories.length; i += config.booksPerBay) {
      const group = sectionStories.slice(i, i + config.booksPerBay);
      const wall = bayTurn++ % 2 === 0 ? 'left' : 'right';
      const bay = makeBay(config, sectionId, wall, z, group, bays.length);
      bays.push(bay);
      sectionBays.push(bay.id);
      collisions.push({ kind: 'table', id: bay.id, sectionId, box: bay.bounds });
      for (const slot of bay.books) {
        bookSlots.push(slot);
        collisions.push({ kind: 'book', id: `book-${slot.storyId}`, sectionId, box: slot.bounds });
      }
      z = round(bay.bounds.maxZ + config.bayGap);
    }

    // One primary reading row. Walls alternate, so neighbouring sheets on one
    // wall stand a full frame width plus clearance apart.
    const step = (config.frame.width + config.frameGap) / 2;
    // Alternation restarts in every section, so each decade opens on the left
    // wall and a visitor reads the same left-then-right rhythm at each threshold.
    let wallTurn = 0;
    const sectionSlots = [];
    members.forEach((publication, index) => {
      const wall = wallTurn++ % 2 === 0 ? 'left' : 'right';
      const centreZ = round(z + config.frame.width / 2 + index * step);
      const slot = makeSlot(config, publication, sectionId, wall, centreZ, slots.length);
      slots.push(slot);
      sectionSlots.push(slot.publicationId);
      collisions.push({ kind: 'frame', id: `frame-${slot.publicationId}`, sectionId, box: slot.bounds });
    });
    if (members.length) z = round(z + config.frame.width + (members.length - 1) * step);

    let endZ = round(z + config.section.exitPad);
    // An empty decade is still a place. It keeps its marker, its anchor, and
    // enough length to read as a section without a long empty walk.
    if (endZ - startZ < config.section.minLength) endZ = round(startZ + config.section.minLength);

    sections.push({
      id: sectionId,
      label: sectionId === UNDATED_SECTION_ID ? UNDATED_SECTION_LABEL : sectionId,
      decade: sectionId === UNDATED_SECTION_ID ? null : Number(sectionId.slice(0, 4)),
      startZ,
      endZ,
      length: round(endZ - startZ),
      count: members.length,
      empty: members.length === 0,
      publicationIds: sectionSlots,
      bayIds: sectionBays,
      storyIds: sectionStories.map((s) => s.id),
      markerBounds: markerBoxes,
      entryAnchor: {
        kind: 'section',
        id: sectionId,
        ...pose(
          { x: 0, y: config.eyeHeight, z: startZ + config.section.entryAnchorOffset },
          { x: 0, y: config.eyeHeight, z: startZ + config.section.entryAnchorOffset + 4 }
        )
      }
    });
    cursor = endZ;
  }

  const hallLength = round(cursor);
  const corridor = box(
    -config.corridorHalfWidth, config.corridorHalfWidth,
    0, config.ceilingHeight,
    0, hallLength
  );
  const walls = [
    { kind: 'wall', id: 'wall-left', sectionId: null, box: box(-config.wallX - config.wallThickness, -config.wallX, 0, config.ceilingHeight, 0, hallLength) },
    { kind: 'wall', id: 'wall-right', sectionId: null, box: box(config.wallX, config.wallX + config.wallThickness, 0, config.ceilingHeight, 0, hallLength) }
  ];
  collisions.push(...walls);

  const slotByPublicationId = new Map(slots.map((slot) => [slot.publicationId, slot]));
  const bookSlotByStoryId = new Map(bookSlots.map((slot) => [slot.storyId, slot]));
  const sectionById = new Map(sections.map((section) => [section.id, section]));

  return {
    config,
    sections,
    sectionById,
    slots,
    slotByPublicationId,
    bays,
    bayById: new Map(bays.map((bay) => [bay.id, bay])),
    bookSlots,
    bookSlotByStoryId,
    corridor,
    collisions,
    bounds: box(-config.wallX - config.wallThickness, config.wallX + config.wallThickness, 0, config.ceilingHeight, 0, hallLength),
    length: hallLength,
    entrance: sections.length ? sections[0].entryAnchor : null,
    publicationOrder: slots.map((slot) => slot.publicationId),
    warnings
  };
}

function compareIds(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b));
}

function markerBox(config, wall, startZ) {
  const sign = wall === 'left' ? -1 : 1;
  const inner = sign * config.wallX;
  const outer = inner - sign * config.marker.depth;
  const z0 = startZ + config.marker.offset;
  return box(
    Math.min(inner, outer), Math.max(inner, outer),
    config.marker.bottom, config.marker.bottom + config.marker.height,
    z0, z0 + config.marker.length
  );
}

function makeSlot(config, publication, sectionId, wall, centreZ, index) {
  const sign = wall === 'left' ? -1 : 1;
  const wallFace = sign * config.wallX;
  const front = wallFace - sign * config.frame.depth;
  const y = config.frame.centreHeight;
  const half = config.frame.width / 2;
  const bounds = box(
    Math.min(wallFace, front), Math.max(wallFace, front),
    y - config.frame.height / 2, y + config.frame.height / 2,
    centreZ - half, centreZ + half
  );
  const standX = wallFace - sign * config.readDistance;
  return {
    publicationId: publication.id,
    index,
    sectionId,
    wall,
    z: centreZ,
    y,
    x: round(front),
    yearFounded: publication.yearFounded ?? null,
    dateText: formatDates(publication),
    // The sheet's own rectangle on its wall plane: width across z, height in y.
    rect: {
      width: config.frame.width,
      height: config.frame.height,
      centre: { x: round(front), y: round(y), z: centreZ },
      normal: { x: -sign, y: 0, z: 0 }
    },
    bounds,
    camera: pose(
      { x: standX, y: config.eyeHeight, z: centreZ },
      { x: wallFace, y, z: centreZ }
    )
  };
}

function makeBay(config, sectionId, wall, startZ, stories, bayIndex) {
  const sign = wall === 'left' ? -1 : 1;
  const nearWall = sign * (config.wallX - config.table.wallGap);
  const inner = nearWall - sign * config.table.width;
  const pitch = config.book.height + config.bookGap;
  const length = round(stories.length * pitch - config.bookGap + config.table.endPad * 2);
  const bounds = box(
    Math.min(nearWall, inner), Math.max(nearWall, inner),
    0, config.table.height,
    startZ, startZ + length
  );
  const centreX = round((nearWall + inner) / 2);
  const id = `bay-${sectionId}-${bayIndex}`;
  const standX = sign * config.tableStandX;

  const books = stories.map((story, i) => {
    const z = round(startZ + config.table.endPad + config.book.height / 2 + i * pitch);
    const bookBounds = box(
      centreX - config.book.width / 2, centreX + config.book.width / 2,
      config.table.height, config.table.height + config.book.thickness,
      z - config.book.height / 2, z + config.book.height / 2
    );
    return {
      storyId: story.id,
      title: story.title,
      era: story.era,
      note: storyEraNote(story),
      sectionId,
      bayId: id,
      wall,
      position: { x: centreX, y: round(config.table.height + config.book.thickness / 2), z },
      size: { width: config.book.width, height: config.book.height, thickness: config.book.thickness },
      bounds: bookBounds,
      camera: pose(
        { x: standX, y: config.eyeHeight, z },
        { x: centreX, y: config.table.height, z }
      )
    };
  });

  return {
    id,
    sectionId,
    wall,
    centre: { x: centreX, y: config.table.height, z: round(startZ + length / 2) },
    size: { width: config.table.width, length, height: config.table.height },
    bounds,
    books,
    storyIds: stories.map((s) => s.id),
    anchor: {
      kind: 'bay',
      id,
      ...pose(
        { x: standX, y: config.eyeHeight, z: round(startZ + length / 2) },
        { x: centreX, y: config.table.height, z: round(startZ + length / 2) }
      )
    }
  };
}
