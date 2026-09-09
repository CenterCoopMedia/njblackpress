// Publication record helpers shared by the index, the flat timeline, and the
// history hall: era colour, the date sentence, and the filter rule.
//
// These three moved out of exhibit-geometry.js so the hall can use them without
// importing drawing geometry, and so the old 3D timeline module can retire
// without taking the index and the filters with it.

// Colour identifies the founding era. It never rates a publication's importance,
// so era is always carried by a label as well.
export const ERA_COLORS = ['#cb7857', '#d59c59', '#cfb37c', '#b1a0b8', '#83a69b', '#91b7c2', '#ead5af'];
export const ERA_COLOR_UNDATED = '#a89c85';

export function eraColor(publication) {
  const index = 'ABCDEFG'.indexOf(publication.bandKey);
  return index < 0 ? ERA_COLOR_UNDATED : ERA_COLORS[index];
}

// Compatibility alias. The woven modules still say thread for a publication;
// new code calls eraColor.
export const threadColor = eraColor;

export function publicationYears(publication) {
  if (publication.yearFounded == null) {
    const end = publication.endState === 'still' ? 'still publishing'
      : publication.yearCeased != null ? `ceased ${publication.yearCeased}` : 'end date unrecorded';
    return `Founding year unrecorded · ${end}`;
  }
  if (publication.endState === 'still') return `${publication.yearFounded}–present`;
  if (publication.yearCeased != null) return `${publication.yearFounded}–${publication.yearCeased}`;
  return `${publication.yearFounded} · end date unrecorded`;
}

export function matchesFilters(publication, { city = '', evidence = 'all' } = {}) {
  if (city && String(publication.city || '') !== city) return false;
  if (evidence === 'active') return publication.endState === 'still';
  if (evidence === 'evidence') return !publication.ghost;
  if (evidence === 'unillustrated') return publication.ghost;
  return true;
}
