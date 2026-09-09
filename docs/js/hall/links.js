// History hall — one place that reads and writes the page's URL. No renderer,
// no DOM. Routing is parsed before anything imports a drawing module, so a
// forced-text visit never fetches Three.js.
//
// Old links keep working: view=3d and view=woven mean the hall, and a bare pub
// parameter means the hall too.

import { HALL_CONFIG } from './layout.js';

/** Parameters that make a visit a deep link. guide.js suppresses its first-visit
 * card when any of these is present, so the visitor lands on what they asked for. */
export const DEEP_LINK_PARAMS = ['pub', 'story', 'stop', 'decade', 'ghost', 'nogl', 'twin'];

export const VIEW_ALIASES = {
  hall: 'hall',
  '3d': 'hall',
  woven: 'hall',
  timeline: 'timeline'
};

export const UNDATED_DECADE = 'undated';

function searchParams(input) {
  if (input instanceof URLSearchParams) return input;
  const text = String(input == null ? '' : input);
  return new URLSearchParams(text.startsWith('?') ? text.slice(1) : text);
}

function flag(params, name) {
  return params.get(name) === '1';
}

/**
 * Read a query string into the hall's route shape. Nothing throws: an
 * unreadable value becomes null and an issue the caller can explain.
 *
 * @returns {{view: ?string, forcedText: boolean, pub: ?number, story: ?string,
 *   stop: ?string, decade: ?string, ghost: boolean, twin: boolean, nogl: boolean,
 *   target: object, issues: Array}}
 */
export function parse(searchString) {
  const params = searchParams(searchString);
  const issues = [];

  const rawView = params.get('view');
  let view = null;
  if (rawView != null && rawView !== '') {
    view = VIEW_ALIASES[rawView] || null;
    if (!view) issues.push({ param: 'view', value: rawView, reason: 'unknown-view', message: 'That view is not one of the hall or the flat timeline.' });
  }

  let pub = null;
  const rawPub = params.get('pub');
  if (rawPub != null && rawPub !== '') {
    const n = Number(rawPub);
    if (Number.isInteger(n) && n >= 0) pub = n;
    else issues.push({ param: 'pub', value: rawPub, reason: 'malformed-id', message: 'That publication link is not a publication number.' });
  }

  const rawStory = params.get('story');
  const story = rawStory ? rawStory : null;
  const rawStop = params.get('stop');
  const stop = rawStop ? rawStop : null;
  if (stop && !story) {
    issues.push({ param: 'stop', value: stop, reason: 'stop-without-story', message: 'A stop link only applies to the story it belongs to.' });
  }

  let decade = null;
  const rawDecade = params.get('decade');
  if (rawDecade != null && rawDecade !== '') {
    decade = normaliseDecade(rawDecade);
    if (!decade) issues.push({ param: 'decade', value: rawDecade, reason: 'malformed-decade', message: 'That decade is not a section of the hall.' });
  }

  const twin = flag(params, 'twin');
  const nogl = flag(params, 'nogl');
  const ghost = flag(params, 'ghost');
  const forcedText = twin || nogl;

  // A bare pub with no view opens the hall. Every other target keeps whichever
  // view the link named.
  if (!view && pub != null && !story && !decade) view = 'hall';

  return {
    view,
    forcedText,
    pub,
    story,
    stop: story ? stop : null,
    decade,
    ghost,
    twin,
    nogl,
    target: pickTarget({ pub, story, stop: story ? stop : null, decade }),
    issues
  };
}

/** Content targets have one order of precedence: story, then publication, then decade. */
function pickTarget({ pub, story, stop, decade }) {
  if (story) return { kind: 'story', id: story, stop: stop || null };
  if (pub != null) return { kind: 'publication', id: pub };
  if (decade) return { kind: 'decade', id: decade };
  return { kind: 'none', id: null };
}

function normaliseDecade(value) {
  const text = String(value).trim().toLowerCase();
  if (text === UNDATED_DECADE) return UNDATED_DECADE;
  const match = /^(\d{4})s$/.exec(text);
  if (!match) return null;
  const year = Number(match[1]);
  if (year % 10 !== 0) return null;
  const first = Math.floor(HALL_CONFIG.chronology.firstYear / 10) * 10;
  const last = Math.floor(HALL_CONFIG.chronology.lastYear / 10) * 10;
  if (year < first || year > last) return null;
  return `${year}s`;
}

/**
 * Check a parsed route against the loaded model. Unknown ids are reported, never
 * thrown, so the page can say what went wrong and still offer the index.
 *
 * @param {object} parsed result of parse()
 * @param {object} model loaded model with byId and tours
 * @param {object} [layout] hall layout, when section ids should be checked too
 */
export function validate(parsed, model, layout) {
  const issues = [...parsed.issues];
  let target = parsed.target;

  if (target.kind === 'publication' && model && model.byId && !model.byId.has(target.id)) {
    issues.push({ param: 'pub', value: target.id, reason: 'unknown-publication', message: 'No publication in the archive has that number.' });
    target = { kind: 'none', id: null };
  }

  if (target.kind === 'story') {
    const tours = (model && (model.tours || model.stories)) || [];
    const tour = tours.find((t) => t.id === target.id);
    if (!tour) {
      issues.push({ param: 'story', value: target.id, reason: 'unknown-story', message: 'No guided story in the archive has that name.' });
      target = { kind: 'none', id: null };
    } else if (target.stop) {
      const stops = (tour.stops || []).map((s) => s.eventId ?? s.id);
      if (!stops.includes(target.stop)) {
        // An unknown stop opens the story at its first stop and explains why.
        issues.push({ param: 'stop', value: target.stop, reason: 'unknown-stop', message: 'That stop is not part of this story, so it opens at the first stop.' });
        target = { kind: 'story', id: target.id, stop: stops[0] ?? null };
      }
    }
  }

  if (target.kind === 'decade' && layout && layout.sectionById && !layout.sectionById.has(target.id)) {
    issues.push({ param: 'decade', value: target.id, reason: 'unknown-decade', message: 'The hall has no section for that decade.' });
    target = { kind: 'none', id: null };
  }

  return { target, issues, ok: issues.length === 0 };
}

/**
 * Which view to open. Forced text wins over everything; then an explicit view;
 * then whatever the visitor last chose; then the hall.
 */
export function resolveView(parsed, { sessionView = null, canRenderHall = true } = {}) {
  if (parsed.forcedText) return 'text';
  if (parsed.view === 'timeline') return 'timeline';
  const wanted = parsed.view || (sessionView === 'timeline' || sessionView === 'hall' ? sessionView : 'hall');
  if (wanted === 'hall' && !canRenderHall) return 'timeline';
  return wanted;
}

/**
 * The canonical link for Copy link. It carries the view and the content target
 * and nothing else: camera coordinates are not part of a shared address.
 */
export function format(state = {}) {
  const params = new URLSearchParams();
  const view = state.view === 'timeline' ? 'timeline' : 'hall';
  params.set('view', view);

  if (state.storyId) {
    params.set('story', state.storyId);
    if (state.stopId) params.set('stop', state.stopId);
  } else if (state.selectedPublicationId != null) {
    params.set('pub', String(state.selectedPublicationId));
  } else if (state.anchor && state.anchor.kind === 'section' && state.anchor.id) {
    params.set('decade', String(state.anchor.id));
  } else if (state.decade) {
    params.set('decade', String(state.decade));
  }
  return `?${params.toString()}`;
}
