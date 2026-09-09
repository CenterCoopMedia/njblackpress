// History hall — the one authoritative state. No DOM, no Three.js.
//
// Every control, search result, deep link, and history event dispatches a
// command here. Animation is a transition between states; it never owns the
// selected publication or the current story stop. Inspecting a clipping is one
// of the four modes, so it is entered and left the same way as the others and
// carries the return context back to the stop it was opened from.

export const VIEWS = ['hall', 'timeline', 'text'];
export const MODES = ['browse', 'publication', 'story', 'clipping'];

export const DEFAULT_FILTERS = { city: '', evidence: 'all', era: 'all' };

function freezeAnchor(anchor) {
  if (!anchor) return null;
  return { kind: anchor.kind || 'section', id: anchor.id ?? null, z: anchor.z ?? null };
}

function sameFilters(a, b) {
  return a.city === b.city && a.evidence === b.evidence && a.era === b.era;
}

/**
 * @param {object} options
 * @param {(storyId: string) => string[]} [options.stopsForStory] ordered stop ids
 * @param {object} [options.initial] starting field values, usually from the URL
 */
/**
 * What a state change means for the clipping inspector. The hall reads this
 * rather than deciding for itself, so inspection is entered and left through
 * the state like every other mode.
 *
 * @returns {'open'|'close'|null}
 */
export function clippingTransition(next, before) {
  if (next.mode === 'clipping' && before.mode !== 'clipping') return 'open';
  if (before.mode === 'clipping' && next.mode !== 'clipping') return 'close';
  return null;
}

export function createHallState(options = {}) {
  const stopsForStory = options.stopsForStory || (() => []);
  const listeners = new Set();

  let state = {
    view: 'hall',
    mode: 'browse',
    filters: { ...DEFAULT_FILTERS },
    anchor: null,
    selectedPublicationId: null,
    storyId: null,
    stopId: null,
    overlay: null,
    returnStack: [],
    motion: 'full',
    tier: 'standard',
    generation: 0,
    ...(options.initial || {})
  };

  function snapshot() {
    return {
      mode: state.mode,
      view: state.view,
      anchor: state.anchor,
      selectedPublicationId: state.selectedPublicationId,
      storyId: state.storyId,
      stopId: state.stopId,
      overlay: state.overlay,
      filters: { ...state.filters }
    };
  }

  // A return context is saved before entering focus, reading, or inspection, and
  // restored on close. It carries the DOM details the page needs to put the
  // visitor back where they were, which is why the caller may add its own.
  function pushReturn(context) {
    state.returnStack = [...state.returnStack, { ...snapshot(), ...(context || {}) }];
  }

  function commit(next, { bumpGeneration = false } = {}) {
    const before = state;
    state = { ...state, ...next };
    if (bumpGeneration) state.generation = before.generation + 1;
    for (const listener of [...listeners]) listener(state, before);
    return state;
  }

  // Story, stop, and view changes can strand asynchronous work — a page image, a
  // painted label — so each one takes a new generation token. Work started under
  // an older token is rejected rather than applied to the view the visitor is
  // looking at now.
  function changesGeneration(next) {
    return (
      ('storyId' in next && next.storyId !== state.storyId) ||
      ('stopId' in next && next.stopId !== state.stopId) ||
      ('view' in next && next.view !== state.view)
    );
  }

  function apply(next) {
    return commit(next, { bumpGeneration: changesGeneration(next) });
  }

  const api = {
    getState: () => state,
    generation: () => state.generation,
    /** True while the token still matches the current story, stop, and view. */
    isCurrent: (token) => token === state.generation,

    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },

    selectPublication(id, context) {
      if (id == null) return state;
      // Selecting the sheet that is already open is not a new state and must not
      // stack a second return context.
      if (state.mode === 'publication' && state.selectedPublicationId === id) return state;
      // Moving from one sheet to the next replaces the focus rather than
      // stacking a second way back.
      if (state.mode !== 'publication') pushReturn(context);
      // A sheet focus is not a reading state: the story and stop are cleared so
      // no stale story reaches the reader or a copied link. The return stack
      // still holds them, so closing puts the visitor back in the story.
      return apply({
        mode: 'publication',
        selectedPublicationId: id,
        storyId: null,
        stopId: null,
        overlay: null,
        anchor: { kind: 'publication', id, z: null }
      });
    },

    openStory(id, stopId, context) {
      if (!id) return state;
      const stops = stopsForStory(id) || [];
      const wanted = stopId != null && stops.includes(stopId) ? stopId : (stops[0] ?? null);
      const unknownStop = stopId != null && !stops.includes(stopId);
      if (state.mode === 'story' && state.storyId === id) {
        // Reopening the same story is a stop move, not a new reading state.
        return wanted === state.stopId ? state : apply({ stopId: wanted, unknownStop });
      }
      if (state.mode !== 'story') pushReturn(context);
      return apply({
        mode: 'story',
        storyId: id,
        stopId: wanted,
        unknownStop,
        overlay: null,
        anchor: { kind: 'story', id, z: null }
      });
    },

    gotoStop(stopId) {
      if (!state.storyId || stopId == null) return state;
      const stops = stopsForStory(state.storyId) || [];
      if (!stops.includes(stopId) || stopId === state.stopId) return state;
      return apply({ stopId, unknownStop: false });
    },

    nextStop() { return step(1); },
    prevStop() { return step(-1); },

    openClipping(payload) {
      if (!payload) return state;
      pushReturn(payload.returnContext);
      return apply({ mode: 'clipping', overlay: { kind: 'clipping', ...payload } });
    },

    /** Pop the topmost state and restore the context saved when it opened. */
    close() {
      if (!state.returnStack.length) {
        if (state.mode === 'browse') return state;
        return apply({ mode: 'browse', overlay: null, storyId: null, stopId: null });
      }
      const stack = state.returnStack.slice();
      const restored = stack.pop();
      return commit(
        {
          mode: restored.mode,
          view: restored.view,
          anchor: restored.anchor,
          selectedPublicationId: restored.selectedPublicationId,
          storyId: restored.storyId,
          stopId: restored.stopId,
          overlay: restored.overlay,
          filters: { ...restored.filters },
          returnStack: stack
        },
        {
          bumpGeneration:
            restored.storyId !== state.storyId ||
            restored.stopId !== state.stopId ||
            restored.view !== state.view
        }
      );
    },

    moveTo(anchor) {
      const next = freezeAnchor(anchor);
      if (state.mode === 'story' || state.mode === 'clipping') return state; // Rail movement is suspended.
      return apply({ anchor: next });
    },

    setFilters(filters) {
      const merged = { ...state.filters, ...(filters || {}) };
      if (sameFilters(merged, state.filters)) return state;
      return apply({ filters: merged });
    },

    setView(view) {
      if (!VIEWS.includes(view) || view === state.view) return state;
      return apply({ view });
    },

    setTier(tier) {
      if (tier === state.tier) return state;
      return apply({ tier });
    },

    setMotion(motion) {
      if (motion === state.motion) return state;
      return apply({ motion });
    }
  };

  function step(direction) {
    if (!state.storyId) return state;
    const stops = stopsForStory(state.storyId) || [];
    const index = stops.indexOf(state.stopId);
    if (index < 0) return state;
    const target = index + direction;
    // The first and last stops do not wrap; the reader disables its controls there.
    if (target < 0 || target >= stops.length) return state;
    return apply({ stopId: stops[target], unknownStop: false });
  }

  return api;
}
