# Historical notes: time map

Design direction: Fable 5.1 (`claude-fable-5-1`) through Claude Code print mode,
September 8, 2026. Implementation and verification: Codex with bounded workers.
This replaces the publication-bar gallery shipped in PR #73.

## Purpose

The ground shows New Jersey geography. Height shows year. Publication posts
show recorded spans at the saved town location. This allows place and time to
be compared together. The flat timeline remains available for date comparison.
A year plane highlights records with known spans at a chosen year. Guided
stories move through the places and dates associated with their source events.

## Composition and interaction

- A state silhouette anchors the scene. A labelled year pole establishes the
  vertical scale. Town names, locator lines, and a north arrow give orientation.
- The entry card offers three existing stories and a direct explore action.
- Publications are small rectangular posts, coloured by founding era. Active
  records have a distinct cap. Faded ends mark missing dates; unknown dates do
  not become inferred publication lifetimes.
- Orbit, zoom, selection, search, and a native year range control support
  exploration. Keyboard selection reaches every publication, including records
  outside the state and records with no known town.
- A story shows the event's exact recorded date and text next to the scene.
  The orange path is the reading order, not proof of travel or causation.
- A publication panel can open during a story and return to the same stop.
  URL state records the view, publication, story, stop, and selected year.
- Reduced motion removes camera travel and idle motion. The scene rests when
  unchanged and suspends when hidden. The flat chart and complete text list
  remain available without WebGL.

## Data and source rules

Coordinates use the existing `docs/data/map-publications.json`. Crowded town
clusters move apart for legibility, with leader lines back to saved positions.
These locations do not identify a publisher address. Composite location values
remain composite. Outside-state and statewide records occupy labelled shelves.

The ground comes from the Census 2023, 1:20 million cartographic boundary KML.
`scripts/build_nj_outline.py` generates `docs/data/nj-outline.json` from that
public source. The outline has no historical or address-level claim.

Event images require an exact match to a recorded source file and a permitted
public image status. A shared publication or year does not establish that an
image illustrates an event. Missing images leave the event and citation intact.
Before-1880 events retain their actual dates in the panel. Placeless events
remain story stops without an invented position. Retrospective source events
can appear above a publication's ending year.

## Implementation decisions after the design proposal

The proposal's spatial concept, story entry, year plane, and reading dock are
retained. The browser uses the existing published coordinate dataset rather
than a second copy of municipality centres. The flat chart uses labelled native
rows, so it works without a second WebGL renderer. Old query values and the old
page route remain compatible. Textile modules and controls are removed.

The design proposal is not a factual source. Statements about archive counts,
imports, location density, or source coverage require checks against this
repository. Review the rendered experience as well as the executable checks.
